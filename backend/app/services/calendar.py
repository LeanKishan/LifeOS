from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from dateutil.rrule import rrulestr
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models.calendar import Event, EventOverride, Reminder
from app.models.job_tracker import Application
from app.models.projects import Project, Task
from app.schemas.calendar import (
    EventCreate,
    EventOverrideCreate,
    EventUpdate,
    ReminderCreate,
)

MAX_RANGE_DAYS = 400
MAX_OCCURRENCES = 750


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _aware(value: datetime) -> datetime:
    """Naive UTC (how we store) -> tz-aware UTC (what dateutil.rrule wants)."""
    return value.replace(tzinfo=UTC)


def _validate_rrule(rule: str, dtstart_naive: datetime) -> None:
    # dtstart is tz-aware so an `UNTIL=...Z` in the rule is accepted.
    try:
        rrulestr(rule, dtstart=_aware(dtstart_naive))
    except (ValueError, TypeError) as exc:
        raise LookupError(f"invalid recurrence rule: {exc}") from exc


def _validate_links(
    db: Session,
    user_id: int,
    *,
    project_id: int | None,
    task_id: int | None,
    application_id: int | None,
) -> None:
    checks: list[tuple[type[Project | Task | Application], int | None, str]] = [
        (Project, project_id, "project_id"),
        (Task, task_id, "task_id"),
        (Application, application_id, "application_id"),
    ]
    for model, ident, label in checks:
        if ident is None:
            continue
        exists = db.scalars(
            select(model).where(model.id == ident, model.user_id == user_id)
        ).first()
        if exists is None:
            raise LookupError(f"{label} does not belong to you")


# --------------------------------------------------------------------------- #
# Event CRUD
# --------------------------------------------------------------------------- #
def _event_query(user_id: int) -> Select[tuple[Event]]:
    return (
        select(Event)
        .where(Event.user_id == user_id)
        .options(selectinload(Event.reminders), selectinload(Event.overrides))
    )


def list_events(db: Session, user_id: int) -> Sequence[Event]:
    return db.scalars(_event_query(user_id).order_by(Event.start_at)).all()


def get_event(db: Session, user_id: int, event_id: int) -> Event | None:
    return db.scalars(_event_query(user_id).where(Event.id == event_id)).first()


def create_event(db: Session, user_id: int, data: EventCreate) -> Event:
    start = _to_naive_utc(data.start_at)
    end = _to_naive_utc(data.end_at)
    if data.recurrence:
        _validate_rrule(data.recurrence, start)
    _validate_links(
        db,
        user_id,
        project_id=data.project_id,
        task_id=data.task_id,
        application_id=data.application_id,
    )

    payload = data.model_dump(exclude={"start_at", "end_at"})
    event = Event(user_id=user_id, start_at=start, end_at=end, **payload)
    db.add(event)
    db.commit()
    return _reload_event(db, user_id, event.id)


def update_event(db: Session, user_id: int, event: Event, data: EventUpdate) -> Event:
    changes = data.model_dump(exclude_unset=True)
    if "start_at" in changes:
        changes["start_at"] = _to_naive_utc(changes["start_at"])
    if "end_at" in changes:
        changes["end_at"] = _to_naive_utc(changes["end_at"])

    for field, value in changes.items():
        setattr(event, field, value)

    if event.end_at < event.start_at:
        raise LookupError("end_at must not be before start_at")
    if event.recurrence:
        _validate_rrule(event.recurrence, event.start_at)
    _validate_links(
        db,
        user_id,
        project_id=event.project_id,
        task_id=event.task_id,
        application_id=event.application_id,
    )

    db.commit()
    return _reload_event(db, user_id, event.id)


def delete_event(db: Session, event: Event) -> None:
    db.delete(event)
    db.commit()


def _reload_event(db: Session, user_id: int, event_id: int) -> Event:
    event = get_event(db, user_id, event_id)
    if event is None:  # pragma: no cover - just committed it
        raise RuntimeError("event vanished after commit")
    return event


# --------------------------------------------------------------------------- #
# Reminders
# --------------------------------------------------------------------------- #
def get_reminder(db: Session, user_id: int, reminder_id: int) -> Reminder | None:
    return db.scalars(
        select(Reminder).where(
            Reminder.id == reminder_id, Reminder.user_id == user_id
        )
    ).first()


def add_reminder(db: Session, user_id: int, event: Event, data: ReminderCreate) -> Reminder:
    reminder = Reminder(
        user_id=user_id, event_id=event.id, minutes_before=data.minutes_before
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, reminder: Reminder) -> None:
    db.delete(reminder)
    db.commit()


# --------------------------------------------------------------------------- #
# Occurrence expansion
# --------------------------------------------------------------------------- #
@dataclass
class Occurrence:
    event_id: int
    title: str
    description: str | None
    location: str | None
    all_day: bool
    is_recurring: bool
    occurrence_start: datetime
    overridden: bool
    start_at: datetime
    end_at: datetime


def _occurrence(
    event: Event,
    origin: datetime,
    start: datetime,
    end: datetime,
    *,
    recurring: bool,
    override: EventOverride | None = None,
) -> Occurrence:
    return Occurrence(
        event_id=event.id,
        title=(override.title if override and override.title else event.title),
        description=(
            override.description
            if override and override.description is not None
            else event.description
        ),
        location=(
            override.location
            if override and override.location is not None
            else event.location
        ),
        all_day=event.all_day,
        is_recurring=recurring,
        occurrence_start=origin,
        overridden=override is not None,
        start_at=start,
        end_at=end,
    )


def expand_occurrences(
    db: Session, user_id: int, window_start: datetime, window_end: datetime
) -> list[Occurrence]:
    start = _to_naive_utc(window_start)
    end = _to_naive_utc(window_end)
    if end <= start:
        raise LookupError("`to` must be after `from`")
    if (end - start).days > MAX_RANGE_DAYS:
        raise LookupError(f"range too large (max {MAX_RANGE_DAYS} days)")

    events = db.scalars(
        select(Event).where(Event.user_id == user_id).options(selectinload(Event.overrides))
    ).all()
    out: list[Occurrence] = []

    for event in events:
        duration = event.end_at - event.start_at

        if not event.recurrence:
            if event.start_at < end and event.end_at > start:
                out.append(
                    _occurrence(
                        event, event.start_at, event.start_at, event.end_at, recurring=False
                    )
                )
            continue

        overrides = {ov.occurrence_start: ov for ov in event.overrides}
        seen: set[datetime] = set()

        rule = rrulestr(event.recurrence, dtstart=_aware(event.start_at))
        # An instance [s, s+duration] overlaps [start, end] iff s in (start - duration, end).
        lo = _aware(start - duration)
        hi = _aware(end)
        for occ_start_aware in rule.between(lo, hi, inc=True):
            origin = occ_start_aware.replace(tzinfo=None)
            seen.add(origin)
            occ = _materialize(event, origin, duration, overrides.get(origin))
            if occ and occ.start_at < end and occ.end_at > start:
                out.append(occ)
            if len(out) >= MAX_OCCURRENCES:
                break

        # An override can also move an instance whose *original* time fell
        # outside the window into it.
        for origin, ov in overrides.items():
            if origin in seen or ov.canceled:
                continue
            occ = _materialize(event, origin, duration, ov)
            if occ and occ.start_at < end and occ.end_at > start:
                out.append(occ)

    out.sort(key=lambda occurrence: occurrence.start_at)
    return out[:MAX_OCCURRENCES]


def _materialize(
    event: Event, origin: datetime, duration: timedelta, override: EventOverride | None
) -> Occurrence | None:
    if override and override.canceled:
        return None
    eff_start = override.start_at if override and override.start_at else origin
    eff_end = override.end_at if override and override.end_at else eff_start + duration
    return _occurrence(
        event, origin, eff_start, eff_end, recurring=True, override=override
    )


# --------------------------------------------------------------------------- #
# Per-occurrence overrides
# --------------------------------------------------------------------------- #
def _occurrence_exists(event: Event, occurrence_start: datetime) -> bool:
    if not event.recurrence:
        return False
    rule = rrulestr(event.recurrence, dtstart=_aware(event.start_at))
    target = _aware(occurrence_start)
    return bool(rule.between(target, target, inc=True))


def list_overrides(db: Session, user_id: int, event_id: int) -> Sequence[EventOverride]:
    return db.scalars(
        select(EventOverride)
        .where(EventOverride.user_id == user_id, EventOverride.event_id == event_id)
        .order_by(EventOverride.occurrence_start)
    ).all()


def get_override(db: Session, user_id: int, override_id: int) -> EventOverride | None:
    return db.scalars(
        select(EventOverride).where(
            EventOverride.id == override_id, EventOverride.user_id == user_id
        )
    ).first()


def upsert_override(
    db: Session, user_id: int, event: Event, data: EventOverrideCreate
) -> EventOverride:
    origin = _to_naive_utc(data.occurrence_start)
    if not _occurrence_exists(event, origin):
        raise LookupError("occurrence_start is not an instance of this event's recurrence")

    fields = data.model_dump(exclude={"occurrence_start"})
    for key in ("start_at", "end_at"):
        if fields.get(key) is not None:
            fields[key] = _to_naive_utc(fields[key])

    existing = db.scalars(
        select(EventOverride).where(
            EventOverride.event_id == event.id,
            EventOverride.occurrence_start == origin,
        )
    ).first()
    if existing is not None:
        for key, value in fields.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    override = EventOverride(
        user_id=user_id, event_id=event.id, occurrence_start=origin, **fields
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


def delete_override(db: Session, override: EventOverride) -> None:
    db.delete(override)
    db.commit()

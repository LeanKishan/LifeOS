from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core import db as _db
from app.core.redis import get_redis
from app.models.calendar import Reminder
from app.models.user import User
from app.realtime.manager import publish
from app.services import calendar as calendar_svc
from app.services import finance as finance_svc
from app.services import learning as learning_svc
from app.services.reports import render_finance_report_pdf, store_report
from app.worker.celery_app import celery_app

_TRIGGER_WINDOW_SECONDS = 90
_DEDUP_TTL_SECONDS = 2 * 86400


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@celery_app.task(name="app.worker.tasks.dispatch_due_reminders")
def dispatch_due_reminders() -> dict[str, int]:
    """Push a notification for every reminder whose lead time lands about now.

    Runs on beat every 60s; a Redis key per (reminder, occurrence) makes it
    at-most-once even if beat is late or double-fires.
    """
    now = _utc_now()
    client = get_redis()
    fired = 0

    with _db.SessionLocal() as db:
        reminders = list(db.scalars(select(Reminder)))
        if not reminders:
            return {"fired": 0}

        by_user: dict[int, list[Reminder]] = defaultdict(list)
        for reminder in reminders:
            by_user[reminder.user_id].append(reminder)

        for user_id, user_reminders in by_user.items():
            horizon = max(r.minutes_before for r in user_reminders)
            occurrences = calendar_svc.expand_occurrences(
                db, user_id, now, now + timedelta(minutes=horizon + 2)
            )
            occ_by_event: dict[int, list[calendar_svc.Occurrence]] = defaultdict(list)
            for occ in occurrences:
                occ_by_event[occ.event_id].append(occ)

            for reminder in user_reminders:
                lead = timedelta(minutes=reminder.minutes_before)
                for occ in occ_by_event.get(reminder.event_id, []):
                    offset = abs((occ.start_at - lead - now).total_seconds())
                    if offset > _TRIGGER_WINDOW_SECONDS:
                        continue
                    dedup = f"reminder-fired:{reminder.id}:{occ.start_at.isoformat()}"
                    if client.set(dedup, "1", nx=True, ex=_DEDUP_TTL_SECONDS):
                        publish(
                            user_id,
                            {
                                "type": "notification",
                                "level": "info",
                                "message": f"Reminder: {occ.title} at {occ.start_at:%H:%M} UTC",
                            },
                        )
                        fired += 1

    return {"fired": fired}


@celery_app.task(name="app.worker.tasks.send_daily_digest")
def send_daily_digest() -> dict[str, int]:
    """One "here's your day" notification per active user (beat, daily)."""
    now = _utc_now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    sent = 0

    with _db.SessionLocal() as db:
        users = list(db.scalars(select(User).where(User.is_active.is_(True))))
        for user in users:
            parts: list[str] = []

            events = calendar_svc.expand_occurrences(db, user.id, day_start, day_end)
            if events:
                parts.append(f"{len(events)} event{'s' if len(events) != 1 else ''} today")

            due_cards = len(learning_svc.review_queue(db, user.id))
            if due_cards:
                plural = "s" if due_cards != 1 else ""
                parts.append(f"{due_cards} flashcard{plural} to review")

            if parts:
                publish(
                    user.id,
                    {
                        "type": "notification",
                        "level": "info",
                        "message": "Today: " + ", ".join(parts),
                    },
                )
                sent += 1

    return {"sent": sent}


@celery_app.task(name="app.worker.tasks.generate_finance_report")
def generate_finance_report(user_id: int, month: str) -> dict[str, int]:
    """Render the month's finance summary to a PDF, stash it in Redis, notify."""
    with _db.SessionLocal() as db:
        summary = finance_svc.summarize(db, user_id, month)

    pdf = render_finance_report_pdf(summary)
    store_report(get_redis(), user_id, month, pdf)
    publish(
        user_id,
        {
            "type": "notification",
            "level": "success",
            "message": f"Your {month} finance report is ready.",
        },
    )
    return {"bytes": len(pdf)}

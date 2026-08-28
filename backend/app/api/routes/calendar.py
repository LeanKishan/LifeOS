from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.calendar import Event, Reminder
from app.schemas.calendar import (
    EventCreate,
    EventRead,
    EventUpdate,
    OccurrenceRead,
    ReminderCreate,
    ReminderRead,
)
from app.services import calendar as svc

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _404(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


def _422(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _event_or_404(db: DbSession, user: CurrentUser, event_id: int) -> Event:
    event = svc.get_event(db, user.id, event_id)
    if event is None:
        raise _404("Event")
    return event


def _reminder_or_404(db: DbSession, user: CurrentUser, reminder_id: int) -> Reminder:
    reminder = svc.get_reminder(db, user.id, reminder_id)
    if reminder is None:
        raise _404("Reminder")
    return reminder


# --------------------------------------------------------------------------- #
# Occurrences (the calendar view)
# --------------------------------------------------------------------------- #
@router.get("/occurrences", response_model=list[OccurrenceRead])
def occurrences(
    user: CurrentUser,
    db: DbSession,
    from_: datetime = Query(alias="from"),
    to: datetime = Query(alias="to"),
) -> list[svc.Occurrence]:
    try:
        return svc.expand_occurrences(db, user.id, from_, to)
    except LookupError as exc:
        raise _422(str(exc)) from exc


# --------------------------------------------------------------------------- #
# Events
# --------------------------------------------------------------------------- #
@router.get("/events", response_model=list[EventRead])
def list_events(user: CurrentUser, db: DbSession) -> Sequence[Event]:
    return svc.list_events(db, user.id)


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(data: EventCreate, user: CurrentUser, db: DbSession) -> Event:
    try:
        return svc.create_event(db, user.id, data)
    except LookupError as exc:
        raise _422(str(exc)) from exc


@router.get("/events/{event_id}", response_model=EventRead)
def read_event(event_id: int, user: CurrentUser, db: DbSession) -> Event:
    return _event_or_404(db, user, event_id)


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(
    event_id: int, data: EventUpdate, user: CurrentUser, db: DbSession
) -> Event:
    event = _event_or_404(db, user, event_id)
    try:
        return svc.update_event(db, user.id, event, data)
    except LookupError as exc:
        raise _422(str(exc)) from exc


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_event(db, _event_or_404(db, user, event_id))


# --------------------------------------------------------------------------- #
# Reminders
# --------------------------------------------------------------------------- #
@router.post(
    "/events/{event_id}/reminders",
    response_model=ReminderRead,
    status_code=status.HTTP_201_CREATED,
)
def add_reminder(
    event_id: int, data: ReminderCreate, user: CurrentUser, db: DbSession
) -> Reminder:
    return svc.add_reminder(db, user.id, _event_or_404(db, user, event_id), data)


@router.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_reminder(db, _reminder_or_404(db, user, reminder_id))

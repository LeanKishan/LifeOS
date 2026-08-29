from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class _FromORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _as_utc_iso(value: datetime) -> str:
    """Naive values are stored as UTC; make that explicit on the way out."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


# --------------------------------------------------------------------------- #
# Reminders
# --------------------------------------------------------------------------- #
class ReminderCreate(BaseModel):
    minutes_before: int = Field(ge=0, le=60 * 24 * 7)


class ReminderRead(_FromORM):
    id: int
    event_id: int
    minutes_before: int


# --------------------------------------------------------------------------- #
# Events
# --------------------------------------------------------------------------- #
class EventBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    location: str | None = Field(default=None, max_length=300)
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    recurrence: str | None = Field(default=None, max_length=500)
    project_id: int | None = None
    task_id: int | None = None
    application_id: int | None = None


class EventCreate(EventBase):
    @model_validator(mode="after")
    def _end_after_start(self) -> EventCreate:
        if self.end_at < self.start_at:
            raise ValueError("end_at must not be before start_at")
        return self


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    location: str | None = Field(default=None, max_length=300)
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    recurrence: str | None = Field(default=None, max_length=500)
    project_id: int | None = None
    task_id: int | None = None
    application_id: int | None = None


class EventRead(_FromORM):
    id: int
    title: str
    description: str | None
    location: str | None
    start_at: datetime
    end_at: datetime
    all_day: bool
    recurrence: str | None
    project_id: int | None
    task_id: int | None
    application_id: int | None
    reminders: list[ReminderRead] = Field(default_factory=list)
    created_at: datetime

    @field_serializer("start_at", "end_at", "created_at")
    def _serialize_dt(self, value: datetime) -> str:
        return _as_utc_iso(value)


class OccurrenceRead(_FromORM):
    event_id: int
    title: str
    description: str | None
    location: str | None
    all_day: bool
    is_recurring: bool
    # The rule-generated start this instance came from (its RECURRENCE-ID);
    # equals start_at for a non-overridden instance. Address overrides by it.
    occurrence_start: datetime
    overridden: bool
    start_at: datetime
    end_at: datetime

    @field_serializer("start_at", "end_at", "occurrence_start")
    def _serialize_dt(self, value: datetime) -> str:
        return _as_utc_iso(value)


# --------------------------------------------------------------------------- #
# Per-occurrence overrides
# --------------------------------------------------------------------------- #
class EventOverrideCreate(BaseModel):
    occurrence_start: datetime
    canceled: bool = False
    start_at: datetime | None = None
    end_at: datetime | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    location: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def _end_after_start(self) -> EventOverrideCreate:
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must not be before start_at")
        return self


class EventOverrideRead(_FromORM):
    id: int
    event_id: int
    occurrence_start: datetime
    canceled: bool
    start_at: datetime | None
    end_at: datetime | None
    title: str | None
    description: str | None
    location: str | None
    created_at: datetime

    @field_serializer("occurrence_start", "created_at")
    def _serialize_dt(self, value: datetime) -> str:
        return _as_utc_iso(value)

    @field_serializer("start_at", "end_at")
    def _serialize_opt_dt(self, value: datetime | None) -> str | None:
        return _as_utc_iso(value) if value is not None else None

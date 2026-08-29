from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(300))

    # Stored as naive UTC (see ADR-0014).
    start_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    all_day: Mapped[bool] = mapped_column(default=False)

    # iCalendar RRULE string, e.g. "FREQ=WEEKLY;BYDAY=MO,WE;COUNT=10". Null = one-off.
    recurrence: Mapped[str | None] = mapped_column(String(500))

    # Optional cross-links into other modules.
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), index=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), index=True
    )

    reminders: Mapped[list[Reminder]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="Reminder.minutes_before",
    )
    overrides: Mapped[list[EventOverride]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventOverride.occurrence_start",
    )


class EventOverride(TimestampMixin, Base):
    """A single occurrence of a recurring event, changed or cancelled.

    Keyed by ``occurrence_start`` — the *original* start the recurrence rule
    produced (the iCalendar RECURRENCE-ID). NULL override columns inherit from
    the parent event.
    """

    __tablename__ = "event_overrides"
    __table_args__ = (
        UniqueConstraint("event_id", "occurrence_start", name="uq_override_instance"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )

    # Naive UTC, matches Event.start_at.
    occurrence_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    canceled: Mapped[bool] = mapped_column(default=False)

    start_at: Mapped[datetime | None] = mapped_column(DateTime)
    end_at: Mapped[datetime | None] = mapped_column(DateTime)
    title: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(300))

    event: Mapped[Event] = relationship(back_populates="overrides")


class Reminder(TimestampMixin, Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    minutes_before: Mapped[int] = mapped_column(default=10)

    event: Mapped[Event] = relationship(back_populates="reminders")

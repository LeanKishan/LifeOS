from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

DEFAULT_EASE = 2.5


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    archived: Mapped[bool] = mapped_column(default=False)

    lessons: Mapped[list[Lesson]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.position",
    )
    flashcards: Mapped[list[Flashcard]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    notes: Mapped[list[Note]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(default=0)
    completed: Mapped[bool] = mapped_column(default=False)
    completed_on: Mapped[date | None] = mapped_column(Date)

    course: Mapped[Course] = relationship(back_populates="lessons")


class Note(TimestampMixin, Base):
    __tablename__ = "learning_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[int | None] = mapped_column(
        ForeignKey("lessons.id", ondelete="SET NULL"), index=True
    )
    body: Mapped[str] = mapped_column(Text)

    course: Mapped[Course] = relationship(back_populates="notes")


class Flashcard(TimestampMixin, Base):
    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)

    # SM-2 scheduling state.
    ease_factor: Mapped[float] = mapped_column(default=DEFAULT_EASE)
    interval_days: Mapped[int] = mapped_column(default=0)
    repetitions: Mapped[int] = mapped_column(default=0)
    due_on: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    last_reviewed_on: Mapped[date | None] = mapped_column(Date)

    course: Mapped[Course] = relationship(back_populates="flashcards")


class LearningGoal(TimestampMixin, Base):
    __tablename__ = "learning_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    target_date: Mapped[date | None] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(default=False)

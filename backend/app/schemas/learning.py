from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class _FromORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Lessons
# --------------------------------------------------------------------------- #
class LessonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str | None = None


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    content: str | None = None
    completed: bool | None = None


class LessonMove(BaseModel):
    position: int = Field(ge=0)


class LessonRead(_FromORM):
    id: int
    course_id: int
    title: str
    content: str | None
    position: int
    completed: bool
    completed_on: date | None


# --------------------------------------------------------------------------- #
# Notes
# --------------------------------------------------------------------------- #
class NoteCreate(BaseModel):
    body: str = Field(min_length=1)
    lesson_id: int | None = None


class NoteUpdate(BaseModel):
    body: str | None = Field(default=None, min_length=1)
    lesson_id: int | None = None


class NoteRead(_FromORM):
    id: int
    course_id: int
    lesson_id: int | None
    body: str
    created_at: datetime


# --------------------------------------------------------------------------- #
# Flashcards
# --------------------------------------------------------------------------- #
class FlashcardCreate(BaseModel):
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)


class FlashcardUpdate(BaseModel):
    front: str | None = Field(default=None, min_length=1)
    back: str | None = Field(default=None, min_length=1)


class FlashcardRead(_FromORM):
    id: int
    course_id: int
    front: str
    back: str
    ease_factor: float
    interval_days: int
    repetitions: int
    due_on: date
    last_reviewed_on: date | None


class ReviewRequest(BaseModel):
    quality: int = Field(ge=0, le=5)


# --------------------------------------------------------------------------- #
# Goals
# --------------------------------------------------------------------------- #
class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    target_date: date | None = None
    course_id: int | None = None


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    target_date: date | None = None
    course_id: int | None = None
    done: bool | None = None


class GoalRead(_FromORM):
    id: int
    title: str
    target_date: date | None
    course_id: int | None
    done: bool
    created_at: datetime


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #
class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    archived: bool | None = None


class CourseRead(BaseModel):
    id: int
    title: str
    description: str | None
    archived: bool
    created_at: datetime
    lesson_count: int
    lessons_completed: int
    progress: float
    flashcards_due: int


class CourseDetail(CourseRead):
    lessons: list[LessonRead] = Field(default_factory=list)

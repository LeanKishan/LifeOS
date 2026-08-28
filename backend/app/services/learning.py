from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.models.learning import (
    Course,
    Flashcard,
    LearningGoal,
    Lesson,
    Note,
)
from app.schemas.learning import (
    CourseCreate,
    CourseDetail,
    CourseRead,
    CourseUpdate,
    FlashcardCreate,
    FlashcardUpdate,
    GoalCreate,
    GoalUpdate,
    LessonCreate,
    LessonUpdate,
    NoteCreate,
    NoteUpdate,
)

MIN_EASE = 1.3


def _apply(obj: object, changes: dict[str, object]) -> None:
    for field, value in changes.items():
        setattr(obj, field, value)


# --------------------------------------------------------------------------- #
# SM-2 spaced repetition
# --------------------------------------------------------------------------- #
def apply_sm2(card: Flashcard, quality: int, today: date) -> None:
    """Update a card's schedule in place after a review (quality 0..5)."""
    if not 0 <= quality <= 5:
        raise ValueError("quality must be between 0 and 5")

    delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    card.ease_factor = max(MIN_EASE, round(card.ease_factor + delta, 4))

    if quality < 3:
        card.repetitions = 0
        card.interval_days = 1
    else:
        card.repetitions += 1
        if card.repetitions == 1:
            card.interval_days = 1
        elif card.repetitions == 2:
            card.interval_days = 6
        else:
            card.interval_days = round(card.interval_days * card.ease_factor)

    card.due_on = today + timedelta(days=card.interval_days)
    card.last_reviewed_on = today


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #
def get_course(db: Session, user_id: int, course_id: int) -> Course | None:
    return db.scalars(
        select(Course).where(Course.id == course_id, Course.user_id == user_id)
    ).first()


def _course_stats(
    db: Session, user_id: int, today: date
) -> tuple[dict[int, tuple[int, int]], dict[int, int]]:
    lesson_rows = db.execute(
        select(
            Lesson.course_id,
            func.count(),
            func.sum(case((Lesson.completed, 1), else_=0)),
        )
        .where(Lesson.user_id == user_id)
        .group_by(Lesson.course_id)
    ).all()
    lessons = {
        course_id: (int(total or 0), int(done or 0))
        for course_id, total, done in lesson_rows
    }

    due_rows = db.execute(
        select(Flashcard.course_id, func.count())
        .where(Flashcard.user_id == user_id, Flashcard.due_on <= today)
        .group_by(Flashcard.course_id)
    ).all()
    due = {course_id: int(total or 0) for course_id, total in due_rows}
    return lessons, due


def _to_course_read(course: Course, lessons: tuple[int, int], due: int) -> CourseRead:
    total, completed = lessons
    return CourseRead(
        id=course.id,
        title=course.title,
        description=course.description,
        archived=course.archived,
        created_at=course.created_at,
        lesson_count=total,
        lessons_completed=completed,
        progress=round(completed / total, 4) if total else 0.0,
        flashcards_due=due,
    )


def list_courses(
    db: Session, user_id: int, *, include_archived: bool = False, today: date | None = None
) -> list[CourseRead]:
    today = today or date.today()
    stmt = select(Course).where(Course.user_id == user_id)
    if not include_archived:
        stmt = stmt.where(Course.archived.is_(False))
    courses = db.scalars(stmt.order_by(Course.title)).all()
    lessons, due = _course_stats(db, user_id, today)
    return [
        _to_course_read(course, lessons.get(course.id, (0, 0)), due.get(course.id, 0))
        for course in courses
    ]


def course_detail(
    db: Session, user_id: int, course: Course, *, today: date | None = None
) -> CourseDetail:
    today = today or date.today()
    lessons, due = _course_stats(db, user_id, today)
    base = _to_course_read(course, lessons.get(course.id, (0, 0)), due.get(course.id, 0))
    ordered = db.scalars(
        select(Lesson)
        .where(Lesson.course_id == course.id)
        .order_by(Lesson.position)
    ).all()
    return CourseDetail(**base.model_dump(), lessons=list(ordered))


def create_course(db: Session, user_id: int, data: CourseCreate) -> Course:
    course = Course(user_id=user_id, **data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course: Course, data: CourseUpdate) -> Course:
    _apply(course, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()


# --------------------------------------------------------------------------- #
# Lessons
# --------------------------------------------------------------------------- #
def get_lesson(db: Session, user_id: int, lesson_id: int) -> Lesson | None:
    return db.scalars(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.user_id == user_id)
    ).first()


def _lessons_of(db: Session, course_id: int, *, exclude_id: int | None = None) -> list[Lesson]:
    stmt = select(Lesson).where(Lesson.course_id == course_id)
    if exclude_id is not None:
        stmt = stmt.where(Lesson.id != exclude_id)
    return list(db.scalars(stmt.order_by(Lesson.position)))


def create_lesson(db: Session, user_id: int, course: Course, data: LessonCreate) -> Lesson:
    position = len(_lessons_of(db, course.id))
    lesson = Lesson(
        user_id=user_id, course_id=course.id, position=position, **data.model_dump()
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def update_lesson(db: Session, lesson: Lesson, data: LessonUpdate, today: date) -> Lesson:
    changes = data.model_dump(exclude_unset=True)
    if "completed" in changes:
        lesson.completed = bool(changes.pop("completed"))
        lesson.completed_on = today if lesson.completed else None
    _apply(lesson, changes)
    db.commit()
    db.refresh(lesson)
    return lesson


def move_lesson(db: Session, lesson: Lesson, position: int) -> None:
    siblings = _lessons_of(db, lesson.course_id, exclude_id=lesson.id)
    index = max(0, min(position, len(siblings)))
    siblings.insert(index, lesson)
    for order, item in enumerate(siblings):
        item.position = order
    db.commit()


def delete_lesson(db: Session, lesson: Lesson) -> None:
    course_id = lesson.course_id
    db.delete(lesson)
    db.flush()
    for order, item in enumerate(_lessons_of(db, course_id)):
        item.position = order
    db.commit()


# --------------------------------------------------------------------------- #
# Notes
# --------------------------------------------------------------------------- #
def list_notes(db: Session, user_id: int, course_id: int) -> Sequence[Note]:
    return db.scalars(
        select(Note)
        .where(Note.user_id == user_id, Note.course_id == course_id)
        .order_by(Note.created_at.desc())
    ).all()


def get_note(db: Session, user_id: int, note_id: int) -> Note | None:
    return db.scalars(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
    ).first()


def create_note(db: Session, user_id: int, course: Course, data: NoteCreate) -> Note:
    note = Note(user_id=user_id, course_id=course.id, **data.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_note(db: Session, note: Note, data: NoteUpdate) -> Note:
    _apply(note, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note: Note) -> None:
    db.delete(note)
    db.commit()


# --------------------------------------------------------------------------- #
# Flashcards
# --------------------------------------------------------------------------- #
def _flashcard_query(user_id: int) -> Select[tuple[Flashcard]]:
    return select(Flashcard).where(Flashcard.user_id == user_id)


def list_flashcards(db: Session, user_id: int, course_id: int) -> Sequence[Flashcard]:
    return db.scalars(
        _flashcard_query(user_id)
        .where(Flashcard.course_id == course_id)
        .order_by(Flashcard.created_at)
    ).all()


def get_flashcard(db: Session, user_id: int, flashcard_id: int) -> Flashcard | None:
    return db.scalars(_flashcard_query(user_id).where(Flashcard.id == flashcard_id)).first()


def create_flashcard(
    db: Session, user_id: int, course: Course, data: FlashcardCreate, today: date
) -> Flashcard:
    card = Flashcard(
        user_id=user_id, course_id=course.id, due_on=today, **data.model_dump()
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def update_flashcard(db: Session, card: Flashcard, data: FlashcardUpdate) -> Flashcard:
    _apply(card, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(card)
    return card


def delete_flashcard(db: Session, card: Flashcard) -> None:
    db.delete(card)
    db.commit()


def review_queue(
    db: Session,
    user_id: int,
    *,
    today: date | None = None,
    course_id: int | None = None,
    limit: int = 50,
) -> Sequence[Flashcard]:
    today = today or date.today()
    stmt = _flashcard_query(user_id).where(Flashcard.due_on <= today)
    if course_id is not None:
        stmt = stmt.where(Flashcard.course_id == course_id)
    return db.scalars(
        stmt.order_by(Flashcard.due_on, Flashcard.id).limit(limit)
    ).all()


def review_flashcard(
    db: Session, card: Flashcard, quality: int, today: date | None = None
) -> Flashcard:
    apply_sm2(card, quality, today or date.today())
    db.commit()
    db.refresh(card)
    return card


# --------------------------------------------------------------------------- #
# Goals
# --------------------------------------------------------------------------- #
def list_goals(db: Session, user_id: int) -> Sequence[LearningGoal]:
    return db.scalars(
        select(LearningGoal)
        .where(LearningGoal.user_id == user_id)
        .order_by(LearningGoal.done, LearningGoal.target_date.is_(None), LearningGoal.target_date)
    ).all()


def get_goal(db: Session, user_id: int, goal_id: int) -> LearningGoal | None:
    return db.scalars(
        select(LearningGoal).where(
            LearningGoal.id == goal_id, LearningGoal.user_id == user_id
        )
    ).first()


def create_goal(db: Session, user_id: int, data: GoalCreate) -> LearningGoal:
    goal = LearningGoal(user_id=user_id, **data.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, goal: LearningGoal, data: GoalUpdate) -> LearningGoal:
    _apply(goal, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, goal: LearningGoal) -> None:
    db.delete(goal)
    db.commit()

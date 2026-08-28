from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.learning import Course, Flashcard, LearningGoal, Lesson, Note
from app.schemas.learning import (
    CourseCreate,
    CourseDetail,
    CourseRead,
    CourseUpdate,
    FlashcardCreate,
    FlashcardRead,
    FlashcardUpdate,
    GoalCreate,
    GoalRead,
    GoalUpdate,
    LessonCreate,
    LessonMove,
    LessonRead,
    LessonUpdate,
    NoteCreate,
    NoteRead,
    NoteUpdate,
    ReviewRequest,
)
from app.services import learning as svc

router = APIRouter(prefix="/learning", tags=["learning"])


def _404(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


def _course_or_404(db: DbSession, user: CurrentUser, course_id: int) -> Course:
    course = svc.get_course(db, user.id, course_id)
    if course is None:
        raise _404("Course")
    return course


def _lesson_or_404(db: DbSession, user: CurrentUser, lesson_id: int) -> Lesson:
    lesson = svc.get_lesson(db, user.id, lesson_id)
    if lesson is None:
        raise _404("Lesson")
    return lesson


def _note_or_404(db: DbSession, user: CurrentUser, note_id: int) -> Note:
    note = svc.get_note(db, user.id, note_id)
    if note is None:
        raise _404("Note")
    return note


def _flashcard_or_404(db: DbSession, user: CurrentUser, flashcard_id: int) -> Flashcard:
    card = svc.get_flashcard(db, user.id, flashcard_id)
    if card is None:
        raise _404("Flashcard")
    return card


def _goal_or_404(db: DbSession, user: CurrentUser, goal_id: int) -> LearningGoal:
    goal = svc.get_goal(db, user.id, goal_id)
    if goal is None:
        raise _404("Goal")
    return goal


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #
@router.get("/courses", response_model=list[CourseRead])
def list_courses(
    user: CurrentUser, db: DbSession, archived: bool = Query(default=False)
) -> list[CourseRead]:
    return svc.list_courses(db, user.id, include_archived=archived)


@router.post("/courses", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, user: CurrentUser, db: DbSession) -> CourseRead:
    course = svc.create_course(db, user.id, data)
    return svc.course_detail(db, user.id, course)


@router.get("/courses/{course_id}", response_model=CourseDetail)
def read_course(course_id: int, user: CurrentUser, db: DbSession) -> CourseDetail:
    return svc.course_detail(db, user.id, _course_or_404(db, user, course_id))


@router.patch("/courses/{course_id}", response_model=CourseDetail)
def update_course(
    course_id: int, data: CourseUpdate, user: CurrentUser, db: DbSession
) -> CourseDetail:
    course = svc.update_course(db, _course_or_404(db, user, course_id), data)
    return svc.course_detail(db, user.id, course)


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_course(db, _course_or_404(db, user, course_id))


# --------------------------------------------------------------------------- #
# Lessons
# --------------------------------------------------------------------------- #
@router.post(
    "/courses/{course_id}/lessons",
    response_model=LessonRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    course_id: int, data: LessonCreate, user: CurrentUser, db: DbSession
) -> Lesson:
    return svc.create_lesson(db, user.id, _course_or_404(db, user, course_id), data)


@router.patch("/lessons/{lesson_id}", response_model=LessonRead)
def update_lesson(
    lesson_id: int, data: LessonUpdate, user: CurrentUser, db: DbSession
) -> Lesson:
    return svc.update_lesson(
        db, _lesson_or_404(db, user, lesson_id), data, date.today()
    )


@router.post("/lessons/{lesson_id}/move", response_model=LessonRead)
def move_lesson(
    lesson_id: int, data: LessonMove, user: CurrentUser, db: DbSession
) -> Lesson:
    lesson = _lesson_or_404(db, user, lesson_id)
    svc.move_lesson(db, lesson, data.position)
    return _lesson_or_404(db, user, lesson_id)


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(lesson_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_lesson(db, _lesson_or_404(db, user, lesson_id))


# --------------------------------------------------------------------------- #
# Notes
# --------------------------------------------------------------------------- #
@router.get("/courses/{course_id}/notes", response_model=list[NoteRead])
def list_notes(course_id: int, user: CurrentUser, db: DbSession) -> Sequence[Note]:
    _course_or_404(db, user, course_id)
    return svc.list_notes(db, user.id, course_id)


@router.post(
    "/courses/{course_id}/notes",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    course_id: int, data: NoteCreate, user: CurrentUser, db: DbSession
) -> Note:
    return svc.create_note(db, user.id, _course_or_404(db, user, course_id), data)


@router.patch("/notes/{note_id}", response_model=NoteRead)
def update_note(
    note_id: int, data: NoteUpdate, user: CurrentUser, db: DbSession
) -> Note:
    return svc.update_note(db, _note_or_404(db, user, note_id), data)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_note(db, _note_or_404(db, user, note_id))


# --------------------------------------------------------------------------- #
# Flashcards
# --------------------------------------------------------------------------- #
@router.get("/courses/{course_id}/flashcards", response_model=list[FlashcardRead])
def list_flashcards(
    course_id: int, user: CurrentUser, db: DbSession
) -> Sequence[Flashcard]:
    _course_or_404(db, user, course_id)
    return svc.list_flashcards(db, user.id, course_id)


@router.post(
    "/courses/{course_id}/flashcards",
    response_model=FlashcardRead,
    status_code=status.HTTP_201_CREATED,
)
def create_flashcard(
    course_id: int, data: FlashcardCreate, user: CurrentUser, db: DbSession
) -> Flashcard:
    return svc.create_flashcard(
        db, user.id, _course_or_404(db, user, course_id), data, date.today()
    )


@router.patch("/flashcards/{flashcard_id}", response_model=FlashcardRead)
def update_flashcard(
    flashcard_id: int, data: FlashcardUpdate, user: CurrentUser, db: DbSession
) -> Flashcard:
    return svc.update_flashcard(db, _flashcard_or_404(db, user, flashcard_id), data)


@router.delete("/flashcards/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flashcard(flashcard_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_flashcard(db, _flashcard_or_404(db, user, flashcard_id))


@router.get("/review", response_model=list[FlashcardRead])
def review_queue(
    user: CurrentUser,
    db: DbSession,
    course_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> Sequence[Flashcard]:
    return svc.review_queue(db, user.id, course_id=course_id, limit=limit)


@router.post("/flashcards/{flashcard_id}/review", response_model=FlashcardRead)
def review_flashcard(
    flashcard_id: int, data: ReviewRequest, user: CurrentUser, db: DbSession
) -> Flashcard:
    card = _flashcard_or_404(db, user, flashcard_id)
    return svc.review_flashcard(db, card, data.quality)


# --------------------------------------------------------------------------- #
# Goals
# --------------------------------------------------------------------------- #
@router.get("/goals", response_model=list[GoalRead])
def list_goals(user: CurrentUser, db: DbSession) -> Sequence[LearningGoal]:
    return svc.list_goals(db, user.id)


@router.post("/goals", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(data: GoalCreate, user: CurrentUser, db: DbSession) -> LearningGoal:
    return svc.create_goal(db, user.id, data)


@router.patch("/goals/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: int, data: GoalUpdate, user: CurrentUser, db: DbSession
) -> LearningGoal:
    return svc.update_goal(db, _goal_or_404(db, user, goal_id), data)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_goal(db, _goal_or_404(db, user, goal_id))

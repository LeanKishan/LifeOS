from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.projects import BoardColumn, Label, Project, Subtask, Task, TaskComment
from app.schemas.projects import (
    BoardRead,
    ColumnCreate,
    ColumnMove,
    ColumnRead,
    ColumnUpdate,
    LabelCreate,
    LabelRead,
    LabelUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    SubtaskCreate,
    SubtaskRead,
    SubtaskUpdate,
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskDetailRead,
    TaskLabelsSet,
    TaskMove,
    TaskUpdate,
)
from app.services import projects as svc

router = APIRouter(prefix="/projects", tags=["projects"])


def _404(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


def _422(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _project_or_404(db: DbSession, user: CurrentUser, project_id: int) -> Project:
    project = svc.get_project(db, user.id, project_id)
    if project is None:
        raise _404("Project")
    return project


def _column_or_404(db: DbSession, user: CurrentUser, column_id: int) -> BoardColumn:
    column = svc.get_column(db, user.id, column_id)
    if column is None:
        raise _404("Column")
    return column


def _task_or_404(db: DbSession, user: CurrentUser, task_id: int) -> Task:
    task = svc.get_task(db, user.id, task_id)
    if task is None:
        raise _404("Task")
    return task


def _subtask_or_404(db: DbSession, user: CurrentUser, subtask_id: int) -> Subtask:
    subtask = svc.get_subtask(db, user.id, subtask_id)
    if subtask is None:
        raise _404("Subtask")
    return subtask


def _label_or_404(db: DbSession, user: CurrentUser, label_id: int) -> Label:
    label = svc.get_label(db, user.id, label_id)
    if label is None:
        raise _404("Label")
    return label


def _comment_or_404(db: DbSession, user: CurrentUser, comment_id: int) -> TaskComment:
    comment = svc.get_comment(db, user.id, comment_id)
    if comment is None:
        raise _404("Comment")
    return comment


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[ProjectRead])
def list_projects(
    user: CurrentUser,
    db: DbSession,
    archived: bool = Query(default=False),
) -> list[ProjectRead]:
    return svc.list_projects(db, user.id, include_archived=archived)


@router.post("", response_model=BoardRead, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, user: CurrentUser, db: DbSession) -> Project:
    return svc.create_project(db, user.id, data)


@router.get("/{project_id}", response_model=BoardRead)
def read_board(project_id: int, user: CurrentUser, db: DbSession) -> Project:
    board = svc.get_board(db, user.id, project_id)
    if board is None:
        raise _404("Project")
    return board


@router.patch("/{project_id}", response_model=BoardRead)
def update_project(
    project_id: int, data: ProjectUpdate, user: CurrentUser, db: DbSession
) -> Project:
    return svc.update_project(db, _project_or_404(db, user, project_id), data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_project(db, _project_or_404(db, user, project_id))


# --------------------------------------------------------------------------- #
# Columns
# --------------------------------------------------------------------------- #
@router.post(
    "/{project_id}/columns", response_model=ColumnRead, status_code=status.HTTP_201_CREATED
)
def create_column(
    project_id: int, data: ColumnCreate, user: CurrentUser, db: DbSession
) -> BoardColumn:
    return svc.create_column(db, user.id, _project_or_404(db, user, project_id), data)


@router.patch("/columns/{column_id}", response_model=ColumnRead)
def update_column(
    column_id: int, data: ColumnUpdate, user: CurrentUser, db: DbSession
) -> BoardColumn:
    return svc.update_column(db, _column_or_404(db, user, column_id), data)


@router.post("/columns/{column_id}/move", response_model=ColumnRead)
def move_column(
    column_id: int, data: ColumnMove, user: CurrentUser, db: DbSession
) -> BoardColumn:
    column = _column_or_404(db, user, column_id)
    svc.move_column(db, column, data.position)
    return _column_or_404(db, user, column_id)


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column(column_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_column(db, _column_or_404(db, user, column_id))


# --------------------------------------------------------------------------- #
# Tasks
# --------------------------------------------------------------------------- #
@router.post(
    "/{project_id}/tasks", response_model=TaskDetailRead, status_code=status.HTTP_201_CREATED
)
def create_task(
    project_id: int, data: TaskCreate, user: CurrentUser, db: DbSession
) -> Task:
    project = _project_or_404(db, user, project_id)
    column = _column_or_404(db, user, data.column_id)
    if column.project_id != project.id:
        raise _422("column_id does not belong to this project")
    return svc.create_task(db, user.id, column, data)


@router.get("/tasks/{task_id}", response_model=TaskDetailRead)
def read_task(task_id: int, user: CurrentUser, db: DbSession) -> Task:
    return _task_or_404(db, user, task_id)


@router.patch("/tasks/{task_id}", response_model=TaskDetailRead)
def update_task(
    task_id: int, data: TaskUpdate, user: CurrentUser, db: DbSession
) -> Task:
    return svc.update_task(db, user.id, _task_or_404(db, user, task_id), data)


@router.post("/tasks/{task_id}/move", response_model=TaskDetailRead)
def move_task(task_id: int, data: TaskMove, user: CurrentUser, db: DbSession) -> Task:
    task = _task_or_404(db, user, task_id)
    target_column = _column_or_404(db, user, data.column_id)
    try:
        return svc.move_task(db, user.id, task, target_column, data.position)
    except LookupError as exc:
        raise _422(str(exc)) from exc


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_task(db, _task_or_404(db, user, task_id))


@router.put("/tasks/{task_id}/labels", response_model=TaskDetailRead)
def set_task_labels(
    task_id: int, data: TaskLabelsSet, user: CurrentUser, db: DbSession
) -> Task:
    task = _task_or_404(db, user, task_id)
    try:
        return svc.set_task_labels(db, user.id, task, data.label_ids)
    except LookupError as exc:
        raise _422(str(exc)) from exc


# --------------------------------------------------------------------------- #
# Subtasks
# --------------------------------------------------------------------------- #
@router.post(
    "/tasks/{task_id}/subtasks",
    response_model=SubtaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_subtask(
    task_id: int, data: SubtaskCreate, user: CurrentUser, db: DbSession
) -> Subtask:
    return svc.create_subtask(db, user.id, _task_or_404(db, user, task_id), data)


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskRead)
def update_subtask(
    subtask_id: int, data: SubtaskUpdate, user: CurrentUser, db: DbSession
) -> Subtask:
    return svc.update_subtask(db, _subtask_or_404(db, user, subtask_id), data)


@router.delete("/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subtask(subtask_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_subtask(db, _subtask_or_404(db, user, subtask_id))


# --------------------------------------------------------------------------- #
# Labels
# --------------------------------------------------------------------------- #
@router.get("/{project_id}/labels", response_model=list[LabelRead])
def list_labels(project_id: int, user: CurrentUser, db: DbSession) -> Sequence[Label]:
    _project_or_404(db, user, project_id)
    return svc.list_labels(db, user.id, project_id)


@router.post(
    "/{project_id}/labels", response_model=LabelRead, status_code=status.HTTP_201_CREATED
)
def create_label(
    project_id: int, data: LabelCreate, user: CurrentUser, db: DbSession
) -> Label:
    return svc.create_label(db, user.id, _project_or_404(db, user, project_id), data)


@router.patch("/labels/{label_id}", response_model=LabelRead)
def update_label(
    label_id: int, data: LabelUpdate, user: CurrentUser, db: DbSession
) -> Label:
    return svc.update_label(db, _label_or_404(db, user, label_id), data)


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(label_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_label(db, _label_or_404(db, user, label_id))


# --------------------------------------------------------------------------- #
# Comments
# --------------------------------------------------------------------------- #
@router.post(
    "/tasks/{task_id}/comments",
    response_model=TaskCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    task_id: int, data: TaskCommentCreate, user: CurrentUser, db: DbSession
) -> TaskComment:
    return svc.create_comment(db, user.id, _task_or_404(db, user, task_id), data)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_comment(db, _comment_or_404(db, user, comment_id))

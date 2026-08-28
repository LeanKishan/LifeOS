from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.projects import TaskPriority


class _FromORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Labels
# --------------------------------------------------------------------------- #
class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#64748b", max_length=20)


class LabelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, max_length=20)


class LabelRead(_FromORM):
    id: int
    name: str
    color: str


# --------------------------------------------------------------------------- #
# Subtasks
# --------------------------------------------------------------------------- #
class SubtaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)


class SubtaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    done: bool | None = None


class SubtaskRead(_FromORM):
    id: int
    task_id: int
    title: str
    done: bool
    position: int


# --------------------------------------------------------------------------- #
# Comments
# --------------------------------------------------------------------------- #
class TaskCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class TaskCommentRead(_FromORM):
    id: int
    task_id: int
    body: str
    created_at: datetime


# --------------------------------------------------------------------------- #
# Tasks
# --------------------------------------------------------------------------- #
class TaskCreate(BaseModel):
    column_id: int
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_on: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    priority: TaskPriority | None = None
    due_on: date | None = None
    done: bool | None = None


class TaskMove(BaseModel):
    column_id: int
    position: int = Field(ge=0)


class TaskCardRead(_FromORM):
    id: int
    column_id: int
    title: str
    priority: TaskPriority
    due_on: date | None
    position: int
    done: bool
    completed_at: datetime | None
    labels: list[LabelRead] = Field(default_factory=list)
    subtask_total: int
    subtask_done: int
    comment_count: int


class TaskDetailRead(TaskCardRead):
    project_id: int
    description: str | None
    subtasks: list[SubtaskRead] = Field(default_factory=list)
    comments: list[TaskCommentRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Columns
# --------------------------------------------------------------------------- #
class ColumnCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ColumnUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class ColumnMove(BaseModel):
    position: int = Field(ge=0)


class ColumnRead(_FromORM):
    id: int
    project_id: int
    name: str
    position: int
    tasks: list[TaskCardRead] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    archived: bool | None = None


class ProjectRead(BaseModel):
    id: int
    name: str
    description: str | None
    archived: bool
    created_at: datetime
    task_count: int


class BoardRead(_FromORM):
    id: int
    name: str
    description: str | None
    archived: bool
    columns: list[ColumnRead] = Field(default_factory=list)
    labels: list[LabelRead] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Task <-> label assignment
# --------------------------------------------------------------------------- #
class TaskLabelsSet(BaseModel):
    label_ids: list[int]

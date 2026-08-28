from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.projects import (
    BoardColumn,
    Label,
    Project,
    Subtask,
    Task,
    TaskComment,
)
from app.schemas.projects import (
    ColumnCreate,
    ColumnUpdate,
    LabelCreate,
    LabelUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    SubtaskCreate,
    SubtaskUpdate,
    TaskCommentCreate,
    TaskCreate,
    TaskUpdate,
)

DEFAULT_COLUMNS = ("To Do", "In Progress", "Done")


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def _reindex(items: Sequence[BoardColumn | Task | Subtask]) -> None:
    for index, item in enumerate(items):
        item.position = index


def _apply_changes(obj: object, changes: dict[str, object]) -> None:
    for field, value in changes.items():
        setattr(obj, field, value)


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
def _board_query(user_id: int) -> Select[tuple[Project]]:
    task_loader = selectinload(Project.columns).selectinload(BoardColumn.tasks)
    return (
        select(Project)
        .where(Project.user_id == user_id)
        .options(
            selectinload(Project.labels),
            task_loader.selectinload(Task.labels),
            task_loader.selectinload(Task.subtasks),
            task_loader.selectinload(Task.comments),
        )
    )


def list_projects(
    db: Session, user_id: int, *, include_archived: bool = False
) -> list[ProjectRead]:
    stmt = select(Project).where(Project.user_id == user_id)
    if not include_archived:
        stmt = stmt.where(Project.archived.is_(False))
    projects = db.scalars(stmt.order_by(Project.name)).all()

    count_rows = db.execute(
        select(Task.project_id, func.count())
        .where(Task.user_id == user_id)
        .group_by(Task.project_id)
    ).all()
    counts = {project_id: int(count) for project_id, count in count_rows}

    return [
        ProjectRead(
            id=project.id,
            name=project.name,
            description=project.description,
            archived=project.archived,
            created_at=project.created_at,
            task_count=counts.get(project.id, 0),
        )
        for project in projects
    ]


def get_board(db: Session, user_id: int, project_id: int) -> Project | None:
    return db.scalars(_board_query(user_id).where(Project.id == project_id)).first()


def get_project(db: Session, user_id: int, project_id: int) -> Project | None:
    return db.scalars(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    ).first()


def create_project(db: Session, user_id: int, data: ProjectCreate) -> Project:
    project = Project(user_id=user_id, **data.model_dump())
    db.add(project)
    db.flush()
    for position, name in enumerate(DEFAULT_COLUMNS):
        db.add(
            BoardColumn(
                user_id=user_id, project_id=project.id, name=name, position=position
            )
        )
    db.commit()
    return _reload_board(db, user_id, project.id)


def update_project(db: Session, project: Project, data: ProjectUpdate) -> Project:
    _apply_changes(project, data.model_dump(exclude_unset=True))
    db.commit()
    return _reload_board(db, project.user_id, project.id)


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()


def _reload_board(db: Session, user_id: int, project_id: int) -> Project:
    board = get_board(db, user_id, project_id)
    if board is None:  # pragma: no cover - just committed it
        raise RuntimeError("project vanished after commit")
    return board


# --------------------------------------------------------------------------- #
# Columns
# --------------------------------------------------------------------------- #
def get_column(db: Session, user_id: int, column_id: int) -> BoardColumn | None:
    return db.scalars(
        select(BoardColumn).where(
            BoardColumn.id == column_id, BoardColumn.user_id == user_id
        )
    ).first()


def _columns_of(
    db: Session, project_id: int, *, exclude_id: int | None = None
) -> list[BoardColumn]:
    stmt = select(BoardColumn).where(BoardColumn.project_id == project_id)
    if exclude_id is not None:
        stmt = stmt.where(BoardColumn.id != exclude_id)
    return list(db.scalars(stmt.order_by(BoardColumn.position)))


def create_column(db: Session, user_id: int, project: Project, data: ColumnCreate) -> BoardColumn:
    position = len(_columns_of(db, project.id))
    column = BoardColumn(
        user_id=user_id, project_id=project.id, name=data.name, position=position
    )
    db.add(column)
    db.commit()
    db.refresh(column)
    return column


def update_column(db: Session, column: BoardColumn, data: ColumnUpdate) -> BoardColumn:
    _apply_changes(column, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(column)
    return column


def move_column(db: Session, column: BoardColumn, position: int) -> None:
    siblings = _columns_of(db, column.project_id, exclude_id=column.id)
    index = _clamp(position, 0, len(siblings))
    siblings.insert(index, column)
    _reindex(siblings)
    db.commit()


def delete_column(db: Session, column: BoardColumn) -> None:
    db.delete(column)
    db.flush()
    _reindex(_columns_of(db, column.project_id))
    db.commit()


# --------------------------------------------------------------------------- #
# Tasks
# --------------------------------------------------------------------------- #
def _task_query(user_id: int) -> Select[tuple[Task]]:
    return (
        select(Task)
        .where(Task.user_id == user_id)
        .options(
            selectinload(Task.labels),
            selectinload(Task.subtasks),
            selectinload(Task.comments),
        )
    )


def get_task(db: Session, user_id: int, task_id: int) -> Task | None:
    return db.scalars(_task_query(user_id).where(Task.id == task_id)).first()


def _tasks_in_column(db: Session, column_id: int, *, exclude_id: int | None = None) -> list[Task]:
    stmt = select(Task).where(Task.column_id == column_id)
    if exclude_id is not None:
        stmt = stmt.where(Task.id != exclude_id)
    return list(db.scalars(stmt.order_by(Task.position)))


def create_task(db: Session, user_id: int, column: BoardColumn, data: TaskCreate) -> Task:
    position = len(_tasks_in_column(db, column.id))
    payload = data.model_dump(exclude={"column_id"})
    task = Task(
        user_id=user_id,
        project_id=column.project_id,
        column_id=column.id,
        position=position,
        **payload,
    )
    db.add(task)
    db.commit()
    return _reload_task(db, user_id, task.id)


def update_task(db: Session, user_id: int, task: Task, data: TaskUpdate) -> Task:
    _apply_changes(task, data.model_dump(exclude_unset=True))
    db.commit()
    return _reload_task(db, user_id, task.id)


def move_task(
    db: Session, user_id: int, task: Task, target_column: BoardColumn, position: int
) -> Task:
    if target_column.project_id != task.project_id:
        raise LookupError("target column belongs to a different project")

    if target_column.id == task.column_id:
        siblings = _tasks_in_column(db, task.column_id, exclude_id=task.id)
        siblings.insert(_clamp(position, 0, len(siblings)), task)
        _reindex(siblings)
    else:
        source = _tasks_in_column(db, task.column_id, exclude_id=task.id)
        _reindex(source)
        task.column_id = target_column.id
        destination = _tasks_in_column(db, target_column.id, exclude_id=task.id)
        destination.insert(_clamp(position, 0, len(destination)), task)
        _reindex(destination)

    db.commit()
    return _reload_task(db, user_id, task.id)


def delete_task(db: Session, task: Task) -> None:
    column_id = task.column_id
    db.delete(task)
    db.flush()
    _reindex(_tasks_in_column(db, column_id))
    db.commit()


def _reload_task(db: Session, user_id: int, task_id: int) -> Task:
    task = get_task(db, user_id, task_id)
    if task is None:  # pragma: no cover - just committed it
        raise RuntimeError("task vanished after commit")
    return task


# --------------------------------------------------------------------------- #
# Subtasks
# --------------------------------------------------------------------------- #
def get_subtask(db: Session, user_id: int, subtask_id: int) -> Subtask | None:
    return db.scalars(
        select(Subtask).where(Subtask.id == subtask_id, Subtask.user_id == user_id)
    ).first()


def create_subtask(db: Session, user_id: int, task: Task, data: SubtaskCreate) -> Subtask:
    position = len(list(db.scalars(select(Subtask).where(Subtask.task_id == task.id))))
    subtask = Subtask(
        user_id=user_id, task_id=task.id, title=data.title, position=position
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


def update_subtask(db: Session, subtask: Subtask, data: SubtaskUpdate) -> Subtask:
    _apply_changes(subtask, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(subtask)
    return subtask


def delete_subtask(db: Session, subtask: Subtask) -> None:
    db.delete(subtask)
    db.commit()


# --------------------------------------------------------------------------- #
# Labels
# --------------------------------------------------------------------------- #
def get_label(db: Session, user_id: int, label_id: int) -> Label | None:
    return db.scalars(
        select(Label).where(Label.id == label_id, Label.user_id == user_id)
    ).first()


def list_labels(db: Session, user_id: int, project_id: int) -> Sequence[Label]:
    return db.scalars(
        select(Label)
        .where(Label.user_id == user_id, Label.project_id == project_id)
        .order_by(Label.name)
    ).all()


def create_label(db: Session, user_id: int, project: Project, data: LabelCreate) -> Label:
    label = Label(
        user_id=user_id, project_id=project.id, name=data.name, color=data.color
    )
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


def update_label(db: Session, label: Label, data: LabelUpdate) -> Label:
    _apply_changes(label, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(label)
    return label


def delete_label(db: Session, label: Label) -> None:
    db.delete(label)
    db.commit()


def set_task_labels(db: Session, user_id: int, task: Task, label_ids: list[int]) -> Task:
    wanted = set(label_ids)
    labels = db.scalars(
        select(Label).where(
            Label.id.in_(wanted),
            Label.user_id == user_id,
            Label.project_id == task.project_id,
        )
    ).all()
    missing = wanted - {label.id for label in labels}
    if missing:
        raise LookupError(f"labels not in this project: {sorted(missing)}")
    task.labels = list(labels)
    db.commit()
    return _reload_task(db, user_id, task.id)


# --------------------------------------------------------------------------- #
# Comments
# --------------------------------------------------------------------------- #
def get_comment(db: Session, user_id: int, comment_id: int) -> TaskComment | None:
    return db.scalars(
        select(TaskComment).where(
            TaskComment.id == comment_id, TaskComment.user_id == user_id
        )
    ).first()


def create_comment(
    db: Session, user_id: int, task: Task, data: TaskCommentCreate
) -> TaskComment:
    comment = TaskComment(user_id=user_id, task_id=task.id, body=data.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment: TaskComment) -> None:
    db.delete(comment)
    db.commit()

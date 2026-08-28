from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


task_labels = Table(
    "task_labels",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    archived: Mapped[bool] = mapped_column(default=False)

    columns: Mapped[list[BoardColumn]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="BoardColumn.position",
    )
    labels: Mapped[list[Label]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Label.name",
    )


class BoardColumn(TimestampMixin, Base):
    __tablename__ = "board_columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(default=0)

    project: Mapped[Project] = relationship(back_populates="columns")
    tasks: Mapped[list[Task]] = relationship(
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="Task.position",
    )


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    column_id: Mapped[int] = mapped_column(
        ForeignKey("board_columns.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(
            TaskPriority,
            native_enum=False,
            length=10,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=TaskPriority.MEDIUM,
    )
    due_on: Mapped[date | None] = mapped_column()
    position: Mapped[int] = mapped_column(default=0)
    done: Mapped[bool] = mapped_column(default=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    column: Mapped[BoardColumn] = relationship(back_populates="tasks")
    subtasks: Mapped[list[Subtask]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="Subtask.position",
    )
    comments: Mapped[list[TaskComment]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at",
    )
    labels: Mapped[list[Label]] = relationship(
        secondary=task_labels, order_by="Label.name"
    )

    @property
    def subtask_total(self) -> int:
        return len(self.subtasks)

    @property
    def subtask_done(self) -> int:
        return sum(1 for subtask in self.subtasks if subtask.done)

    @property
    def comment_count(self) -> int:
        return len(self.comments)


class Subtask(TimestampMixin, Base):
    __tablename__ = "subtasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    done: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)

    task: Mapped[Task] = relationship(back_populates="subtasks")


class Label(TimestampMixin, Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(20), default="#64748b")

    project: Mapped[Project] = relationship(back_populates="labels")


class TaskComment(TimestampMixin, Base):
    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)

    task: Mapped[Task] = relationship(back_populates="comments")

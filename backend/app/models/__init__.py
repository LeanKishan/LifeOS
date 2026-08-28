"""SQLAlchemy models.

Import every model module here so ``Base.metadata`` is fully populated
before Alembic autogenerate runs.
"""

from app.models.base import Base
from app.models.calendar import Event, Reminder
from app.models.finance import (
    Account,
    Bill,
    Budget,
    Category,
    Transaction,
    TransactionKind,
)
from app.models.job_tracker import (
    Application,
    ApplicationStatus,
    Company,
    Contact,
    Interview,
)
from app.models.projects import (
    BoardColumn,
    Label,
    Project,
    Subtask,
    Task,
    TaskComment,
    TaskPriority,
)
from app.models.user import User

__all__ = [
    "Account",
    "Application",
    "ApplicationStatus",
    "Base",
    "Bill",
    "BoardColumn",
    "Budget",
    "Category",
    "Company",
    "Contact",
    "Event",
    "Interview",
    "Label",
    "Project",
    "Reminder",
    "Subtask",
    "Task",
    "TaskComment",
    "TaskPriority",
    "Transaction",
    "TransactionKind",
    "User",
]

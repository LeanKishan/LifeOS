"""SQLAlchemy models.

Import every model module here so ``Base.metadata`` is fully populated
before Alembic autogenerate runs.
"""

from app.models.base import Base
from app.models.job_tracker import (
    Application,
    ApplicationStatus,
    Company,
    Contact,
    Interview,
)
from app.models.user import User

__all__ = [
    "Application",
    "ApplicationStatus",
    "Base",
    "Company",
    "Contact",
    "Interview",
    "User",
]

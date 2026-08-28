"""SQLAlchemy models.

Import every model module here so ``Base.metadata`` is fully populated
before Alembic autogenerate runs.
"""

from app.models.base import Base
from app.models.user import User

__all__ = ["Base", "User"]

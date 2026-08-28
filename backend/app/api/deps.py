"""Shared FastAPI dependencies.

``get_current_user`` and friends are added in the authentication milestone.
"""

from app.core.db import get_db

__all__ = ["get_db"]

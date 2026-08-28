from __future__ import annotations

import sqlite3
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
    """SQLite ignores ON DELETE CASCADE / SET NULL unless asked per connection.

    Turning it on makes local SQLite behave like the Postgres used in CI / prod.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _make_engine() -> Engine:
    url = make_url(settings.database_url)

    if url.get_backend_name() == "sqlite":
        # Local dev default. check_same_thread=False so FastAPI's thread pool
        # can share the connection.
        return create_engine(url, future=True, connect_args={"check_same_thread": False})

    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        pool_recycle=1800,
        # Fail fast when the DB is unreachable instead of hanging on the TCP timeout.
        connect_args={"connect_timeout": 5},
    )


engine = _make_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session, always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

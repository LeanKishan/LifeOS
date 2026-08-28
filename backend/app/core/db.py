from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


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

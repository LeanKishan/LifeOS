from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.core.redis import get_redis
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
def _flush_redis() -> Iterator[None]:
    """Each test starts with an empty Redis (denylist / rate limits / cache)."""
    get_redis().flushall()
    yield
    get_redis().flushall()


@pytest.fixture
def db_session(monkeypatch: pytest.MonkeyPatch) -> Iterator[Session]:
    """A fresh in-memory SQLite database per test.

    Also repoints ``app.core.db.SessionLocal`` at it so code that opens its own
    session outside a request (Celery tasks) hits the same database.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr("app.core.db.SessionLocal", testing_session)

    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


AuthHeaderFactory = Callable[..., dict[str, str]]


@pytest.fixture
def make_auth_headers(client: TestClient) -> AuthHeaderFactory:
    """Register a user and return an Authorization header for them."""

    def _make(
        email: str = "owner@example.com", password: str = "password123"
    ) -> dict[str, str]:
        client.post("/api/auth/register", json={"email": email, "password": password})
        resp = client.post(
            "/api/auth/login", data={"username": email, "password": password}
        )
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _make


@pytest.fixture
def auth_headers(make_auth_headers: AuthHeaderFactory) -> dict[str, str]:
    return make_auth_headers()

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.main import app


def test_security_headers_on_every_response(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "no-referrer"
    assert "geolocation=()" in resp.headers["permissions-policy"]
    assert resp.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
    # Tests don't run as production, so no HSTS.
    assert "strict-transport-security" not in resp.headers


def test_oversized_body_is_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.main.settings.max_body_bytes", 100)
    resp = client.post(
        "/api/auth/register",
        json={"email": "big@example.com", "password": "x" * 500},
    )
    assert resp.status_code == 413
    assert resp.json()["detail"] == "Request body too large"


def test_global_mutation_rate_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.main.settings.global_rate_limit_per_minute", 3)
    # Even requests that 4xx count against the ceiling.
    codes = [
        client.post("/api/auth/refresh", json={"refresh_token": "nope"}).status_code
        for _ in range(4)
    ]
    assert codes[:3] == [401, 401, 401]
    assert codes[3] == 429


def test_reads_are_not_rate_limited(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.main.settings.global_rate_limit_per_minute", 1)
    for _ in range(5):
        assert client.get("/api/health").status_code == 200


def test_unhandled_error_returns_a_generic_500(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("secret internal detail that must not leak")

    monkeypatch.setattr("app.services.finance.summarize", boom)

    def override_get_db() -> object:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        safe = TestClient(app, raise_server_exceptions=False)
        safe.post(
            "/api/auth/register",
            json={"email": "e@example.com", "password": "password123"},
        )
        token = safe.post(
            "/api/auth/login",
            data={"username": "e@example.com", "password": "password123"},
        ).json()["access_token"]
        resp = safe.get(
            "/api/finance/summary?month=2026-08",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 500
    body = resp.json()
    assert body["detail"] == "Internal server error"
    assert body["request_id"]  # correlate with the server log
    assert "secret internal detail" not in resp.text
    assert "RuntimeError" not in resp.text
    assert "Traceback" not in resp.text

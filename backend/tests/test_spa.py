from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import create_app


@pytest.fixture
def spa_client(tmp_path: Path, db_session: object, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>LifeOS</title><div id=root>")
    (tmp_path / "assets" / "app.js").write_text("console.log('lifeos')")
    monkeypatch.setattr("app.main.settings.static_dir", str(tmp_path))

    app = create_app()

    def override_get_db() -> object:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_root_serves_the_spa_shell(spa_client: TestClient) -> None:
    resp = spa_client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "<div id=root>" in resp.text


def test_unknown_route_falls_back_to_the_shell(spa_client: TestClient) -> None:
    resp = spa_client.get("/calendar")
    assert resp.status_code == 200
    assert "<div id=root>" in resp.text


def test_real_asset_is_served(spa_client: TestClient) -> None:
    resp = spa_client.get("/assets/app.js")
    assert resp.status_code == 200
    assert "lifeos" in resp.text


def test_api_still_answers_json(spa_client: TestClient) -> None:
    resp = spa_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_html_gets_the_spa_csp_not_deny_all(spa_client: TestClient) -> None:
    csp = spa_client.get("/").headers["content-security-policy"]
    assert "script-src 'self'" in csp
    assert "fonts.googleapis.com" in csp
    assert "default-src 'none'" not in csp
    # the API keeps the strict policy
    assert spa_client.get("/api/health").headers["content-security-policy"].startswith(
        "default-src 'none'"
    )

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.redis import get_redis
from app.services.reports import load_report
from app.worker import tasks


@pytest.fixture
def captured_notifications(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    sent: list[dict[str, Any]] = []
    monkeypatch.setattr(
        tasks, "publish", lambda user_id, event: sent.append({"user_id": user_id, **event})
    )
    return sent


def _account(client: TestClient, headers: dict[str, str]) -> int:
    resp = client.post(
        "/api/finance/accounts",
        json={"name": "Checking", "starting_balance_cents": 0},
        headers=headers,
    )
    return int(resp.json()["id"])


# --------------------------------------------------------------------------- #
# generate_finance_report
# --------------------------------------------------------------------------- #
def test_report_task_renders_a_pdf_and_notifies(
    client: TestClient,
    auth_headers: dict[str, str],
    captured_notifications: list[dict[str, Any]],
) -> None:
    account_id = _account(client, auth_headers)
    client.post(
        "/api/finance/transactions",
        json={
            "account_id": account_id,
            "kind": "expense",
            "amount_cents": 4200,
            "occurred_on": "2026-08-09",
        },
        headers=auth_headers,
    )
    user_id = client.get("/api/auth/me", headers=auth_headers).json()["id"]

    tasks.generate_finance_report(user_id, "2026-08")

    pdf = load_report(get_redis(), user_id, "2026-08")
    assert pdf is not None and pdf.startswith(b"%PDF")
    assert captured_notifications[-1]["type"] == "notification"
    assert "2026-08" in captured_notifications[-1]["message"]


def test_report_endpoint_enqueues_then_serves_the_pdf(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _account(client, auth_headers)

    queued = client.post(
        "/api/finance/reports", json={"month": "2026-08"}, headers=auth_headers
    )
    assert queued.status_code == 202  # eager mode runs it before we get here

    got = client.get("/api/finance/reports/2026-08", headers=auth_headers)
    assert got.status_code == 200
    assert got.headers["content-type"] == "application/pdf"
    assert got.content.startswith(b"%PDF")

    missing = client.get("/api/finance/reports/2026-01", headers=auth_headers)
    assert missing.status_code == 404


# --------------------------------------------------------------------------- #
# dispatch_due_reminders
# --------------------------------------------------------------------------- #
def test_due_reminder_fires_once(
    client: TestClient,
    auth_headers: dict[str, str],
    captured_notifications: list[dict[str, Any]],
) -> None:
    start = (datetime.now(UTC) + timedelta(minutes=10)).replace(microsecond=0)
    event = client.post(
        "/api/calendar/events",
        json={
            "title": "Dentist",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(minutes=30)).isoformat(),
        },
        headers=auth_headers,
    ).json()
    client.post(
        f"/api/calendar/events/{event['id']}/reminders",
        json={"minutes_before": 10},
        headers=auth_headers,
    )

    assert tasks.dispatch_due_reminders() == {"fired": 1}
    assert captured_notifications[-1]["message"].startswith("Reminder: Dentist")

    # dedup key means a second sweep does nothing
    assert tasks.dispatch_due_reminders() == {"fired": 0}


def test_no_reminders_is_a_noop(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert tasks.dispatch_due_reminders() == {"fired": 0}


# --------------------------------------------------------------------------- #
# send_daily_digest
# --------------------------------------------------------------------------- #
def test_daily_digest_notifies_users_with_something_on(
    client: TestClient,
    auth_headers: dict[str, str],
    captured_notifications: list[dict[str, Any]],
) -> None:
    course = client.post(
        "/api/learning/courses", json={"title": "Spanish"}, headers=auth_headers
    ).json()
    client.post(
        f"/api/learning/courses/{course['id']}/flashcards",
        json={"front": "hola", "back": "hello"},
        headers=auth_headers,
    )

    result = tasks.send_daily_digest()
    assert result["sent"] >= 1
    assert any("flashcard" in n["message"] for n in captured_notifications)

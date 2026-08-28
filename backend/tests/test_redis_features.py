from __future__ import annotations

from collections.abc import Callable
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import Transaction, TransactionKind
from app.models.user import User

AuthHeaderFactory = Callable[..., dict[str, str]]


def _tokens(client: TestClient, email: str, password: str = "password123") -> dict[str, str]:
    client.post("/api/auth/register", json={"email": email, "password": password})
    return client.post(
        "/api/auth/login", data={"username": email, "password": password}
    ).json()


# --------------------------------------------------------------------------- #
# Token revocation
# --------------------------------------------------------------------------- #
def test_logout_revokes_the_access_token_immediately(client: TestClient) -> None:
    tokens = _tokens(client, "revoke@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    assert client.get("/api/auth/me", headers=headers).status_code == 200

    out = client.post(
        "/api/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert out.status_code == 204

    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_logout_also_kills_the_refresh_token(client: TestClient) -> None:
    tokens = _tokens(client, "revoke2@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    client.post(
        "/api/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    resp = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


def test_logout_all_invalidates_every_existing_token(client: TestClient) -> None:
    first = _tokens(client, "everywhere@example.com")
    second = client.post(
        "/api/auth/login",
        data={"username": "everywhere@example.com", "password": "password123"},
    ).json()

    client.post(
        "/api/auth/logout-all",
        json={"refresh_token": first["refresh_token"]},
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )

    for tokens in (first, second):
        me = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me.status_code == 401


# --------------------------------------------------------------------------- #
# Rate limiting
# --------------------------------------------------------------------------- #
def test_login_is_rate_limited(client: TestClient) -> None:
    client.post("/api/auth/register", json={"email": "rl@example.com", "password": "password123"})

    statuses = [
        client.post(
            "/api/auth/login",
            data={"username": "rl@example.com", "password": "wrong"},
        ).status_code
        for _ in range(12)
    ]

    assert statuses[:10] == [401] * 10  # first ten attempts hit the endpoint
    assert 429 in statuses[10:]


def test_register_is_rate_limited(client: TestClient) -> None:
    statuses = [
        client.post(
            "/api/auth/register",
            json={"email": f"burst{i}@example.com", "password": "password123"},
        ).status_code
        for i in range(7)
    ]
    assert statuses.count(429) >= 1


# --------------------------------------------------------------------------- #
# Response caching
# --------------------------------------------------------------------------- #
def test_summary_is_cached_until_a_mutation_busts_it(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    owner = db_session.scalars(
        select(User).where(User.email == "owner@example.com")
    ).one()
    account = client.post(
        "/api/finance/accounts",
        json={"name": "Checking", "starting_balance_cents": 0},
        headers=auth_headers,
    ).json()

    def spend_via_api(cents: int) -> None:
        resp = client.post(
            "/api/finance/transactions",
            json={
                "account_id": account["id"],
                "kind": "expense",
                "amount_cents": cents,
                "occurred_on": "2026-08-10",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

    spend_via_api(1000)
    first = client.get("/api/finance/summary?month=2026-08", headers=auth_headers).json()
    assert first["expense_cents"] == 1000  # computed and now cached

    # Write straight to the DB: the mutation middleware never sees it, so the
    # cache version isn't bumped and the stale value must still be served.
    db_session.add(
        Transaction(
            user_id=owner.id,
            account_id=account["id"],
            kind=TransactionKind.EXPENSE,
            amount_cents=999_999,
            occurred_on=date(2026, 8, 11),
        )
    )
    db_session.commit()

    still_cached = client.get(
        "/api/finance/summary?month=2026-08", headers=auth_headers
    ).json()
    assert still_cached["expense_cents"] == 1000

    spend_via_api(500)  # a real API mutation bumps the cache version
    fresh = client.get("/api/finance/summary?month=2026-08", headers=auth_headers).json()
    assert fresh["expense_cents"] == 1000 + 999_999 + 500

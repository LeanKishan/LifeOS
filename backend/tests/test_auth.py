from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

REGISTER = "/api/auth/register"
LOGIN = "/api/auth/login"
REFRESH = "/api/auth/refresh"
ME = "/api/auth/me"

EMAIL = "ada@example.com"
PASSWORD = "correct horse battery"


def register(client: TestClient, **overrides: object) -> httpx.Response:
    payload: dict[str, object] = {
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": "Ada Lovelace",
    }
    payload.update(overrides)
    return client.post(REGISTER, json=payload)


def login(client: TestClient, email: str = EMAIL, password: str = PASSWORD) -> httpx.Response:
    return client.post(LOGIN, data={"username": email, "password": password})


def test_register_returns_public_user_only(client: TestClient) -> None:
    resp = register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == EMAIL
    assert body["full_name"] == "Ada Lovelace"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_short_password(client: TestClient) -> None:
    assert register(client, password="short").status_code == 422


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    assert register(client).status_code == 201
    assert register(client).status_code == 409


def test_login_returns_token_pair(client: TestClient) -> None:
    register(client)
    resp = login(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_wrong_password_is_401(client: TestClient) -> None:
    register(client)
    assert login(client, password="nope").status_code == 401


def test_me_requires_a_token(client: TestClient) -> None:
    assert client.get(ME).status_code == 401


def test_me_returns_current_user(client: TestClient) -> None:
    register(client)
    token = login(client).json()["access_token"]
    resp = client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == EMAIL


def test_refresh_token_is_not_accepted_as_access(client: TestClient) -> None:
    register(client)
    refresh_token = login(client).json()["refresh_token"]
    resp = client.get(ME, headers={"Authorization": f"Bearer {refresh_token}"})
    assert resp.status_code == 401


def test_refresh_issues_a_working_access_token(client: TestClient) -> None:
    register(client)
    refresh_token = login(client).json()["refresh_token"]
    resp = client.post(REFRESH, json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_access = resp.json()["access_token"]
    assert client.get(ME, headers={"Authorization": f"Bearer {new_access}"}).status_code == 200


def test_access_token_is_not_accepted_as_refresh(client: TestClient) -> None:
    register(client)
    access_token = login(client).json()["access_token"]
    assert client.post(REFRESH, json={"refresh_token": access_token}).status_code == 401


def test_garbage_token_is_401(client: TestClient) -> None:
    resp = client.get(ME, headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 401

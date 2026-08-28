from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.realtime.manager import ConnectionManager


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def accept(self) -> None:  # pragma: no cover - trivial
        pass

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)


# --------------------------------------------------------------------------- #
# ConnectionManager fan-out
# --------------------------------------------------------------------------- #
async def test_send_reaches_only_the_target_users_sockets() -> None:
    manager = ConnectionManager()
    alice_1, alice_2, bob_1 = FakeSocket(), FakeSocket(), FakeSocket()
    await manager.connect(1, alice_1)
    await manager.connect(1, alice_2)
    await manager.connect(2, bob_1)

    await manager.send_to_user(1, {"type": "projects"})

    assert alice_1.sent == [{"type": "projects"}]
    assert alice_2.sent == [{"type": "projects"}]
    assert bob_1.sent == []


async def test_disconnect_drops_the_socket() -> None:
    manager = ConnectionManager()
    socket = FakeSocket()
    await manager.connect(7, socket)
    assert manager.connection_count(7) == 1

    manager.disconnect(7, socket)
    assert manager.connection_count(7) == 0
    await manager.send_to_user(7, {"type": "x"})  # nothing to send, must not raise


# --------------------------------------------------------------------------- #
# WebSocket endpoint auth
# --------------------------------------------------------------------------- #
def test_ws_rejects_missing_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/api/ws"):
        pass


def test_ws_rejects_garbage_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/api/ws?token=x"):
        pass


def test_ws_accepts_a_valid_token_and_greets(
    client: TestClient, make_auth_headers
) -> None:
    headers = make_auth_headers("live@example.com")
    token = headers["Authorization"].removeprefix("Bearer ")
    with client.websocket_connect(f"/api/ws?token={token}") as websocket:
        assert websocket.receive_json() == {"type": "connected"}


def test_mutation_pushes_a_live_update(client: TestClient, make_auth_headers) -> None:
    headers = make_auth_headers("live@example.com")
    token = headers["Authorization"].removeprefix("Bearer ")

    with client.websocket_connect(f"/api/ws?token={token}") as websocket:
        assert websocket.receive_json() == {"type": "connected"}

        resp = client.post(
            "/api/job-tracker/applications",
            json={"company_name": "Globex", "role": "SWE"},
            headers=headers,
        )
        assert resp.status_code == 201

        assert websocket.receive_json() == {"type": "job-tracker"}

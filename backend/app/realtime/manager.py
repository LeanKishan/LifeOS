from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Protocol


class _Sendable(Protocol):
    async def accept(self) -> None: ...
    async def send_json(self, data: Any) -> None: ...


class ConnectionManager:
    """Tracks live WebSocket connections per user, in this process only.

    Multi-worker deployments need a Redis pub/sub fan-out in front of this
    (see ADR-0017); the interface here stays the same.
    """

    def __init__(self) -> None:
        self._by_user: dict[int, set[_Sendable]] = {}
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, user_id: int, websocket: _Sendable) -> None:
        await websocket.accept()
        self.loop = asyncio.get_running_loop()
        self._by_user.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: _Sendable) -> None:
        sockets = self._by_user.get(user_id)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            self._by_user.pop(user_id, None)

    def connection_count(self, user_id: int) -> int:
        return len(self._by_user.get(user_id, ()))

    async def send_to_user(self, user_id: int, event: dict[str, Any]) -> None:
        for websocket in list(self._by_user.get(user_id, ())):
            try:
                await websocket.send_json(event)
            except Exception:  # noqa: BLE001 - a failed send means the socket is gone
                self.disconnect(user_id, websocket)


manager = ConnectionManager()


def publish(user_id: int, event: dict[str, Any]) -> None:
    """Fan an event out to a user's sockets from synchronous code.

    Request handlers run in a threadpool, so this hops back onto the server's
    event loop. A no-op when no WebSocket server is running (e.g. plain tests).
    """
    loop = manager.loop
    if loop is None or loop.is_closed():
        return
    with contextlib.suppress(RuntimeError):
        asyncio.run_coroutine_threadsafe(manager.send_to_user(user_id, event), loop)

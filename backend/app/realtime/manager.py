from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any, Protocol

from app.core.redis import get_redis

LIVE_CHANNEL = "lifeos:live"


class _Sendable(Protocol):
    async def accept(self) -> None: ...
    async def send_json(self, data: Any) -> None: ...


class ConnectionManager:
    """Tracks live WebSocket connections for *this* process."""

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
    """Deliver an event to a user's sockets on this process, and mirror it onto a
    Redis channel.

    The direct call is what actually reaches browsers with a single worker (dev,
    and one uvicorn process). The Redis publish is the seam a standalone
    subscriber process would consume to fan out across workers in a real
    multi-process deployment; nothing in this repo consumes it yet (ADR-0017).
    """
    loop = manager.loop
    if loop is not None and not loop.is_closed():
        with contextlib.suppress(RuntimeError):
            asyncio.run_coroutine_threadsafe(manager.send_to_user(user_id, event), loop)

    with contextlib.suppress(Exception):
        get_redis().publish(LIVE_CHANNEL, json.dumps({"user_id": user_id, "event": event}))

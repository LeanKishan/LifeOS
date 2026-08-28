"""Cross-process delivery of live-update frames.

With more than one API process (the ECS deployment runs several), a mutation
handled by process A must still refresh a browser connected to process B.
`publish()` mirrors every frame onto a Redis channel; this subscriber runs in
each process and delivers the frames that came from *other* processes.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.realtime.manager import LIVE_CHANNEL, ConnectionManager

logger = logging.getLogger("lifeos.fanout")


def _should_deliver(frame: dict[str, Any], origin: str) -> bool:
    return (
        frame.get("user_id") is not None
        and frame.get("event") is not None
        and frame.get("origin") != origin  # our own frames were delivered in-process
    )


async def run_fanout(manager: ConnectionManager) -> None:
    settings = get_settings()
    client: aioredis.Redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(LIVE_CHANNEL)
    logger.info("ws fan-out subscriber started", extra={"origin": manager.origin})
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                frame = json.loads(message["data"])
            except (ValueError, TypeError, KeyError):
                continue
            if not _should_deliver(frame, manager.origin):
                continue
            with contextlib.suppress(Exception):
                await manager.send_to_user(int(frame["user_id"]), frame["event"])
    except asyncio.CancelledError:
        raise
    finally:
        with contextlib.suppress(Exception):
            await pubsub.aclose()  # type: ignore[no-untyped-call]
        with contextlib.suppress(Exception):
            await client.aclose()

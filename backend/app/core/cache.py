from __future__ import annotations

import json
from typing import Any

import redis


def cache_version(client: redis.Redis, channel: str, user_id: int) -> int:
    raw = client.get(f"cachever:{channel}:{user_id}")
    return int(raw) if raw is not None else 0


def bump_cache_version(client: redis.Redis, channel: str, user_id: int) -> None:
    client.incr(f"cachever:{channel}:{user_id}")


def cached_json(client: redis.Redis, key: str) -> Any | None:
    raw = client.get(key)
    return json.loads(raw) if raw is not None else None


def store_json(client: redis.Redis, key: str, value: Any, ttl_seconds: int) -> None:
    client.set(key, json.dumps(value, default=str), ex=ttl_seconds)

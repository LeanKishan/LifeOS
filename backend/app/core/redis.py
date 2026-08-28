from __future__ import annotations

from functools import lru_cache
from typing import cast

import fakeredis
import redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> redis.Redis:
    """One process-wide client. `fakeredis://` (the dev default) gets an
    in-memory server; anything else is a real Redis URL (CI, Compose, prod).
    """
    url = get_settings().redis_url
    if url.startswith("fakeredis"):
        return cast("redis.Redis", fakeredis.FakeStrictRedis(decode_responses=True))
    return redis.Redis.from_url(url, decode_responses=True)

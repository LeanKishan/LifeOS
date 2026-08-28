from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis


def _over_limit_retry_after(key: str, limit: int, window_seconds: int) -> int:
    """Fixed-window counter. Returns seconds to wait if over the limit, else 0.

    Fixed windows can allow a 2x burst at a boundary; a sliding window (sorted
    set of timestamps) is the stricter option if abuse gets clever.
    """
    client = get_redis()
    bucket = int(time.time()) // window_seconds
    redis_key = f"rl:{key}:{bucket}"
    count = client.incr(redis_key)
    if count == 1:
        client.expire(redis_key, window_seconds)
    if count > limit:
        return max(int(client.ttl(redis_key) or 1), 1)
    return 0


def rate_limited(
    bucket: str, *, limit: int, window_seconds: int
) -> Callable[[Request], None]:
    """A dependency that 429s the caller's IP after `limit` hits per window."""

    def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        retry_after = _over_limit_retry_after(
            f"{bucket}:{client_host}", limit, window_seconds
        )
        if retry_after:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency

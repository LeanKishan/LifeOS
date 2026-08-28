from __future__ import annotations

from datetime import UTC, datetime

import redis

_DENYLIST = "denylist:"
_GENERATION = "tokgen:"


def _ttl_until(exp: int) -> int:
    return max(exp - int(datetime.now(UTC).timestamp()), 1)


# --- single-token revocation (used by /auth/logout) ------------------------- #
def revoke_token(client: redis.Redis, jti: str, exp: int) -> None:
    """Deny one token by id until it would have expired anyway."""
    client.set(f"{_DENYLIST}{jti}", "1", ex=_ttl_until(exp))


def is_token_revoked(client: redis.Redis, jti: str) -> bool:
    return bool(client.exists(f"{_DENYLIST}{jti}"))


# --- bulk revocation via a generation counter (used by /auth/logout-all) ---- #
def token_generation(client: redis.Redis, user_id: int) -> int:
    """The current token generation for a user. Tokens carry the generation they
    were minted under; anything older is rejected.
    """
    raw = client.get(f"{_GENERATION}{user_id}")
    return int(raw) if raw is not None else 0


def bump_token_generation(client: redis.Redis, user_id: int) -> None:
    client.incr(f"{_GENERATION}{user_id}")

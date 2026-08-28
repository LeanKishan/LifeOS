from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()
_password_hash = PasswordHash.recommended()

TokenType = Literal["access", "refresh"]


def hash_password(plain: str) -> str:
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _password_hash.verify(plain, hashed)


def _create_token(
    subject: str, token_type: TokenType, expires_delta: timedelta, generation: int
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": uuid4().hex,
        "gen": generation,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, *, generation: int = 0) -> str:
    delta = timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(subject, "access", delta, generation)


def create_refresh_token(subject: str, *, generation: int = 0) -> str:
    delta = timedelta(days=settings.refresh_token_expire_days)
    return _create_token(subject, "refresh", delta, generation)


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    payload: dict[str, Any] = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected a {expected_type} token")
    return payload

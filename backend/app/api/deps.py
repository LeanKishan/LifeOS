"""Shared FastAPI dependencies: DB session, Redis, and the current user."""

from __future__ import annotations

from typing import Annotated, Any

import jwt
import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.user import User
from app.services import users as user_service
from app.services.tokens import is_token_revoked, token_generation

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

DbSession = Annotated[Session, Depends(get_db)]
RedisDep = Annotated["redis.Redis", Depends(get_redis)]

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_token_payload(
    token: Annotated[str, Depends(oauth2_scheme)],
    client: RedisDep,
) -> dict[str, Any]:
    """Decode the access token and reject it if it's been revoked."""
    try:
        payload = decode_token(token, "access")
    except jwt.PyJWTError as exc:
        raise _credentials_exc from exc

    jti = payload.get("jti")
    if isinstance(jti, str) and is_token_revoked(client, jti):
        raise _credentials_exc

    sub = payload.get("sub")
    if (
        isinstance(sub, str)
        and sub.isdigit()
        and int(payload.get("gen", 0)) < token_generation(client, int(sub))
    ):
        raise _credentials_exc

    return payload


TokenPayload = Annotated[dict[str, Any], Depends(get_token_payload)]


def get_current_user(payload: TokenPayload, db: DbSession) -> User:
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.isdigit():
        raise _credentials_exc

    user = user_service.get_by_id(db, int(sub))
    if user is None:
        raise _credentials_exc
    return user


def get_current_active_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_active_user)]

__all__ = [
    "CurrentUser",
    "DbSession",
    "RedisDep",
    "TokenPayload",
    "get_current_active_user",
    "get_current_user",
    "get_db",
    "get_token_payload",
]

"""Shared FastAPI dependencies: DB session and the current authenticated user."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User
from app.services import users as user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

DbSession = Annotated[Session, Depends(get_db)]

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    try:
        payload = decode_token(token, "access")
    except jwt.PyJWTError as exc:
        raise _credentials_exc from exc

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

__all__ = ["CurrentUser", "DbSession", "get_current_active_user", "get_current_user", "get_db"]

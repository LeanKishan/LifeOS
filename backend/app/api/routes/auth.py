from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.user import RefreshRequest, Token, UserCreate, UserRead
from app.services import users as user_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user_id: int) -> Token:
    subject = str(user_id)
    return Token(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession) -> UserRead:
    if user_service.get_by_email(db, str(data.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists",
        )
    user = user_service.create_user(db, data)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    user = user_service.authenticate(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_tokens(user.id)


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: DbSession) -> Token:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(data.refresh_token, "refresh")
    except jwt.PyJWTError as exc:
        raise invalid from exc

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.isdigit():
        raise invalid

    user = user_service.get_by_id(db, int(sub))
    if user is None or not user.is_active:
        raise invalid
    return _issue_tokens(user.id)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)

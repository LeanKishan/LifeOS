from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession, RedisDep, TokenPayload
from app.core.ratelimit import rate_limited
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.user import RefreshRequest, Token, UserCreate, UserRead, UserUpdate
from app.services import users as user_service
from app.services.tokens import (
    bump_token_generation,
    is_token_revoked,
    revoke_token,
    token_generation,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_login_limit = rate_limited("auth-login", limit=10, window_seconds=60)
_register_limit = rate_limited("auth-register", limit=5, window_seconds=60)


def _issue_tokens(user_id: int, client: RedisDep) -> Token:
    subject = str(user_id)
    generation = token_generation(client, user_id)
    return Token(
        access_token=create_access_token(subject, generation=generation),
        refresh_token=create_refresh_token(subject, generation=generation),
    )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_register_limit)],
)
def register(data: UserCreate, db: DbSession) -> UserRead:
    if user_service.get_by_email(db, str(data.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists",
        )
    user = user_service.create_user(db, data)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token, dependencies=[Depends(_login_limit)])
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
    client: RedisDep,
) -> Token:
    user = user_service.authenticate(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_tokens(user.id, client)


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: DbSession, client: RedisDep) -> Token:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(data.refresh_token, "refresh")
    except jwt.PyJWTError as exc:
        raise invalid from exc

    jti = payload.get("jti")
    if isinstance(jti, str) and is_token_revoked(client, jti):
        raise invalid

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.isdigit():
        raise invalid
    if int(payload.get("gen", 0)) < token_generation(client, int(sub)):
        raise invalid

    user = user_service.get_by_id(db, int(sub))
    if user is None or not user.is_active:
        raise invalid
    return _issue_tokens(user.id, client)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, payload: TokenPayload, client: RedisDep) -> None:
    """Revoke the presented access token and its refresh token immediately."""
    revoke_token(client, payload["jti"], int(payload["exp"]))
    try:
        refresh_payload = decode_token(data.refresh_token, "refresh")
        revoke_token(client, refresh_payload["jti"], int(refresh_payload["exp"]))
    except jwt.PyJWTError:
        pass  # already unusable, nothing to revoke


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(payload: TokenPayload, client: RedisDep) -> None:
    """Invalidate every token issued to this user so far ("sign out everywhere")."""
    bump_token_generation(client, int(payload["sub"]))


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
def update_me(data: UserUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    try:
        updated = user_service.update_user(db, user, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return UserRead.model_validate(updated)

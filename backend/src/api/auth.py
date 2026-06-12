"""FastAPI router for account login and current-user lookup."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from decimal import Decimal
from typing import Any
from uuid import UUID

import jwt
import psycopg2
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, field_validator

from src.security.auth import (
    AuthConfigurationError,
    access_token_expires_in_seconds,
    create_access_token,
    decode_access_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value:
            raise ValueError("Email is not valid.")
        return value


class UserPublic(BaseModel):
    id: UUID
    full_name: str
    email: str
    avatar_url: str | None = None
    travel_preferences: dict[str, Any] = Field(default_factory=dict)
    total_points: int = 0
    level: str = "Explorer"


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


def _connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "travel_buddy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", ""),
        cursor_factory=RealDictCursor,
    )


@contextmanager
def _database_connection():
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def _clean(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean(item) for item in value]
    return value


def _get_user_by_email(email: str) -> dict[str, Any] | None:
    with _database_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name, email, password_hash, avatar_url,
                       travel_preferences, total_points, level
                FROM users
                WHERE lower(email) = lower(%s)
                LIMIT 1
                """,
                (email,),
            )
            row = cur.fetchone()
            return _clean(dict(row)) if row else None


def _get_user_by_id(user_id: str) -> dict[str, Any] | None:
    with _database_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name, email, avatar_url,
                       travel_preferences, total_points, level
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            return _clean(dict(row)) if row else None


def _update_password_hash(user_id: str, password_hash: str) -> None:
    with _database_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
                (password_hash, user_id),
            )


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email hoặc mật khẩu không đúng.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPublic:
    if not credentials:
        raise _invalid_credentials()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = str(payload["sub"])
        user = _get_user_by_id(user_id)
    except (AuthConfigurationError, jwt.PyJWTError) as exc:
        logger.warning("Invalid access token: %s", exc)
        raise _invalid_credentials() from exc
    except psycopg2.Error as exc:
        logger.exception("Database error while loading current user")
        raise HTTPException(status_code=503, detail="Auth database unavailable.") from exc

    if not user:
        raise _invalid_credentials()
    return UserPublic.model_validate(user)


@router.post("/login", response_model=LoginResponse, summary="Đăng nhập")
def login(body: LoginRequest):
    try:
        user = _get_user_by_email(body.email)
    except psycopg2.Error as exc:
        logger.exception("Database error during login")
        raise HTTPException(status_code=503, detail="Auth database unavailable.") from exc

    if not user or not verify_password(body.password, user.get("password_hash")):
        raise _invalid_credentials()

    try:
        token = create_access_token(str(user["id"]), user["email"])
    except AuthConfigurationError as exc:
        logger.error("Auth configuration error: %s", exc)
        raise HTTPException(status_code=500, detail="Auth service is not configured.") from exc

    if password_needs_rehash(user["password_hash"]):
        try:
            _update_password_hash(str(user["id"]), hash_password(body.password))
        except psycopg2.Error:
            logger.warning("Could not update password hash for user %s", user["id"], exc_info=True)

    return LoginResponse(
        access_token=token,
        expires_in=access_token_expires_in_seconds(),
        user=UserPublic.model_validate(user),
    )


@router.get("/me", response_model=UserPublic, summary="Thông tin tài khoản hiện tại")
async def me(current_user: UserPublic = Depends(get_current_user)):
    return current_user

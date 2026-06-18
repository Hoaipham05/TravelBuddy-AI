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


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPublic | None:
    """Như get_current_user nhưng KHÔNG raise khi thiếu/lỗi token — trả None.
    Dùng cho endpoint công khai muốn cá nhân hoá nếu có đăng nhập (vd: nút Hữu ích
    vẫn chạy ẩn danh, nhưng nếu đăng nhập thì tạo thông báo cho tác giả)."""
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user = _get_user_by_id(str(payload["sub"]))
        return UserPublic.model_validate(user) if user else None
    except Exception:  # noqa: BLE001 — token hỏng/hết hạn → coi như ẩn danh
        return None


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


# ─────────────────────────────────────────────────────────────────────────────
#  Đăng nhập bằng Google (OAuth 2.0 — Google Identity Services)
# ─────────────────────────────────────────────────────────────────────────────

def _google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


@router.get("/config", summary="Cấu hình công khai cho trang đăng nhập")
def auth_config():
    """Frontend gọi để biết có bật đăng nhập Google không và lấy client_id để init GIS."""
    return {"google_client_id": _google_client_id() or None}


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., min_length=10)  # ID token (JWT) từ Google Identity Services


def _upsert_google_user(sub: str, email: str, full_name: str, avatar_url: str | None) -> dict[str, Any]:
    """Tìm user theo google_sub → email; tạo mới nếu chưa có; liên kết nếu trùng email."""
    with _database_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name, email, avatar_url, travel_preferences, total_points, level
                FROM users WHERE google_sub = %s LIMIT 1
                """,
                (sub,),
            )
            row = cur.fetchone()
            if row:
                return _clean(dict(row))

            # Chưa liên kết google_sub — thử khớp theo email (tài khoản đã tạo trước đó)
            cur.execute(
                """
                UPDATE users
                   SET google_sub = %s,
                       avatar_url = COALESCE(avatar_url, %s),
                       updated_at = NOW()
                 WHERE lower(email) = lower(%s)
             RETURNING id, full_name, email, avatar_url, travel_preferences, total_points, level
                """,
                (sub, avatar_url, email),
            )
            row = cur.fetchone()
            if row:
                conn.commit()
                return _clean(dict(row))

            # Tạo tài khoản mới (không mật khẩu — chỉ đăng nhập qua Google)
            cur.execute(
                """
                INSERT INTO users (full_name, email, google_sub, avatar_url)
                VALUES (%s, %s, %s, %s)
             RETURNING id, full_name, email, avatar_url, travel_preferences, total_points, level
                """,
                (full_name or email.split("@")[0], email, sub, avatar_url),
            )
            row = cur.fetchone()
            conn.commit()
            return _clean(dict(row))


@router.post("/google", response_model=LoginResponse, summary="Đăng nhập bằng Google")
def google_login(body: GoogleLoginRequest):
    client_id = _google_client_id()
    if not client_id:
        raise HTTPException(status_code=503, detail="Đăng nhập Google chưa được cấu hình trên máy chủ.")

    # Verify id_token với Google (kiểm tra chữ ký + audience = client_id của ta)
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        claims = google_id_token.verify_oauth2_token(
            body.credential, google_requests.Request(), client_id
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google token verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Token Google không hợp lệ.") from exc

    if not claims.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Email Google chưa được xác thực.")

    sub = str(claims["sub"])
    email = (claims.get("email") or "").strip().lower()
    full_name = claims.get("name") or ""
    avatar_url = claims.get("picture")

    try:
        user = _upsert_google_user(sub, email, full_name, avatar_url)
        token = create_access_token(str(user["id"]), user["email"])
    except AuthConfigurationError as exc:
        raise HTTPException(status_code=500, detail="Auth service is not configured.") from exc
    except psycopg2.Error as exc:
        logger.exception("Database error during Google login")
        raise HTTPException(status_code=503, detail="Auth database unavailable.") from exc

    return LoginResponse(
        access_token=token,
        expires_in=access_token_expires_in_seconds(),
        user=UserPublic.model_validate(user),
    )

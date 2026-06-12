"""Authentication helpers for TravelBuddy accounts."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


JWT_ALGORITHM = "HS256"
JWT_ISSUER = "travelbuddy-api"
JWT_AUDIENCE = "travelbuddy-frontend"

_password_hasher = PasswordHasher()


class AuthConfigurationError(RuntimeError):
    """Raised when auth cannot run safely with the current environment."""


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return _password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except (InvalidHashError, VerificationError):
        return True


def access_token_lifetime_minutes() -> int:
    raw_value = os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60")
    try:
        return max(1, int(raw_value))
    except ValueError:
        return 60


def access_token_expires_in_seconds() -> int:
    return access_token_lifetime_minutes() * 60


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if len(secret) < 32:
        raise AuthConfigurationError(
            "JWT_SECRET_KEY must be set to a random value of at least 32 characters."
        )
    return secret


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=access_token_lifetime_minutes())
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        _jwt_secret(),
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={"require": ["sub", "exp", "iat", "iss", "aud"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type.")
    return payload

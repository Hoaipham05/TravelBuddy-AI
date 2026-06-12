from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import jwt

from src.security.auth import (
    AuthConfigurationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class PasswordTests(unittest.TestCase):
    def test_password_hash_round_trip(self):
        password_hash = hash_password("StrongDemoPassword@2026")

        self.assertNotIn("StrongDemoPassword@2026", password_hash)
        self.assertTrue(verify_password("StrongDemoPassword@2026", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_short_password_is_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("short")


class TokenTests(unittest.TestCase):
    def test_access_token_round_trip(self):
        env = {
            "JWT_SECRET_KEY": "test-secret-that-is-longer-than-32-characters",
            "JWT_ACCESS_TOKEN_MINUTES": "15",
        }
        with patch.dict(os.environ, env, clear=False):
            token = create_access_token("user-123", "demo@travelbuddy.local")
            payload = decode_access_token(token)

        self.assertEqual(payload["sub"], "user-123")
        self.assertEqual(payload["email"], "demo@travelbuddy.local")
        self.assertEqual(payload["type"], "access")

    def test_short_jwt_secret_is_rejected(self):
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "too-short"}, clear=False):
            with self.assertRaises(AuthConfigurationError):
                create_access_token("user-123", "demo@travelbuddy.local")

    def test_tampered_token_is_rejected(self):
        env = {"JWT_SECRET_KEY": "test-secret-that-is-longer-than-32-characters"}
        with patch.dict(os.environ, env, clear=False):
            token = create_access_token("user-123", "demo@travelbuddy.local")
            tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
            with self.assertRaises(jwt.PyJWTError):
                decode_access_token(tampered)


if __name__ == "__main__":
    unittest.main()

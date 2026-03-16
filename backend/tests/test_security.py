"""Unit tests for app.core.security — no DB or HTTP needed."""
import logging
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify_roundtrip(self):
        password = "myS3cureP@ss"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False


class TestAccessToken:
    def test_access_token_has_type_access(self):
        token = create_access_token({"sub": "user-123"})
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert payload["type"] == "access"
        assert payload["sub"] == "user-123"
        assert "exp" in payload


class TestRefreshToken:
    def test_refresh_token_has_type_and_jti(self):
        token = create_refresh_token({"sub": "user-456"})
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert payload["type"] == "refresh"
        assert payload["sub"] == "user-456"
        assert "jti" in payload
        # jti must be a valid UUID string
        import uuid
        uuid.UUID(payload["jti"])  # raises if invalid


class TestDecodeToken:
    def test_expired_token_returns_none(self):
        payload = {
            "sub": "user-789",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        assert decode_token(token) is None

    def test_wrong_secret_returns_none_and_logs(self, caplog):
        payload = {
            "sub": "user-789",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong-secret", algorithm=settings.jwt_algorithm)
        with caplog.at_level(logging.WARNING, logger="app.core.security"):
            result = decode_token(token)
        assert result is None
        assert "JWT decode failed" in caplog.text

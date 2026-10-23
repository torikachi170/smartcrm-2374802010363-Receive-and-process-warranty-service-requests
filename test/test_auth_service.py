from datetime import datetime, timedelta, timezone

import pytest

from src.business.auth_service import (
    AuthService,
    InvalidAccessToken,
    InvalidCredentials,
)


def make_auth_service() -> AuthService:
    return AuthService("demo", "demo-password", "test-secret-key-that-is-at-least-32-chars")


def test_login_returns_token_with_expected_subject() -> None:
    service = make_auth_service()

    token = service.login("demo", "demo-password")
    claims = service.verify_access_token(token)

    assert claims["sub"] == "demo"
    assert claims["exp"] > claims["iat"]


def test_login_rejects_invalid_credentials() -> None:
    with pytest.raises(InvalidCredentials):
        make_auth_service().login("demo", "wrong-password")


def test_access_token_rejects_expired_token() -> None:
    service = make_auth_service()
    now = datetime.now(timezone.utc)
    token = __import__("jwt").encode(
        {"sub": "demo", "iat": now - timedelta(minutes=2), "exp": now - timedelta(minutes=1)},
        "test-secret-key-that-is-at-least-32-chars",
        algorithm="HS256",
    )

    with pytest.raises(InvalidAccessToken):
        service.verify_access_token(token)
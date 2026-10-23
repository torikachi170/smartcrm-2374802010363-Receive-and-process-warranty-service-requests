from datetime import datetime, timedelta, timezone
import os
from secrets import compare_digest

import jwt
from dotenv import load_dotenv


class InvalidCredentials(Exception):
    pass


class InvalidAccessToken(Exception):
    pass


class AuthService:
    def __init__(
        self,
        username: str,
        password: str,
        secret_key: str,
        token_lifetime_minutes: int = 30,
    ) -> None:
        if not username or not password or len(secret_key) < 32:
            raise ValueError("Authentication settings are incomplete or insecure")
        if token_lifetime_minutes <= 0:
            raise ValueError("Token lifetime must be positive")

        self._username = username
        self._password = password
        self._secret_key = secret_key
        self._token_lifetime_minutes = token_lifetime_minutes

    @property
    def token_lifetime_seconds(self) -> int:
        return self._token_lifetime_minutes * 60

    def login(self, username: str, password: str) -> str:
        username_matches = compare_digest(
            username.encode("utf-8"), self._username.encode("utf-8")
        )
        password_matches = compare_digest(
            password.encode("utf-8"), self._password.encode("utf-8")
        )
        if not username_matches or not password_matches:
            raise InvalidCredentials

        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": self._username,
                "iat": now,
                "exp": now + timedelta(minutes=self._token_lifetime_minutes),
            },
            self._secret_key,
            algorithm="HS256",
        )

    def verify_access_token(self, token: str) -> dict[str, object]:
        try:
            claims = jwt.decode(
                token,
                self._secret_key,
                algorithms=["HS256"],
                options={"require": ["sub", "iat", "exp"]},
            )
        except jwt.PyJWTError as error:
            raise InvalidAccessToken from error

        if not isinstance(claims.get("sub"), str):
            raise InvalidAccessToken
        return claims


def auth_service_from_environment() -> AuthService | None:
    load_dotenv()
    username = os.getenv("DEMO_USERNAME")
    password = os.getenv("DEMO_PASSWORD")
    secret_key = os.getenv("JWT_SECRET_KEY")
    lifetime = os.getenv("JWT_ACCESS_TOKEN_MINUTES", "30")

    if not username or not password or not secret_key:
        return None

    try:
        return AuthService(username, password, secret_key, int(lifetime))
    except ValueError:
        return None
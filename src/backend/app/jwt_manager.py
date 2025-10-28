"""JWT token utilities for authentication and authorization."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TokenData:
    """Token payload data."""

    def __init__(
        self,
        user_id: str,
        session_id: str,
        token_type: str = "access",
        scopes: Optional[list[str]] = None,
        **extra: Any,
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.token_type = token_type
        self.scopes = scopes or []
        self.extra = extra

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JWT encoding."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "token_type": self.token_type,
            "scopes": self.scopes,
            **self.extra,
        }


class JWTManager:
    """Manage JWT token creation and validation."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        token_data: TokenData,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a new access token."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload = token_data.to_dict()
        payload.update(
            {
                "iat": now,
                "exp": expire,
                "jti": self._generate_jti(),
            }
        )

        try:
            encoded = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Access token created for user {token_data.user_id}")
            return encoded
        except Exception as e:
            logger.error(f"Error encoding JWT: {e}")
            raise

    def create_refresh_token(
        self,
        token_data: TokenData,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a new refresh token."""
        if expires_delta is None:
            expires_delta = timedelta(days=settings.refresh_token_expire_days)

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload = token_data.to_dict()
        payload.update(
            {
                "token_type": "refresh",
                "iat": now,
                "exp": expire,
                "jti": self._generate_jti(),
            }
        )

        try:
            encoded = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Refresh token created for user {token_data.user_id}")
            return encoded
        except Exception as e:
            logger.error(f"Error encoding JWT: {e}")
            raise

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except ExpiredSignatureError:
            logger.warning("Token expired")
            raise
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise

    def extract_user_id(self, token: str) -> Optional[str]:
        """Extract user_id from token without verification (for logging)."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": False},
            )
            return payload.get("user_id")
        except Exception:
            return None

    @staticmethod
    def _generate_jti() -> str:
        """Generate a unique JWT ID."""
        return secrets.token_urlsafe(32)


def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance."""
    return JWTManager(settings.jwt_secret_key, settings.jwt_algorithm)

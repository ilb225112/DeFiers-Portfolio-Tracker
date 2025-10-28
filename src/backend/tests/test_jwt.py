"""Tests for JWT and token utilities."""

import pytest
from datetime import timedelta
from jwt.exceptions import ExpiredSignatureError

from app.jwt_manager import JWTManager, TokenData


def test_jwt_token_creation():
    """Test JWT token creation and verification."""
    manager = JWTManager(secret_key="test-secret-key", algorithm="HS256")

    token_data = TokenData(user_id="user123", session_id="session456")
    token = manager.create_access_token(token_data)

    assert token is not None
    assert isinstance(token, str)

    # Verify the token
    payload = manager.verify_token(token)
    assert payload["user_id"] == "user123"
    assert payload["session_id"] == "session456"
    assert payload["token_type"] == "access"


def test_jwt_refresh_token_creation():
    """Test refresh token creation."""
    manager = JWTManager(secret_key="test-secret-key", algorithm="HS256")

    token_data = TokenData(user_id="user123", session_id="session456")
    token = manager.create_refresh_token(token_data)

    payload = manager.verify_token(token)
    assert payload["token_type"] == "refresh"


def test_jwt_token_with_short_expiry():
    """Test token expiration."""
    manager = JWTManager(secret_key="test-secret-key", algorithm="HS256")

    token_data = TokenData(user_id="user123", session_id="session456")
    # Create token that expires immediately
    token = manager.create_access_token(token_data, expires_delta=timedelta(seconds=-1))

    # Should raise ExpiredSignatureError
    with pytest.raises(ExpiredSignatureError):
        manager.verify_token(token)


def test_jwt_invalid_signature():
    """Test that token with wrong key fails verification."""
    manager1 = JWTManager(secret_key="secret1", algorithm="HS256")
    manager2 = JWTManager(secret_key="secret2", algorithm="HS256")

    token_data = TokenData(user_id="user123", session_id="session456")
    token = manager1.create_access_token(token_data)

    # Should fail verification with different key
    with pytest.raises(Exception):
        manager2.verify_token(token)


def test_jwt_extract_user_id_without_verification():
    """Test extracting user_id from token without full verification."""
    manager = JWTManager(secret_key="test-secret-key", algorithm="HS256")

    token_data = TokenData(user_id="user123", session_id="session456")
    token = manager.create_access_token(token_data)

    # Extract without verification (useful for logging)
    user_id = manager.extract_user_id(token)
    assert user_id == "user123"

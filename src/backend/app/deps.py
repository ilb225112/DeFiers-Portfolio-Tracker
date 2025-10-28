"""FastAPI dependencies injection."""

import logging
from typing import Optional

from redis import asyncio as aioredis
from fastapi import Depends, HTTPException, status

from app.config import get_settings
from app.jwt_manager import get_jwt_manager
from app.redis_client import get_redis, SessionStore

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_session_store(redis: aioredis.Redis = Depends(get_redis)) -> SessionStore:
    """Dependency: Get session store."""
    return SessionStore(redis)


async def get_current_user_id(
    authorization: Optional[str] = None,
) -> str:
    """Extract and validate user_id from JWT token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jwt_manager = get_jwt_manager()
    try:
        payload = jwt_manager.verify_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id in token")
        return user_id
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_session_context(
    user_id: str = Depends(get_current_user_id),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """Get current session context (user_id + session info)."""
    store = SessionStore(redis)
    sessions = await store.list_user_sessions(user_id)
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active sessions found",
        )
    return {
        "user_id": user_id,
        "sessions": sessions,
    }

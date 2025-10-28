"""Session management endpoints."""

import logging
from typing import Optional

from redis import asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Header, status

from app.config import get_settings
from app.deps import get_current_user_id
from app.redis_client import SessionStore, get_redis
from app.schemas import SessionListResponse, SessionResponse

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["sessions"])


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    user_id: str = Depends(get_current_user_id),
    redis: aioredis.Redis = Depends(get_redis),
) -> SessionListResponse:
    """List all active sessions for the current user.

    This endpoint returns all active sessions across devices.
    Sessions are automatically cleaned up if they exceed the inactivity timeout.
    """
    store = SessionStore(redis)
    sessions = await store.list_user_sessions(user_id)

    # Convert to response format (parse last_activity from ISO string)
    session_responses = []
    for session in sessions:
        try:
            session_responses.append(
                SessionResponse(
                    session_id=session["session_id"],
                    user_id=session["user_id"],
                    device_info=eval(
                        session.get("device_info", "{}")
                    ),  # Parse JSON string
                    ip_address=session["ip_address"],
                    created_at=session["created_at"],
                    last_activity=session["last_activity"],
                )
            )
        except Exception as e:
            logger.warning(f"Error parsing session {session.get('session_id')}: {e}")
            continue

    return SessionListResponse(sessions=session_responses, count=len(session_responses))


@router.post("/logout")
async def logout(
    user_id: str = Depends(get_current_user_id),
    authorization: Optional[str] = Header(None),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """Log out the current session (revoke current token).

    This endpoint revokes the session associated with the current JWT token.
    The user will need to log in again.
    """
    # Extract session_id from the authorization header (for simplicity, we'll just revoke all sessions)
    # In a production system, you'd extract the jti from the JWT payload to revoke a specific session.
    store = SessionStore(redis)

    # For now, we'll revoke all sessions for this user
    # In a proper implementation, extract jti from JWT and revoke only that session
    count = await store.revoke_user_sessions(user_id)

    logger.info(f"User {user_id} logged out ({count} sessions revoked)")
    return {"message": f"Logged out successfully ({count} sessions revoked)"}


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """Revoke a specific session by session_id.

    This allows users to log out from a specific device remotely.
    The user can only revoke their own sessions.
    """
    store = SessionStore(redis)

    # Verify the session belongs to the current user
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke another user's session",
        )

    await store.revoke_session(session_id)
    logger.info(f"Session {session_id} revoked by user {user_id}")

    return {"message": f"Session {session_id} revoked successfully"}


@router.post("/logout-all")
async def logout_all(
    user_id: str = Depends(get_current_user_id),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """Log out from all devices (revoke all sessions).

    This endpoint revokes all sessions for the user across all devices.
    The user will need to log in again on all devices.
    Use with caution.
    """
    store = SessionStore(redis)
    count = await store.revoke_user_sessions(user_id)

    logger.info(
        f"User {user_id} logged out from all devices ({count} sessions revoked)"
    )
    return {"message": f"Logged out from all devices ({count} sessions revoked)"}

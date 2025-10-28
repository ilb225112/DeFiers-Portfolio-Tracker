"""Redis client and session management."""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from redis import asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global Redis client (initialized at app startup)
_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get Redis client (singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.redis_url, encoding="utf8", decode_responses=True
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class SessionStore:
    """Redis-backed session store for managing user sessions."""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.namespace = "session"

    def _key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.namespace}:{session_id}"

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        ttl_hours: int = 24,
    ) -> None:
        """Create a new session in Redis."""
        now = datetime.utcnow()
        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "device_info": json.dumps(device_info or {}),
            "ip_address": ip_address or "unknown",
        }
        key = self._key(session_id)
        ttl_seconds = ttl_hours * 3600

        await self.redis.setex(
            key,
            ttl_seconds,
            json.dumps(session_data),
        )
        logger.info(f"Session created: {session_id} for user {user_id}")

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from Redis."""
        key = self._key(session_id)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def update_last_activity(self, session_id: str) -> None:
        """Update last_activity timestamp for a session."""
        session = await self.get_session(session_id)
        if session:
            session["last_activity"] = datetime.utcnow().isoformat()
            key = self._key(session_id)
            # Get remaining TTL
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.setex(
                    key,
                    ttl,
                    json.dumps(session),
                )

    async def is_session_active(
        self, session_id: str, timeout_minutes: int = 30
    ) -> bool:
        """Check if session is active (not expired by inactivity or absolute TTL)."""
        session = await self.get_session(session_id)
        if not session:
            return False

        last_activity = datetime.fromisoformat(session["last_activity"])
        now = datetime.utcnow()

        # Check inactivity timeout
        if now - last_activity > timedelta(minutes=timeout_minutes):
            await self.revoke_session(session_id)
            return False

        return True

    async def revoke_session(self, session_id: str) -> None:
        """Revoke a session by deleting it from Redis."""
        key = self._key(session_id)
        deleted = await self.redis.delete(key)
        if deleted:
            logger.info(f"Session revoked: {session_id}")

    async def revoke_user_sessions(
        self, user_id: str, except_session_id: Optional[str] = None
    ) -> int:
        """Revoke all sessions for a user except optionally one."""
        pattern = f"{self.namespace}:*"
        cursor = 0
        deleted_count = 0

        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            for key in keys:
                session_data = await self.redis.get(key)
                if session_data:
                    session = json.loads(session_data)
                    if session.get("user_id") == user_id:
                        session_id = session.get("session_id")
                        if except_session_id is None or session_id != except_session_id:
                            await self.redis.delete(key)
                            deleted_count += 1

            if cursor == 0:
                break

        if deleted_count > 0:
            logger.info(f"Revoked {deleted_count} sessions for user {user_id}")

        return deleted_count

    async def list_user_sessions(self, user_id: str) -> list[Dict[str, Any]]:
        """List all active sessions for a user."""
        pattern = f"{self.namespace}:*"
        cursor = 0
        sessions = []

        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            for key in keys:
                session_data = await self.redis.get(key)
                if session_data:
                    session = json.loads(session_data)
                    if session.get("user_id") == user_id:
                        sessions.append(session)

            if cursor == 0:
                break

        return sessions

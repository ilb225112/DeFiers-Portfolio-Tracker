"""Pydantic schemas for session and authentication endpoints."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    """Response model for a single session."""

    session_id: str
    user_id: str
    device_info: Optional[dict] = None
    ip_address: str
    created_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Response model listing all user sessions."""

    sessions: List[SessionResponse] = Field(default_factory=list)
    count: int = 0


class RevokeSessionRequest(BaseModel):
    """Request model to revoke a specific session."""

    session_id: str


class LogoutAllRequest(BaseModel):
    """Request model for logout-all action (with optional password confirmation)."""

    password: Optional[str] = None
    confirm_2fa: Optional[str] = None  # 2FA code if enabled


class TokenResponse(BaseModel):
    """Response model for login/token endpoints."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = Field(default=30 * 60)  # seconds

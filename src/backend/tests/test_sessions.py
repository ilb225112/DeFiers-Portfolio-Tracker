"""Tests for session management endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_sessions_endpoint_requires_auth():
    """Test that sessions endpoint requires authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/auth/sessions")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_endpoint_requires_auth():
    """Test that logout endpoint requires authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/logout")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_all_endpoint_requires_auth():
    """Test that logout-all endpoint requires authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/logout-all")
        assert response.status_code == 401

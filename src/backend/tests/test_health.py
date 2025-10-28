"""Basic tests for backend health and configuration."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data


@pytest.mark.asyncio
async def test_app_startup():
    """Test app can be created and has main components."""
    from app.main import create_app
    from app.config import get_settings

    test_app = create_app()
    settings = get_settings()

    assert test_app is not None
    assert settings.app_name == "Crypto Portfolio Tracker"
    assert settings.debug is False or settings.debug is True  # Could be either


def test_settings_loaded():
    """Test configuration is loaded from environment."""
    from app.config import get_settings

    settings = get_settings()
    assert settings.database_url is not None
    assert settings.redis_url is not None
    assert settings.jwt_secret_key is not None

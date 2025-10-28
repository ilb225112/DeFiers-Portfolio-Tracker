"""Test fixtures and configuration."""

import pytest
import sys
from pathlib import Path

# Add src/backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture
def test_settings():
    """Get test settings."""
    from app.config import Settings

    return Settings(
        debug=True,
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/15",
    )


@pytest.fixture
async def test_client():
    """Get async test client."""
    from httpx import AsyncClient
    from app.main import create_app

    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

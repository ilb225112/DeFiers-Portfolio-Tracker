"""FastAPI main application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, configure_logging
from app.database import init_db, close_db
from app.redis_client import get_redis, close_redis
from app.api import sessions

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle (startup and shutdown)."""
    # Startup
    logger.info("Starting up Crypto Portfolio Backend...")
    configure_logging(settings)

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Initialize Redis
        await get_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to initialize resources: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Crypto Portfolio Backend...")
    try:
        await close_redis()
        logger.info("Redis connection closed")

        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "version": settings.app_version,
            "environment": settings.environment,
        }

    # Include routers
    app.include_router(sessions.router)

    return app


# Create app instance
app = create_app()

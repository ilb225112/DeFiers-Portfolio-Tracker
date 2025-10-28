"""Configuration management for the crypto portfolio backend."""

import logging
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Crypto Portfolio Tracker"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database
    database_url: str = (
        "postgresql+asyncpg://user:password@localhost:5432/crypto_portfolio"
    )
    database_echo: bool = False  # Log all SQL queries if True
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0

    # JWT & Security
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    session_timeout_minutes: int = 30
    max_session_ttl_hours: int = 24

    # Encryption
    encryption_master_key: Optional[str] = (
        None  # Should be 32 bytes hex-encoded for AES-256
    )

    # Email
    sendgrid_api_key: Optional[str] = None
    email_from: str = "noreply@defiers.io"

    # Market Data APIs
    coingecko_api_key: Optional[str] = None
    coingecko_pro_api_url: str = "https://pro-api.coingecko.com/api/v3"
    market_price_cache_ttl: int = 60  # seconds

    # S3
    s3_bucket: str = "crypto-portfolio-backups"
    s3_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # Celery
    celery_broker_url: Optional[str] = None  # Defaults to redis_url if not set
    celery_result_backend: Optional[str] = None  # Defaults to redis_url if not set

    # IP Geolocation
    geoip2_db_path: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL."""
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        """Get Celery result backend URL."""
        return self.celery_result_backend or self.redis_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def configure_logging(settings: Settings) -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    )

    # Reduce noise from libraries
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)

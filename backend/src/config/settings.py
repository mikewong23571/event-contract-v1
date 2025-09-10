"""
Application configuration management using Pydantic Settings.

This module centralizes environment configuration for the backend. It reads
from environment variables and optional `.env` files and exposes a cached
`get_settings()` accessor for use throughout the codebase.

Task: T082 Application configuration management
Path: backend/src/config/settings.py
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyUrl, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment.

    Only includes settings required by current tasks and used by the backend.
    """

    # General
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Backend service
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")

    # CORS
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_CREDENTIALS")

    # PostgreSQL
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="event_contract_dev", alias="POSTGRES_DB")
    postgres_user: str = Field(default="dev_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="dev_password", alias="POSTGRES_PASSWORD")

    # InfluxDB
    influxdb_url: Optional[AnyUrl] = Field(default=None, alias="INFLUXDB_URL")
    influxdb_token: Optional[str] = Field(default=None, alias="INFLUXDB_TOKEN")
    influxdb_org: Optional[str] = Field(default="trading", alias="INFLUXDB_ORG")
    influxdb_bucket: Optional[str] = Field(default="market_data", alias="INFLUXDB_BUCKET")

    # Redis
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    # Auth (non-enforcing; middleware reads token if provided)
    jwt_secret_key: Optional[str] = Field(default=None, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    def database_dsn_async(self) -> str:
        """Return an async SQLAlchemy DSN for PostgreSQL using asyncpg.

        If `database_url` is provided, convert it to asyncpg scheme when possible.
        """
        if self.database_url:
            url = self.database_url
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def database_dsn_sync(self) -> str:
        """Return a sync PostgreSQL DSN (psycopg2)."""
        if self.database_url:
            url = self.database_url
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql://", 1)
            return url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def redis_dsn(self) -> str:
        """Return Redis DSN."""
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class SettingsInfo(BaseModel):
    """Lightweight projection used for diagnostics/tests without leaking secrets."""

    environment: str
    debug: bool
    backend_host: str
    backend_port: int
    cors_origins: List[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached instance of Settings."""
    return Settings()


def get_public_settings() -> SettingsInfo:
    """Return safe-to-log subset of settings for diagnostics/tests."""
    s = get_settings()
    return SettingsInfo(
        environment=s.environment,
        debug=s.debug,
        backend_host=s.backend_host,
        backend_port=s.backend_port,
        cors_origins=s.cors_origins,
    )


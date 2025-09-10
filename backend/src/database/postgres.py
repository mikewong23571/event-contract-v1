"""
PostgreSQL connection setup using SQLAlchemy (async) and asyncpg.

Task: T077 PostgreSQL connection setup
Path: backend/src/database/postgres.py
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from ..config.settings import get_settings


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    """Return a singleton async SQLAlchemy engine configured from settings."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_dsn_async(),
            poolclass=NullPool,  # safer default for serverless/tests
            future=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return a singleton async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async DB session."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        await session.close()


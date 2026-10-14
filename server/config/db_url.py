"""Helpers for DATABASE_URL validation shared by settings and Alembic."""

from __future__ import annotations

import os
from typing import Optional

PRODUCTION_DATABASE_URL_MISSING = (
    "DATABASE_URL must be set when ENVIRONMENT=production "
    "(refusing silent sqlite fallback)"
)
PRODUCTION_DATABASE_URL_SQLITE = (
    "DATABASE_URL must not use sqlite when ENVIRONMENT=production"
)


def is_sqlite_database_url(url: Optional[str]) -> bool:
    """Return True when the URL is sqlite (sync, async, or relative)."""
    if not url:
        return False
    value = url.strip().lower()
    return (
        value.startswith("sqlite:")
        or value.startswith("sqlite+")
        or "+aiosqlite://" in value
        or ":///:memory:" in value
    )


def to_sync_database_url(url: str) -> str:
    """Convert async SQLAlchemy URLs to sync drivers for Alembic."""
    return url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "sqlite+aiosqlite://", "sqlite://"
    )


def assert_production_database_url(
    url: Optional[str], environment: Optional[str] = None
) -> None:
    """Raise RuntimeError if production is missing a non-sqlite DATABASE_URL."""
    env = (environment or os.getenv("ENVIRONMENT") or "development").lower()
    if env != "production":
        return
    if not url or not str(url).strip():
        raise RuntimeError(PRODUCTION_DATABASE_URL_MISSING)
    if is_sqlite_database_url(url):
        raise RuntimeError(PRODUCTION_DATABASE_URL_SQLITE)


def resolve_alembic_database_url(
    *,
    env_url: Optional[str],
    fallback: Optional[str] = None,
    environment: Optional[str] = None,
) -> str:
    """
    Resolve the Alembic SQLAlchemy URL.

    In production, DATABASE_URL is required and must not be sqlite. The
    alembic.ini fallback (sqlite:///./test.db) is never used then.
    """
    env = (environment or os.getenv("ENVIRONMENT") or "development").lower()
    if env == "production":
        assert_production_database_url(env_url, environment=env)
        url = env_url
    else:
        url = env_url or fallback

    if url:
        url = to_sync_database_url(url)

    if env == "production":
        assert_production_database_url(url, environment=env)

    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url

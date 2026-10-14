"""Production DATABASE_URL guards for settings and Alembic."""

import os
import unittest
from unittest.mock import patch

import pytest

from config.db_url import (
    PRODUCTION_DATABASE_URL_MISSING,
    PRODUCTION_DATABASE_URL_SQLITE,
    assert_production_database_url,
    is_sqlite_database_url,
    resolve_alembic_database_url,
)


@pytest.mark.unit
class TestSqliteUrlDetection:
    def test_detects_sqlite_variants(self):
        assert is_sqlite_database_url("sqlite:///./test.db")
        assert is_sqlite_database_url("sqlite+aiosqlite:///./climatewise-dev.db")
        assert is_sqlite_database_url("sqlite:///:memory:")
        assert not is_sqlite_database_url(
            "postgresql+asyncpg://user:pass@host:5432/db"
        )
        assert not is_sqlite_database_url(None)
        assert not is_sqlite_database_url("")


@pytest.mark.unit
class TestProductionDatabaseUrl:
    def test_production_rejects_missing(self):
        with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
            assert_production_database_url(None, environment="production")
        with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
            assert_production_database_url("  ", environment="production")

    def test_production_rejects_sqlite(self):
        with pytest.raises(RuntimeError, match="must not use sqlite"):
            assert_production_database_url("sqlite:///./test.db", environment="production")
        with pytest.raises(RuntimeError, match="must not use sqlite"):
            assert_production_database_url(
                "sqlite+aiosqlite:///./climatewise-dev.db", environment="production"
            )

    def test_production_accepts_postgres(self):
        assert_production_database_url(
            "postgresql+asyncpg://u:p@db.supabase.co:5432/postgres",
            environment="production",
        )

    def test_development_allows_sqlite(self):
        assert_production_database_url("sqlite:///./test.db", environment="development")


@pytest.mark.unit
class TestAlembicUrlResolution:
    def test_production_does_not_fall_back_to_ini_sqlite(self):
        with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
            resolve_alembic_database_url(
                env_url=None,
                fallback="sqlite:///./test.db",
                environment="production",
            )

    def test_production_rejects_sqlite_env(self):
        with pytest.raises(RuntimeError, match="must not use sqlite"):
            resolve_alembic_database_url(
                env_url="sqlite:///./test.db",
                fallback="sqlite:///./test.db",
                environment="production",
            )

    def test_production_uses_postgres_env(self):
        url = resolve_alembic_database_url(
            env_url="postgresql+asyncpg://u:p@host:5432/db",
            fallback="sqlite:///./test.db",
            environment="production",
        )
        assert url == "postgresql://u:p@host:5432/db"

    def test_development_may_use_ini_fallback(self):
        url = resolve_alembic_database_url(
            env_url=None,
            fallback="sqlite:///./test.db",
            environment="development",
        )
        assert url == "sqlite:///./test.db"


class TestSettingsProductionDatabase(unittest.TestCase):
    PROD_SECRET = "production-secret-key-32-chars-min"

    def test_production_exits_when_database_url_missing(self):
        from server.config.config import Settings

        with patch.dict(
            os.environ,
            {"ENVIRONMENT": "production", "SECRET_KEY": self.PROD_SECRET},
            clear=True,
        ):
            with self.assertRaises(SystemExit):
                Settings()

    def test_production_exits_when_database_url_is_sqlite(self):
        from server.config.config import Settings

        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "SECRET_KEY": self.PROD_SECRET,
                "DATABASE_URL": "sqlite:///./test.db",
            },
            clear=True,
        ):
            with self.assertRaises(SystemExit):
                Settings()

    def test_production_accepts_postgres_database_url(self):
        from server.config.config import Settings

        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "SECRET_KEY": self.PROD_SECRET,
                "DATABASE_URL": "postgresql+asyncpg://user:pass@host:5432/dbname",
            },
            clear=True,
        ):
            settings = Settings()
            self.assertIn("postgresql+asyncpg", settings.DATABASE_URL)

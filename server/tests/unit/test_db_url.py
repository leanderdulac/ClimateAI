"""Production DATABASE_URL guards for settings and Alembic."""

import os
import unittest
from unittest.mock import patch

import pytest

from config.db_url import (
    PRODUCTION_DATABASE_URL_MISSING,
    PRODUCTION_DATABASE_URL_SQLITE,
    assert_production_database_url,
    escape_alembic_config_url,
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


ENCODED_PASSWORD_URL = (
    "postgresql+asyncpg://postgres.tyzmywhvpmdfepxdtyes:"
    "p%40ss%2Fw%3Dord@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
)
ENCODED_PASSWORD_SYNC_URL = (
    "postgresql://postgres.tyzmywhvpmdfepxdtyes:"
    "p%40ss%2Fw%3Dord@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
)


@pytest.mark.unit
class TestAlembicPercentEncodedPassword:
    def test_escape_doubles_percent_signs(self):
        assert escape_alembic_config_url(ENCODED_PASSWORD_SYNC_URL) == (
            ENCODED_PASSWORD_SYNC_URL.replace("%", "%%")
        )
        assert "%40" in ENCODED_PASSWORD_SYNC_URL
        assert "%%40" in escape_alembic_config_url(ENCODED_PASSWORD_SYNC_URL)

    def test_set_main_option_rejects_unescaped_percent_password(self):
        from pathlib import Path
        from alembic.config import Config

        cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        with pytest.raises(ValueError, match="invalid interpolation syntax"):
            cfg.set_main_option("sqlalchemy.url", ENCODED_PASSWORD_SYNC_URL)

    def test_set_main_option_accepts_escaped_percent_password(self):
        from pathlib import Path
        from alembic.config import Config

        cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        cfg.set_main_option(
            "sqlalchemy.url", escape_alembic_config_url(ENCODED_PASSWORD_SYNC_URL)
        )
        assert cfg.get_main_option("sqlalchemy.url") == ENCODED_PASSWORD_SYNC_URL

    def test_run_alembic_upgrade_escapes_percent_encoded_password(self):
        from unittest.mock import patch
        from config.database import run_alembic_upgrade

        with patch("alembic.command.upgrade") as upgrade:
            run_alembic_upgrade(ENCODED_PASSWORD_URL)
        upgrade.assert_called_once()
        cfg = upgrade.call_args.args[0]
        assert cfg.get_main_option("sqlalchemy.url") == ENCODED_PASSWORD_SYNC_URL

    def test_asyncpg_disables_statement_cache_for_pgbouncer_6543(self):
        from urllib.parse import parse_qs, urlparse
        from config.database import apply_asyncpg_pgbouncer_settings

        url, connect_args = apply_asyncpg_pgbouncer_settings(ENCODED_PASSWORD_URL)
        assert connect_args["statement_cache_size"] == 0
        assert connect_args["prepared_statement_cache_size"] == 0
        assert connect_args["server_settings"]["prepared_statement_cache_size"] == "0"
        query = parse_qs(urlparse(url).query)
        assert query["statement_cache_size"] == ["0"]
        assert query["prepared_statement_cache_size"] == ["0"]
        assert "p%40ss%2Fw%3Dord" in url


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

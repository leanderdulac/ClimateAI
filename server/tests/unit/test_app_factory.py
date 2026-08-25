"""Application factory and schema bootstrap."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_still_public_after_factory_split(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"healthy", "degraded"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_init_db_uses_alembic_in_production():
    from config import database as db

    with patch.object(db.settings, "ENVIRONMENT", "production"), patch.object(
        db, "run_alembic_upgrade"
    ) as upgrade:
        await db.init_db()
        upgrade.assert_called_once()


@pytest.mark.unit
def test_sync_database_url_strips_async_drivers():
    from config.database import _sync_database_url

    assert _sync_database_url("postgresql+asyncpg://u:p@h/db") == "postgresql://u:p@h/db"
    assert _sync_database_url("sqlite+aiosqlite:///./x.db") == "sqlite:///./x.db"

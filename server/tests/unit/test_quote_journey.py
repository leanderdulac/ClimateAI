"""Quote journey persistence must not block agri strategy generation."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from models.sqlalchemy_models import Base
from services.quote_journey_service import QuoteJourneyService, _is_missing_journey_table


@pytest.mark.unit
def test_quote_journey_model_is_registered_on_metadata():
    assert "quote_journey_events" in Base.metadata.tables
    table = Base.metadata.tables["quote_journey_events"]
    assert "session_id" in table.c
    assert "event_type" in table.c
    assert "payload" in table.c


@pytest.mark.unit
def test_missing_table_detector():
    sqlite_error = OperationalError(
        "INSERT INTO quote_journey_events",
        {},
        Exception("no such table: quote_journey_events"),
    )
    assert _is_missing_journey_table(sqlite_error) is True
    assert _is_missing_journey_table(OperationalError("SELECT 1", {}, Exception("disk I/O error"))) is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_event_creates_missing_sqlite_table(tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    url = f"sqlite+aiosqlite:///{tmp_path / 'journey.db'}"
    engine = create_async_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn,
                    tables=[
                        Base.metadata.tables["users"],
                        Base.metadata.tables["locations"],
                    ],
                )
            )

        async with maker() as session:
            inspector_tables = await session.run_sync(
                lambda sync_session: inspect(sync_session.connection()).get_table_names()
            )
            assert "quote_journey_events" not in inspector_tables

            service = QuoteJourneyService()
            event = await service.log_event(
                db=session,
                session_id="session-1",
                event_type="strategy_generated",
                payload={"location": {"latitude": -22.9, "longitude": -43.1}},
            )
            assert event.id
            assert event.session_id == "session-1"

            tables = await session.run_sync(
                lambda sync_session: inspect(sync_session.connection()).get_table_names()
            )
            assert "quote_journey_events" in tables
    finally:
        await engine.dispose()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_strategy_plan_survives_journey_log_failure(monkeypatch):
    from api import agri_strategy
    from api.agri_strategy import AgriStrategyRequest

    class FakeDB:
        async def rollback(self):
            return None

    async def boom(**_kwargs):
        raise OperationalError(
            "INSERT",
            {},
            Exception("no such table: quote_journey_events"),
        )

    async def fake_plan(**_kwargs):
        return {"crop_type": "soybean", "phenological_stage": "flowering"}

    monkeypatch.setattr(agri_strategy.agri_strategy_service, "generate_plan", fake_plan)
    monkeypatch.setattr(agri_strategy.quote_journey_service, "log_event", boom)

    payload = AgriStrategyRequest(
        crop_type="soybean",
        phenological_stage="flowering",
        latitude=-22.9068,
        longitude=-43.1729,
        session_id="3e7a213d-7e00-442a-ad6d-ab6c727b3ed0",
    )
    response = await agri_strategy.generate_agri_strategy_plan(payload, db=FakeDB())
    assert response["crop_type"] == "soybean"

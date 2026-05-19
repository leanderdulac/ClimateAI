from datetime import date, datetime

import pytest
import pytest_asyncio
from config.database import close_db, init_db

pytestmark = [pytest.mark.integration, pytest.mark.requires_db]


@pytest_asyncio.fixture(autouse=True)
async def ensure_test_db_ready():
    await init_db()
    yield
    await close_db()


@pytest.mark.integration
class TestENSONoaaIntegration:
    def test_enso_series_endpoint(self, client, monkeypatch):
        from api import noaa_integration

        async def fake_roni_series():
            return [
                {"year": 2026, "season": "JFM", "value": -0.7},
                {"year": 2026, "season": "FMA", "value": -0.5},
            ]

        monkeypatch.setattr(noaa_integration.enso_service, "get_roni_series", fake_roni_series)

        response = client.get("/api/v1/noaa/enso/series", params={"index_name": "roni", "limit": 2})
        assert response.status_code == 200

        data = response.json()
        assert data["index"] == "roni"
        assert data["count"] == 2
        assert data["series"][-1]["value"] == -0.5

    def test_enso_snapshot_and_persisted_latest(self, client, monkeypatch):
        from api import noaa_integration

        async def fake_snapshot():
            return {
                "reference_date": date(2026, 4, 1),
                "roni": -0.5,
                "oni": -0.4,
                "soi": None,
                "olr": None,
                "nino12": None,
                "nino3": None,
                "nino34": -0.5,
                "nino4": None,
                "regime_label": "la_nina",
                "regime_confidence": "high",
                "provisional_flag": True,
                "source_url": "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/",
                "ingestion_timestamp": datetime.utcnow(),
                "enso_score": -0.62,
                "p_el_nino": 0.11,
                "p_la_nina": 0.79,
                "p_neutral": 0.21,
                "coupling_score": None,
                "transition_score": 0.2,
                "impact_risk_modifier": 1.075,
                "metadata": {"test": True},
            }

        monkeypatch.setattr(noaa_integration.enso_service, "get_latest_snapshot", fake_snapshot)

        response_snapshot = client.get("/api/v1/noaa/enso/snapshot", params={"persist": "true"})
        assert response_snapshot.status_code == 200
        body_snapshot = response_snapshot.json()
        assert body_snapshot["persisted"] is True
        assert body_snapshot["snapshot"]["regime_label"] == "la_nina"

        response_latest = client.get("/api/v1/noaa/enso/persisted/latest")
        assert response_latest.status_code == 200
        body_latest = response_latest.json()
        assert body_latest["found"] is True
        assert body_latest["regime_label"] == "la_nina"
        assert body_latest["impact_risk_modifier"] == pytest.approx(1.075)

    def test_enso_ingest_now_endpoint(self, client, monkeypatch):
        from api import noaa_integration

        async def fake_snapshot():
            return {
                "reference_date": date(2026, 5, 1),
                "roni": -0.4,
                "oni": -0.3,
                "soi": None,
                "olr": None,
                "nino12": None,
                "nino3": None,
                "nino34": -0.4,
                "nino4": None,
                "regime_label": "neutral",
                "regime_confidence": "medium",
                "provisional_flag": True,
                "source_url": "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/",
                "ingestion_timestamp": datetime.utcnow(),
                "enso_score": -0.2,
                "p_el_nino": 0.2,
                "p_la_nina": 0.5,
                "p_neutral": 0.5,
                "coupling_score": None,
                "transition_score": 0.1,
                "impact_risk_modifier": 1.06,
                "metadata": {"test": "ingest-now"},
            }

        monkeypatch.setattr(noaa_integration.enso_service, "get_latest_snapshot", fake_snapshot)

        response = client.post("/api/v1/noaa/enso/ingest-now")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["regime_label"] == "neutral"
        assert data["impact_risk_modifier"] == pytest.approx(1.06)

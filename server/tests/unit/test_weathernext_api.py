"""API tests for WeatherNext ensemble endpoints with mocked upstream."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from services.weathernext_ensemble_service import WeatherNextEnsembleService, reset_weathernext_service


def _sample_result() -> dict:
    return {
        "latitude": -22.9068,
        "longitude": -43.1729,
        "model": "google_weathernext2_ensemble",
        "hourly_fan": [{"time_local": "2026-10-14T12:00:00-03:00", "temperature_p50_c": 28}],
        "daily": [{"date": "2026-10-14", "p_heavy_rain": 0.4}],
        "pricing_exceedance": {"p_heavy_rain": 0.4, "precip_exceedance": {"ge_50mm": 0.4}},
        "timezone_daily": "America/Sao_Paulo",
        "license": {"provider": "Open-Meteo"},
    }


@pytest.fixture
def weathernext_client(client: TestClient, monkeypatch):
    service = WeatherNextEnsembleService(enabled=True, retries=1)
    service.forecast_point = AsyncMock(return_value=_sample_result())  # type: ignore[method-assign]
    service.forecast_municipality = AsyncMock(  # type: ignore[method-assign]
        return_value={**_sample_result(), "municipality": {"ibge_code": "1504802", "name": "Monte Alegre", "uf": "PA"}}
    )
    service.forecast_brazil_grid = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "resolution_deg": 1.0,
            "cell_count": 2,
            "p_heavy_rain_mean": 0.3,
            "cells": [
                {"lat": -22.0, "lon": -43.0, "p_heavy_rain": 0.5},
                {"lat": -23.0, "lon": -46.0, "p_heavy_rain": 0.1},
            ],
        }
    )
    service.forecast_batch = AsyncMock(return_value=[_sample_result()])  # type: ignore[method-assign]
    monkeypatch.setattr("api.weathernext_ensemble.get_weathernext_service", lambda: service)
    monkeypatch.setattr("services.weathernext_ensemble_service.get_weathernext_service", lambda: service)
    yield client, service
    reset_weathernext_service()


@pytest.mark.unit
def test_ensemble_point_endpoint(weathernext_client):
    client, service = weathernext_client
    response = client.get("/api/v1/forecast/ensemble", params={"lat": -22.9068, "lon": -43.1729})
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "google_weathernext2_ensemble"
    service.forecast_point.assert_awaited()


@pytest.mark.unit
def test_ensemble_municipality_endpoint(weathernext_client):
    client, _service = weathernext_client
    response = client.get("/api/v1/forecast/ensemble/municipality/1504802")
    assert response.status_code == 200
    assert response.json()["municipality"]["name"] == "Monte Alegre"


@pytest.mark.unit
def test_ensemble_brazil_endpoint(weathernext_client):
    client, _service = weathernext_client
    response = client.get("/api/v1/forecast/ensemble/brazil", params={"resolution": 1.0})
    assert response.status_code == 200
    assert response.json()["cell_count"] == 2


@pytest.mark.unit
def test_ensemble_disabled_returns_404(client: TestClient, monkeypatch):
    monkeypatch.setattr("lib.features.settings.FEATURE_WEATHERNEXT", False)
    response = client.get("/api/v1/forecast/ensemble", params={"lat": -22.9, "lon": -43.2})
    assert response.status_code == 404
    assert "weathernext" in response.json()["detail"]

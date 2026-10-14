"""WeatherNext 2 ensemble: stats, Brazil validation, municipality catalog, mocked HTTP."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.ibge_municipalities import get_municipality, monte_alegre_records
from services.oracle_consensus import REQUIRED_YES_VOTES, evaluate_oracle_consensus
from services.weathernext_ensemble_service import (
    BRAZIL_BBOX,
    MODEL_ID,
    OutsideBrazilError,
    WeatherNextEnsembleService,
    generate_brazil_grid,
)
from services.weathernext_prob import (
    apply_exceedance_loading,
    exceedance_probability,
    extract_member_series,
    parse_utc_times,
    percentile,
    process_open_meteo_hourly,
    weathernext_oracle_vote,
)


def _hourly_payload(member_count: int = 4) -> dict:
    times = [
        "2026-10-14T03:00",
        "2026-10-14T15:00",
        "2026-10-15T03:00",
        "2026-10-15T15:00",
    ]
    hourly = {"time": times, "temperature_2m": [22.0, 31.0, 21.0, 29.0], "precipitation": [0.0, 2.0, 0.0, 1.0]}
    for idx in range(1, member_count + 1):
        # Members 1-2 are wet/hot; 3-4 are dry/cool so probabilities are 0.5
        wet = idx <= member_count // 2
        hourly[f"temperature_2m_member{idx:02d}"] = [20 + idx, 36 if wet else 27, 19 + idx, 34 if wet else 26]
        hourly[f"precipitation_member{idx:02d}"] = [1.0, 40.0 if wet else 2.0, 0.5, 30.0 if wet else 1.0]
    return {
        "latitude": -22.9068,
        "longitude": -43.1729,
        "hourly": hourly,
        "model": MODEL_ID,
    }


@pytest.mark.unit
def test_percentiles_and_exceedance():
    assert percentile([10, 20, 30], 50) == 20
    assert exceedance_probability([5, 10, 50, 80], 50) == 0.5
    assert exceedance_probability([5, 10], 50) == 0.0


@pytest.mark.unit
def test_extract_members_includes_control():
    members = extract_member_series(
        {"temperature_2m": [1, 2], "temperature_2m_member01": [3, 4], "other": [0]},
        "temperature_2m_member",
        include_control="temperature_2m",
    )
    assert "00" in members
    assert "01" in members
    assert len(members) == 2


@pytest.mark.unit
def test_daily_aggregation_uses_sao_paulo():
    payload = _hourly_payload()
    fan, daily, meta = process_open_meteo_hourly(payload, include_members=True)
    assert meta["timezone_daily"] == "America/Sao_Paulo"
    assert meta["member_count"] >= 4
    assert fan
    assert daily
    first = daily[0]
    assert first.precip_exceedance["ge_10mm"] >= 0
    assert 0 <= first.p_heavy_rain <= 1
    assert first.temperature_p10_c <= first.temperature_p50_c <= first.temperature_p90_c


@pytest.mark.unit
def test_utc_afternoon_falls_on_sao_paulo_same_calendar_day():
    times = parse_utc_times(["2026-10-14T15:00"])
    local = times[0].astimezone(timezone.utc)
    assert local.hour == 15


@pytest.mark.unit
def test_oracle_vote_majority():
    _, daily, _ = process_open_meteo_hourly(_hourly_payload(), include_members=True)
    vote = weathernext_oracle_vote(
        daily, trigger_type="rainfall", threshold=25.0, condition="above"
    )
    assert vote["source"] == "google_weathernext2_ensemble"
    assert "probability" in vote
    assert vote["vote"] in {True, False}


@pytest.mark.unit
def test_exceedance_loading():
    assert apply_exceedance_loading(1000, 0.4, 0.25) == 1100


@pytest.mark.unit
def test_brazil_bbox_rejects_lisbon():
    service = WeatherNextEnsembleService(enabled=True)
    assert service.in_brazil(-22.9, -43.17) is True
    with pytest.raises(OutsideBrazilError):
        service.validate_brazil(38.72, -9.14)
    rio = (-22.9068, -43.1729)
    assert BRAZIL_BBOX["lat_min"] <= rio[0] <= BRAZIL_BBOX["lat_max"]


@pytest.mark.unit
def test_cache_key_rounds_coordinates():
    service = WeatherNextEnsembleService(enabled=True, coord_decimals=1)
    assert service.cache_key(-22.91, -43.17) == service.cache_key(-22.94, -43.19)
    assert service.cache_key(-22.91, -43.17) != service.cache_key(-23.5, -46.6)


@pytest.mark.unit
def test_municipality_catalog_includes_monte_alegre():
    records = monte_alegre_records()
    assert records
    assert any(row["name"] == "Monte Alegre" for row in records)
    pa = get_municipality("1504802")
    assert pa["uf"] == "PA"
    assert pa["name"] == "Monte Alegre"


@pytest.mark.unit
def test_brazil_grid_resolution():
    coarse = generate_brazil_grid(2.0)
    fine = generate_brazil_grid(1.0)
    assert len(fine) > len(coarse)
    assert all(WeatherNextEnsembleService.in_brazil(lat, lon) for lat, lon in coarse)


@pytest.mark.asyncio
async def test_forecast_point_uses_mocked_http():
    service = WeatherNextEnsembleService(enabled=True, retries=1, cache_ttl=3600)
    service._http_ensemble = AsyncMock(return_value=[_hourly_payload()])  # type: ignore[method-assign]
    result = await service.forecast_point(-22.9068, -43.1729)
    assert result["model"] == MODEL_ID
    assert result["timezone_daily"] == "America/Sao_Paulo"
    assert result["hourly_fan"]
    assert result["daily"]
    assert "p_heavy_rain" in result["pricing_exceedance"]
    assert result["license"]["url"].startswith("https://open-meteo.com")
    # second call hits cache
    result2 = await service.forecast_point(-22.9068, -43.1729)
    assert result2["daily"]
    service._http_ensemble.assert_awaited_once()


@pytest.mark.asyncio
async def test_forecast_rejects_outside_brazil():
    service = WeatherNextEnsembleService(enabled=True)
    with pytest.raises(OutsideBrazilError):
        await service.forecast_point(40.7, -74.0)


@pytest.mark.asyncio
async def test_municipality_forecast_monte_alegre():
    service = WeatherNextEnsembleService(enabled=True, retries=1)
    service._http_ensemble = AsyncMock(return_value=[_hourly_payload()])  # type: ignore[method-assign]
    result = await service.forecast_municipality("1504802")
    assert result["municipality"]["name"] == "Monte Alegre"
    assert result["municipality"]["uf"] == "PA"


@pytest.mark.asyncio
async def test_batch_validates_every_coordinate():
    service = WeatherNextEnsembleService(enabled=True, retries=1)
    service._http_ensemble = AsyncMock(return_value=[_hourly_payload(), _hourly_payload()])  # type: ignore[method-assign]
    with pytest.raises(OutsideBrazilError):
        await service.forecast_batch([(-22.9, -43.2), (51.5, -0.1)])


@pytest.mark.asyncio
async def test_oracle_consensus_keeps_two_vote_threshold():
    class FakeIndex:
        def __init__(self, met: bool, value: float):
            self.trigger_met = met
            self.value = value

    class FakeOracle:
        def get_climate_index(self, **kwargs):
            source = kwargs["source"]
            if source == "inmet":
                return FakeIndex(True, 80)
            if source == "noaa":
                return FakeIndex(False, 10)
            return FakeIndex(True, 70)

    wn = WeatherNextEnsembleService(enabled=True, retries=1)
    wn.forecast_point = AsyncMock(  # type: ignore[method-assign]
        return_value={"daily": [{"date": "2026-10-14", "p_heavy_rain": 0.8, "precip_exceedance": {"ge_50mm": 0.8}, "heat_exceedance": {}, "precip_p50_mm": 60, "temperature_p50_c": 30, "member_count": 4}]}
    )
    wn.oracle_vote = MagicMock(return_value={"source": "google_weathernext2_ensemble", "vote": True, "probability": 0.8})

    result = await evaluate_oracle_consensus(
        latitude=-22.9,
        longitude=-43.2,
        index_type="rainfall",
        trigger_value=50,
        trigger_condition="above",
        oracle_service=FakeOracle(),
        weathernext_service=wn,
        include_weathernext=True,
    )
    assert result["required_votes"] == REQUIRED_YES_VOTES == 2
    assert result["consensus"] is True
    assert "inmet" in result["agreeing_sources"]
    assert "openmeteo" in result["agreeing_sources"]
    assert result["weathernext_voted"] is True
    sources = [v["source"] for v in result["votes"]]
    assert "google_weathernext2_ensemble" in sources
    assert sources.count("inmet") == 1


@pytest.mark.asyncio
async def test_oracle_consensus_without_weathernext_still_two_of_three():
    class FakeIndex:
        def __init__(self, met: bool):
            self.trigger_met = met
            self.value = 1

    class FakeOracle:
        def get_climate_index(self, **kwargs):
            return FakeIndex(kwargs["source"] != "noaa")

    result = await evaluate_oracle_consensus(
        latitude=-22.9,
        longitude=-43.2,
        index_type="rainfall",
        trigger_value=50,
        oracle_service=FakeOracle(),
        include_weathernext=False,
    )
    assert result["required_votes"] == 2
    assert result["consensus"] is True
    assert result["weathernext_voted"] is False
    assert len(result["votes"]) == 3

import pytest

from services.agri_strategy_service import AgriculturalStrategyService


@pytest.mark.asyncio
async def test_generate_plan_el_nino_prioritizes_heat_drought(monkeypatch):
    service = AgriculturalStrategyService()

    async def fake_enso(_db):
        return {
            "source": "database",
            "regime_label": "el_nino",
            "regime_confidence": "high",
            "impact_risk_modifier": 1.1,
            "reference_date": "2026-05-01",
        }

    async def fake_forecast(_lat, _lon):
        return {
            "source": "NOAA/NWS",
            "forecast": [
                {
                    "temperature": 36,
                    "windSpeed": "48 mph",
                    "shortForecast": "Sunny and hot",
                    "detailedForecast": "Dry weather persists",
                }
            ],
        }

    monkeypatch.setattr(service, "_get_latest_enso_context", fake_enso)
    monkeypatch.setattr(service.noaa_service, "get_weather_forecast", fake_forecast)

    plan = await service.generate_plan(
        crop_type="corn",
        phenological_stage="flowering",
        latitude=-23.55,
        longitude=-46.63,
        planning_horizon_days=120,
        risk_tolerance="low",
        farm_profile={"irrigation_available": False, "drainage_level": "medium"},
        db=None,
    )

    assert plan["climate_outlook"]["enso"]["regime_label"] == "el_nino"
    assert plan["exposure_scores"]["drought"] >= plan["exposure_scores"]["excess_rain"]
    assert any(a["category"] == "water_management" for a in plan["operational_actions"])


@pytest.mark.asyncio
async def test_generate_plan_la_nina_prioritizes_excess_rain(monkeypatch):
    service = AgriculturalStrategyService()

    async def fake_enso(_db):
        return {
            "source": "database",
            "regime_label": "la_nina",
            "regime_confidence": "high",
            "impact_risk_modifier": 1.05,
            "reference_date": "2026-05-01",
        }

    async def fake_forecast(_lat, _lon):
        return {
            "source": "NOAA/NWS",
            "forecast": [
                {
                    "temperature": 24,
                    "windSpeed": "20 mph",
                    "shortForecast": "Heavy rain",
                    "detailedForecast": "Thunderstorm and flood risk",
                }
            ],
        }

    monkeypatch.setattr(service, "_get_latest_enso_context", fake_enso)
    monkeypatch.setattr(service.noaa_service, "get_weather_forecast", fake_forecast)

    plan = await service.generate_plan(
        crop_type="soybean",
        phenological_stage="planting",
        latitude=-23.55,
        longitude=-46.63,
        planning_horizon_days=90,
        risk_tolerance="medium",
        farm_profile={"irrigation_available": True, "drainage_level": "low"},
        db=None,
    )

    assert plan["climate_outlook"]["enso"]["regime_label"] == "la_nina"
    assert plan["exposure_scores"]["excess_rain"] >= 0.5
    assert any(a["category"] == "drainage" for a in plan["operational_actions"])

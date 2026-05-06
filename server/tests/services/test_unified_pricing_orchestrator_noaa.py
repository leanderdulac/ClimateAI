import os

import pytest

# Prevent settings validation issues in environments where DEBUG may be non-boolean.
os.environ.setdefault("DEBUG", "false")

from services.unified_pricing_orchestrator import (
    ModelResult,
    PricingInput,
    PricingModel,
    UnifiedPricingOrchestrator,
)


class _StubNOAASevere:
    async def get_weather_forecast(self, lat, lon):
        return {
            "source": "NOAA/NWS",
            "forecast": [
                {
                    "temperature": 38,
                    "windSpeed": "55 mph",
                    "shortForecast": "Heavy rain and thunderstorm",
                    "detailedForecast": "Severe storm expected",
                }
            ],
        }


class _StubNOAAFail:
    async def get_weather_forecast(self, lat, lon):
        raise RuntimeError("simulated NOAA outage")


@pytest.fixture
def base_input():
    return PricingInput(
        coverage_amount=100000,
        location_latitude=-23.55,
        location_longitude=-46.63,
        risk_factors={"climatic_risk": 0.3},
        models_to_use=[PricingModel.COMPREHENSIVE],
    )


def _stub_single_model(orchestrator: UnifiedPricingOrchestrator):
    orchestrator._services_loaded = True
    orchestrator._run_comprehensive_model = lambda inp: ModelResult(
        model_name=PricingModel.COMPREHENSIVE.value,
        premium=1000.0,
        confidence_interval=(900.0, 1100.0),
        risk_score=0.40,
        calculation_time_ms=1.0,
    )


def test_noaa_adjustment_default_parameters(base_input):
    orchestrator = UnifiedPricingOrchestrator()
    _stub_single_model(orchestrator)
    orchestrator._noaa_service = _StubNOAASevere()

    result = orchestrator.calculate_unified_premium(base_input)

    # combined_risk = 0.4 * 0.85 + 1.0 * 0.15 = 0.49
    assert result.combined_risk_score == pytest.approx(0.49)
    # recommended = 1000 * 1.0(agreement) * 1.12(default NOAA max impact)
    assert result.recommended_premium == pytest.approx(1120.0)

    adjustment = result.explanation["noaa_weather_adjustment"]
    assert adjustment["weather_risk_score"] == pytest.approx(1.0)
    assert adjustment["premium_modifier"] == pytest.approx(1.12)


def test_noaa_adjustment_uses_environment_parameters(base_input, monkeypatch):
    monkeypatch.setenv("NOAA_RISK_BLEND_WEIGHT", "0.30")
    monkeypatch.setenv("NOAA_PREMIUM_MAX_IMPACT", "0.20")

    orchestrator = UnifiedPricingOrchestrator()
    _stub_single_model(orchestrator)
    orchestrator._noaa_service = _StubNOAASevere()

    result = orchestrator.calculate_unified_premium(base_input)

    # combined_risk = 0.4 * 0.7 + 1.0 * 0.3 = 0.58
    assert result.combined_risk_score == pytest.approx(0.58)
    # recommended = 1000 * 1.20
    assert result.recommended_premium == pytest.approx(1200.0)

    blend = result.explanation["noaa_blend_parameters"]
    assert blend["noaa_risk_blend_weight"] == pytest.approx(0.30)
    assert blend["noaa_premium_max_impact"] == pytest.approx(0.20)


def test_noaa_unavailable_keeps_neutral_modifier(base_input):
    orchestrator = UnifiedPricingOrchestrator()
    _stub_single_model(orchestrator)
    orchestrator._noaa_service = _StubNOAAFail()

    result = orchestrator.calculate_unified_premium(base_input)

    # neutral fallback on NOAA errors
    assert result.combined_risk_score == pytest.approx(0.40)
    assert result.recommended_premium == pytest.approx(1000.0)
    assert any("neutral weather modifier" in w for w in result.warnings)

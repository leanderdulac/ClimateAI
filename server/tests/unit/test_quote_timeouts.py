"""Quote path must stay under ~20s and never train LSTM on the request."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from api.policy_pricing import (
    EVT_TIMEOUT_SECONDS,
    GEOCODE_TIMEOUT_SECONDS,
    OVERLAY_TIMEOUT_SECONDS,
    PolicyRequest,
    PricingResult,
    _merge_overlay,
    calculate_policy_endpoint,
)
from services.pytorch_climate_pricing_service import (
    CACHE_TTL_SECONDS,
    CachedLstm,
    PyTorchClimatePricingService,
    pytorch_climate_pricing_service,
    region_key,
)
from services.sgb_service import GeologicalRiskAdjuster, SGBGeoportalClient


def _sample_request() -> PolicyRequest:
    return PolicyRequest(
        asset_value=100_000,
        severity_amount=10_000,
        frequency_pct=5.0,
        latitude=-2.0,
        longitude=-54.07,
    )


@pytest.mark.unit
def test_quote_timeout_budgets_match_prod_slo():
    assert GEOCODE_TIMEOUT_SECONDS == 5
    assert EVT_TIMEOUT_SECONDS == 15
    assert OVERLAY_TIMEOUT_SECONDS == 8
    assert CACHE_TTL_SECONDS == 24 * 3600


@pytest.mark.unit
@pytest.mark.asyncio
async def test_quote_returns_under_20s_with_mocked_slow_services(monkeypatch):
    import api.policy_pricing as pp

    monkeypatch.setattr(pp, "GEOCODE_TIMEOUT_SECONDS", 0.15)
    monkeypatch.setattr(pp, "EVT_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setattr(pp, "OVERLAY_TIMEOUT_SECONDS", 0.15)

    async def slow_geo(*_args, **_kwargs):
        await asyncio.sleep(30)
        return {"city": "Monte Alegre", "uf": "PA"}

    async def slow_evt(*_args, **_kwargs):
        await asyncio.sleep(30)
        return None

    async def slow_overlay(*_args, **_kwargs):
        await asyncio.sleep(30)
        return {"overlay_pending": False}

    monkeypatch.setattr(pp, "_resolve_quote_region", slow_geo)
    monkeypatch.setattr(pp, "_calculate_evt_pricing", slow_evt)
    monkeypatch.setattr(pp, "_compute_pytorch_overlay", slow_overlay)

    started = time.perf_counter()
    result = await calculate_policy_endpoint(_sample_request())
    elapsed = time.perf_counter() - started

    assert elapsed < 2.0
    assert elapsed < 20.0
    assert isinstance(result, PricingResult)
    assert result.risk_factors is not None
    assert result.risk_factors.get("overlay_pending") is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_loop_not_blocked_during_overlay_predict(monkeypatch):
    svc = pytorch_climate_pricing_service
    svc.reset_caches()
    key = region_key(-2.0, -54.07)
    svc.model_cache.set(
        key,
        CachedLstm(
            service=object(),
            archive={"n_obs": 40, "start": "s", "end": "e", "source": "t"},
            oni=None,
            regime=None,
            train_metrics={},
        ),
    )

    def slow_predict(*_args, **_kwargs):
        time.sleep(0.35)
        return {
            "overlay_pending": False,
            "device": "cpu",
            "simulation": {
                "frequency_multiplier": 1.1,
                "severity_multiplier": 1.0,
            },
            "observations": {"n": 40},
            "lstm": {"next_day_precip_mm": 1.2},
        }

    monkeypatch.setattr(
        "services.pytorch_climate_pricing_service.HAS_TORCH", True
    )
    monkeypatch.setattr(svc, "_predict_price_sync", slow_predict)

    ticks = 0

    async def ticker():
        nonlocal ticks
        for _ in range(6):
            ticks += 1
            await asyncio.sleep(0.05)

    overlay_task = asyncio.create_task(
        svc.compute_overlay(
            -2.0,
            -54.07,
            asset_value=1000,
            severity_amount=100,
            frequency_pct=5,
        )
    )
    await asyncio.gather(overlay_task, ticker())
    assert ticks >= 4
    out = overlay_task.result()
    assert out["overlay_pending"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compute_overlay_cache_miss_does_not_train(monkeypatch):
    svc = PyTorchClimatePricingService()
    svc.reset_caches()
    trained = {"n": 0}

    def boom(*_args, **_kwargs):
        trained["n"] += 1
        raise AssertionError("must not train on the request path")

    scheduled = {"n": 0}

    def fake_schedule(*_args, **_kwargs):
        scheduled["n"] += 1

    monkeypatch.setattr(
        "services.pytorch_climate_pricing_service.HAS_TORCH", True
    )
    monkeypatch.setattr(svc, "_train_sync", boom)
    monkeypatch.setattr(svc, "schedule_train", fake_schedule)

    out = await svc.compute_overlay(
        -2.0,
        -54.07,
        asset_value=1000,
        severity_amount=100,
        frequency_pct=5,
    )
    assert out["overlay_pending"] is True
    assert trained["n"] == 0
    assert scheduled["n"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_simulate_default_does_not_train_inline(monkeypatch):
    svc = PyTorchClimatePricingService()
    svc.reset_caches()
    monkeypatch.setattr(
        "services.pytorch_climate_pricing_service.HAS_TORCH", True
    )
    monkeypatch.setattr(svc, "schedule_train", lambda *_a, **_k: None)
    monkeypatch.setattr(
        svc,
        "_train_region",
        AsyncMock(side_effect=AssertionError("inline train")),
    )
    out = await svc.simulate(
        -2.0,
        -54.07,
        asset_value=1000,
        severity_amount=100,
        frequency_pct=5,
    )
    assert out["overlay_pending"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_archive_and_oni_cached_per_rounded_region(monkeypatch):
    svc = PyTorchClimatePricingService()
    svc.reset_caches()
    fetches = {"archive": 0, "oni": 0}

    def fake_archive(lat, lon, days=365, timeout=12):
        fetches["archive"] += 1
        return {
            "n_obs": 50,
            "dates": ["2024-01-01"],
            "temperature": [25.0],
            "precipitation": [1.0],
            "pressure": [1010.0],
            "wind": [3.0],
            "start": "2024-01-01",
            "end": "2024-01-02",
            "latitude": lat,
            "longitude": lon,
            "source": "test",
        }

    async def fake_oni():
        fetches["oni"] += 1
        return 0.4, "nino"

    monkeypatch.setattr(
        "services.pytorch_climate_pricing_service.fetch_openmeteo_daily_archive",
        fake_archive,
    )
    monkeypatch.setattr(
        "services.pytorch_climate_pricing_service._fetch_oni_snapshot",
        fake_oni,
    )

    first = await svc.get_archive(-2.004, -54.071)
    second = await svc.get_archive(-2.001, -54.069)
    oni_a = await svc.get_oni()
    oni_b = await svc.get_oni()
    assert first["n_obs"] == 50
    assert second is first
    assert fetches["archive"] == 1
    assert oni_a == (0.4, "nino")
    assert oni_b == oni_a
    assert fetches["oni"] == 1


@pytest.mark.unit
def test_sgb_does_not_call_sigmine(monkeypatch):
    called = []

    def fake_get(*_args, **_kwargs):
        called.append((_args, _kwargs))
        raise AssertionError("SIGMINE/ArcGIS must not be called")

    monkeypatch.setattr("services.sgb_service.requests.get", fake_get)
    client = SGBGeoportalClient()
    df = client.fetch_risk_areas_by_bbox(-55.0, -3.0, -53.0, -1.0)
    assert df.empty
    assert called == []
    risk = client.get_risk_factor(-2.0, -54.07)
    assert risk["fator_ajuste"] == 1.0
    assert called == []
    adj = GeologicalRiskAdjuster(client).adjust_premium(1000.0, -2.0, -54.07)
    assert adj["risk_factor"] == 1.0
    assert adj["adjusted_premium"] == 1000.0
    assert called == []


@pytest.mark.unit
def test_openmeteo_verifies_tls():
    from services.openmeteo_service import OpenMeteoService

    svc = OpenMeteoService()
    assert svc.cache_session.verify is True


@pytest.mark.unit
def test_merge_overlay_pending_does_not_scale_premium():
    from api.policy_pricing import FinancialBreakdown

    result = PricingResult(
        is_approved=True,
        status="APPROVED",
        rejection_reason=None,
        financials=FinancialBreakdown(
            pure_premium=100,
            risk_margin=10,
            loadings=10,
            total_premium=200,
            op_claims_cost=1,
            op_admin_cost=1,
            op_subscription_cost=1,
            total_operational_costs=3,
            net_profit=10,
            profit_margin_pct=5,
            combined_ratio=0.9,
        ),
        decision_flow="GREEN",
        risk_factors={},
    )
    _merge_overlay(result, {"overlay_pending": True, "region": [-2.0, -54.07]})
    assert result.financials.total_premium == 200
    assert result.risk_factors["overlay_pending"] is True

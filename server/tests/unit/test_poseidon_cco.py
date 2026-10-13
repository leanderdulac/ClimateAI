"""Poseidon CCO: PSA thresholds, outage math, demanda clamp, auth."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from services.poseidon_cco import (
    GUANDU_CAPACITY_L_S,
    allocate_guandu_outage,
    clamp_horizon,
    demo_geosmina,
    demo_guandu_50,
    evaluate_geosmina,
    forecast_demanda,
    reset_cco_state,
)


@pytest.fixture(autouse=True)
def _reset_cco():
    reset_cco_state()
    yield
    reset_cco_state()


@pytest.mark.unit
def test_geosmina_lab_alerta_threshold():
    out = evaluate_geosmina(lab_geosmin_ug_l=0.02)
    assert out["level"] == "alerta"
    assert out["sensor_online_geosmin_ngl"] is False
    assert out["thresholds"]["lab_geosmin_alerta_ug_l"] == 0.02
    assert any(
        "0.02" in step or "laboratório" in step.lower() or "laudo" in step.lower()
        for step in out["sop"]
    )


@pytest.mark.unit
def test_geosmina_lab_critico_threshold():
    out = evaluate_geosmina(lab_geosmin_ug_l=0.1)
    assert out["level"] == "critico"
    assert out["psa"]["level"] == "critico"


@pytest.mark.unit
def test_geosmina_proxy_bloom_is_alerta_without_lab():
    out = evaluate_geosmina(
        phycocyanin_proxy=3.0,
        temp_c=28.0,
        low_flow=True,
        lab_geosmin_ug_l=0.0,
    )
    assert out["level"] == "alerta"


@pytest.mark.unit
def test_geosmina_proxy_and_lab_elevated_is_critico():
    out = evaluate_geosmina(
        phycocyanin_proxy=2.6,
        temp_c=27.8,
        low_flow=True,
        lab_geosmin_ug_l=0.038,
    )
    assert out["level"] == "critico"


@pytest.mark.unit
def test_geosmina_below_thresholds_is_normal():
    out = evaluate_geosmina(
        phycocyanin_proxy=0.4,
        temp_c=22.0,
        low_flow=False,
        lab_geosmin_ug_l=0.004,
    )
    assert out["level"] == "normal"
    assert out["sensor_online_geosmin_ngl"] is False


@pytest.mark.unit
def test_guandu_outage_allocates_22500_by_fixture_shares():
    out = allocate_guandu_outage(0.5)
    assert out["capacity_l_s"] == GUANDU_CAPACITY_L_S
    assert out["remaining_l_s"] == 22500
    by_id = {row["id"]: row for row in out["allocations"]}
    assert by_id["aguas_do_rio"]["remaining_l_s"] == 15300
    assert by_id["igua"]["remaining_l_s"] == 3825
    assert by_id["rio_mais"]["remaining_l_s"] == 3375
    assert sum(row["remaining_l_s"] for row in out["allocations"]) == 22500
    assert len(out["at_risk"]) == 3
    assert out["scenario"]["at"].startswith("2026-07-21")
    assert out["virtual_novo_guandu"]["online"] is False
    assert out["level"] == "critico"


@pytest.mark.unit
def test_guandu_outage_full_production_has_no_deficit():
    out = allocate_guandu_outage(1.0)
    assert out["remaining_l_s"] == 45000
    assert all(row["deficit_l_s"] == 0 for row in out["allocations"])
    assert out["level"] == "normal"


@pytest.mark.unit
def test_demanda_horizon_clamp_1_to_48():
    assert clamp_horizon(0) == 1
    assert clamp_horizon(-3) == 1
    assert clamp_horizon(1) == 1
    assert clamp_horizon(24) == 24
    assert clamp_horizon(48) == 48
    assert clamp_horizon(100) == 48
    assert clamp_horizon("nope") == 24
    out = forecast_demanda(
        100, weather={"temperature": 25, "rain": 0, "live": False}
    )
    assert out["horizonte_h"] == 48
    assert len(out["series"]) == 48
    guandu = out["series"][0]["systems"]["guandu"]
    assert guandu["low_l_s"] <= guandu["point_l_s"] <= guandu["high_l_s"]


@pytest.mark.unit
def test_cco_routes_require_auth(client: TestClient):
    paths = [
        "/api/v1/poseidon/cco/systems",
        "/api/v1/poseidon/cco/cma",
        "/api/v1/poseidon/cco/connectors",
        "/api/v1/poseidon/cco/psa",
        "/api/v1/poseidon/cco/incidents",
        "/api/v1/poseidon/cco/demanda",
    ]
    for path in paths:
        assert client.get(path).status_code == 401, path
    assert client.post("/api/v1/poseidon/cco/demo/geosmina").status_code == 401
    assert client.post("/api/v1/poseidon/cco/demo/guandu-50").status_code == 401


@pytest.mark.unit
def test_cco_routes_ok_with_auth(authenticated_client: TestClient):
    fake = {
        "data": None,
        "meta": {"status": "unavailable", "source": "test", "live": False},
    }
    with patch(
        "services.poseidon_cco._probe_tool",
        new_callable=AsyncMock,
        return_value=fake,
    ), patch(
        "services.poseidon_cco._weather_covariates",
        new_callable=AsyncMock,
        return_value={
            "temperature": 25.0,
            "rain": 0.0,
            "live": False,
            "source": "fixture",
        },
    ):
        systems = authenticated_client.get("/api/v1/poseidon/cco/systems")
        cma = authenticated_client.get("/api/v1/poseidon/cco/cma")
        connectors = authenticated_client.get("/api/v1/poseidon/cco/connectors")
        psa = authenticated_client.get("/api/v1/poseidon/cco/psa")
        incidents = authenticated_client.get("/api/v1/poseidon/cco/incidents")
        demanda = authenticated_client.get(
            "/api/v1/poseidon/cco/demanda?horizonte_h=24"
        )
        geo = authenticated_client.post("/api/v1/poseidon/cco/demo/geosmina")
        outage = authenticated_client.post("/api/v1/poseidon/cco/demo/guandu-50")

    for response in (
        systems,
        cma,
        connectors,
        psa,
        incidents,
        demanda,
        geo,
        outage,
    ):
        assert response.status_code == 200, response.text
        body = response.json()
        assert "data" in body and "meta" in body
        assert body["meta"]["live"] is False

    assert systems.json()["data"]["systems"][0]["id"] == "guandu"
    assert systems.json()["data"]["systems"][0]["lat"] == -22.759
    assert cma.json()["data"]["cameras"] == 36
    assert cma.json()["data"]["status"] == "fixture"
    assert psa.json()["data"]["sensor_online_geosmin_ngl"] is False
    assert psa.json()["data"]["thresholds"]["lab_geosmin_alerta_ug_l"] == 0.02
    assert geo.json()["data"]["evaluation"]["level"] in {"alerta", "critico"}
    assert outage.json()["data"]["evaluation"]["remaining_l_s"] == 22500
    assert demanda.json()["data"]["horizonte_h"] == 24

    listed = authenticated_client.get("/api/v1/poseidon/cco/incidents")
    assert listed.status_code == 200
    assert listed.json()["data"]["count"] >= 2


@pytest.mark.unit
def test_demo_helpers_label_fixtures():
    geo = demo_geosmina()
    assert geo["meta"]["live"] is False
    assert geo["meta"]["kind"] == "fixture"
    outage = demo_guandu_50()
    assert outage["data"]["evaluation"]["scenario"]["id"] == "guandu-50-2026-07-21"

"""Poseidon tools: observed envelopes, no invented climate numbers."""

from unittest.mock import patch

from services import poseidon_tools as tools

import pytest
from fastapi.testclient import TestClient

from services.poseidon_tools import (
    compare_to_siren,
    execute_tool,
    parse_sar_sin_table,
    recommend_engine,
    resolve_place,
    siren_protocol,
)


@pytest.mark.unit
def test_recommend_engine_picks_gev_for_drainage():
    out = recommend_engine("chuva de 50 anos para drenagem do PMSB")
    assert out["meta"]["status"] == "fresh"
    assert out["data"]["engine"] == "GEV"
    assert "LSTM" in out["data"]["not"]


@pytest.mark.unit
def test_recommend_engine_picks_lstm_for_short_horizon():
    out = recommend_engine("vai alagar nas próximas 12 horas no centro?")
    assert out["data"]["engine"].startswith("LSTM")


@pytest.mark.unit
def test_siren_protocol_is_documented_not_live_rain():
    out = siren_protocol()
    assert out["data"]["rain_1h_mm"] == 40.0
    assert out["data"]["rain_24h_mm"] == 125.0
    assert out["meta"]["live_rainfall"] is False


@pytest.mark.unit
def test_compare_to_siren_flags_threshold():
    out = compare_to_siren(rain_1h_mm=42, rain_24h_mm=10)
    assert out["data"]["triggers_1h"] is True
    assert out["data"]["triggers_24h"] is False


@pytest.mark.unit
def test_resolve_place_guandu():
    out = resolve_place("ETA Guandu")
    assert out["meta"]["status"] == "fresh"
    assert out["data"]["latitude"] < 0
    assert out["data"]["longitude"] < 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_unknown_tool_is_unavailable():
    out = await execute_tool("invent_rainfall", {})
    assert out["meta"]["status"] == "unavailable"
    assert out["meta"]["unavailable"] is True
    assert out["data"] is None


@pytest.mark.unit
def test_recommend_engine_picks_sar_for_reservoir():
    out = recommend_engine("qual o volume útil do Funil e do equivalente Paraíba?")
    assert "SAR" in out["data"]["engine"]


@pytest.mark.unit
def test_parse_sar_sin_table_reads_funil_row():
    html = """
    <table><tbody><tr>
      <td>19093</td><td>FUNIL</td><td>453,48</td><td>185,47</td><td>171,00</td>
      <td>0,00</td><td>171,00</td><td>75,03</td><td>31,63</td><td>44,22</td>
      <td>27/08/2026</td>
    </tr></tbody></table>
    """
    rows = parse_sar_sin_table(html)
    assert len(rows) == 1
    assert rows[0]["code"] == "19093"
    assert rows[0]["useful_volume_pct"] == 31.63
    assert rows[0]["measured_on"] == "2026-08-27"


@pytest.mark.unit
def test_fetch_paraiba_reservoirs_builds_equivalent(monkeypatch):
    html = """
    <tr><td>19093</td><td>FUNIL</td><td>453,48</td><td>185,47</td><td>171,00</td>
    <td>0,00</td><td>171,00</td><td>75,03</td><td>40,00</td><td>44,22</td>
    <td>27/08/2026</td></tr>
    """
    monkeypatch.setattr(tools, "_fetch_sar_html", lambda *a, **k: html)
    tools._SAR_CACHE["at"] = None
    tools._SAR_CACHE["payload"] = None
    out = tools.fetch_paraiba_reservoirs(lookback_days=5)
    assert out["meta"]["status"] == "fresh"
    assert out["data"]["equivalent_useful_volume_pct"] == 40.0
    assert len(out["data"]["reservoirs"]) == 4
    assert out["meta"]["source"].startswith("ANA SAR")


@pytest.mark.unit
def test_poseidon_status_requires_auth(client: TestClient):
    response = client.get("/api/v1/poseidon/status")
    assert response.status_code == 401


@pytest.mark.unit
def test_poseidon_chat_503_when_ollama_down(authenticated_client: TestClient):
    with patch(
        "api.poseidon.chat",
        side_effect=RuntimeError("Ollama indisponível em http://127.0.0.1:11434"),
    ):
        response = authenticated_client.post(
            "/api/v1/poseidon/chat",
            json={"messages": [{"role": "user", "content": "olá"}]},
        )
    assert response.status_code == 503
    assert "Ollama" in response.json()["detail"]

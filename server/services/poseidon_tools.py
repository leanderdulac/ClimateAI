"""Tools Poseidon may call. Every observation uses a {data, meta} envelope."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lib.partner_contract import envelope

logger = logging.getLogger(__name__)

PLACES: Dict[str, Dict[str, Any]] = {
    "rio": {"latitude": -22.9068, "longitude": -43.1729, "label": "Rio de Janeiro (centro)"},
    "guandu": {"latitude": -22.759, "longitude": -43.451, "label": "ETA Guandu, Nova Iguaçu"},
    "funil": {"latitude": -22.529, "longitude": -44.568, "label": "UHE Funil / Paraíba do Sul"},
}

# ANA SAR / SIN codes (dropdown MedicaoSin) and useful capacity (CEIVAP, hm³).
PARAIBA_RESERVOIRS = {
    "paraibuna": {"code": "19090", "name": "PARAIBUNA", "useful_hm3": 2636.1, "share": 0.607},
    "santa_branca": {"code": "19091", "name": "SANTA BRANCA", "useful_hm3": 308.0, "share": 0.071},
    "jaguari": {"code": "19092", "name": "JAGUARI", "useful_hm3": 792.5, "share": 0.183},
    "funil": {"code": "19093", "name": "FUNIL", "useful_hm3": 605.3, "share": 0.139},
}
EQUIVALENT_USEFUL_HM3 = 4341.9
_SAR_CACHE: Dict[str, Any] = {"at": None, "payload": None}
_SAR_TTL = timedelta(hours=6)

SIREN_A2C2 = {
    "rain_1h_mm": 40.0,
    "rain_24h_mm": 125.0,
    "source": "GEO-RIO / Alerta Rio — Sistema A2C2",
    "intensity_mm_h": {
        "fraca": "< 5",
        "moderada": "5–25",
        "forte": "25–50",
        "muito_forte": "> 50",
    },
}

OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "resolve_place",
            "description": "Resolve um nome (rio, guandu, funil) para latitude/longitude.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Tempo atual observado (Open-Meteo) em um ponto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_forecast",
            "description": "Previsão diária 1–16 dias (Open-Meteo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "days": {"type": "integer", "minimum": 1, "maximum": 16},
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_history",
            "description": "Histórico diário de arquivo Open-Meteo (temp, chuva, pressão, vento).",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "days": {"type": "integer", "minimum": 14, "maximum": 730},
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_enso",
            "description": "Snapshot ENSO ao vivo (ONI/RONI da NOAA CPC).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_engine",
            "description": "Escolhe o motor ClimateWise adequado à pergunta (LSTM, GEV, HMM, SPI…).",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "siren_protocol",
            "description": "Limiares documentados das sirenes A2C2 / Alerta Rio (não é chuva ao vivo).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_to_siren",
            "description": "Compara chuva observada (mm) com os limiares A2C2 de 1 h e 24 h.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rain_1h_mm": {"type": "number"},
                    "rain_24h_mm": {"type": "number"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_alerta_rio_stations",
            "description": "Tenta pluviômetros ao vivo do Alerta Rio. Se falhar, o envelope vem unavailable — use siren_protocol.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_paraiba_reservoirs",
            "description": "Volume útil observado (ANA SAR) de Paraibuna, Jaguari, Funil e Santa Branca, mais o reservatório equivalente da bacia do Paraíba do Sul.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _unavailable(reason: str, license_key: str = "climatewise") -> Dict[str, Any]:
    return envelope(
        None,
        source="Poseidon tools",
        license_key=license_key,
        status="unavailable",
        stale=True,
        extra_meta={"reason": reason},
    )


def recommend_engine(question: str) -> Dict[str, Any]:
    q = (question or "").lower()
    if any(k in q for k in ("50 anos", "100 anos", "período de retorno", "pmsb", "drenagem", "galeria")):
        choice = {
            "engine": "GEV",
            "also": "GPD/POT se a pergunta for pico acima de limiar",
            "why": "Período de retorno é cauda de máximos de bloco, não previsão de amanhã.",
            "not": "LSTM",
        }
    elif any(k in q for k in ("turbidez", "eta", "água bruta", "tratabilidade")):
        choice = {
            "engine": "GPD/POT",
            "why": "A ETA reage a pico que passa do limiar, não à média do mês.",
            "not": "HMM",
        }
    elif any(k in q for k in ("reservat", "volume útil", "volume util", "funil", "paraíba", "paraiba do sul", "sar")):
        choice = {
            "engine": "ANA SAR (observado) + HMM/SPI para regime",
            "why": "A cota e o % de volume útil vêm da medição ANA, não de modelo. HMM/SPI só classificam o regime.",
            "not": "LSTM nem número inventado de VU",
        }
    elif any(k in q for k in ("estiagem", "seca", "raciona", "spi", "spei", "3 meses", "sazonal")):
        choice = {
            "engine": "HMM + SPI/SPEI + ENSO",
            "why": "Estiagem é mudança de regime em meses; SPI é a língua oficial do INMET.",
            "not": "LSTM de 24 h",
        }
    elif any(k in q for k in ("el nino", "el niño", "la nina", "la niña", "enso", "oni")):
        choice = {
            "engine": "ENSO ONI/RONI",
            "why": "Forçante sazonal observado pela NOAA CPC.",
            "not": "GEV",
        }
    elif any(k in q for k in ("bairro", "onde agir", "encosta", "cluster", "mapa")):
        choice = {
            "engine": "KDE + DBSCAN",
            "why": "Ação é geográfica; um único pluviômetro não localiza o cluster.",
            "not": "só a média municipal",
        }
    elif any(k in q for k in ("sirene", "a2c2", "alerta rio", "40 mm")):
        choice = {
            "engine": "gatilho paramétrico",
            "why": "O SOP da cidade já é limiar: 40 mm/1 h ou 125 mm/24 h.",
            "not": "GEV de 50 anos",
        }
    else:
        choice = {
            "engine": "LSTM + atenção",
            "why": "Horizonte tático 6–48 h com as variáveis da estação.",
            "not": "GEV",
        }
    return envelope(choice, source="ClimateWise engine map", license_key="climatewise", status="fresh")


def siren_protocol() -> Dict[str, Any]:
    return envelope(
        dict(SIREN_A2C2),
        source="GEO-RIO / Alerta Rio A2C2 (protocolo documentado)",
        license_key="climatewise",
        status="fresh",
        extra_meta={"kind": "protocol_constant", "live_rainfall": False},
    )


def compare_to_siren(rain_1h_mm: Optional[float] = None, rain_24h_mm: Optional[float] = None) -> Dict[str, Any]:
    if rain_1h_mm is None and rain_24h_mm is None:
        return _unavailable("Informe rain_1h_mm e/ou rain_24h_mm observados.")
    data = {
        "thresholds": SIREN_A2C2,
        "rain_1h_mm": rain_1h_mm,
        "rain_24h_mm": rain_24h_mm,
        "triggers_1h": rain_1h_mm is not None and float(rain_1h_mm) >= SIREN_A2C2["rain_1h_mm"],
        "triggers_24h": rain_24h_mm is not None and float(rain_24h_mm) >= SIREN_A2C2["rain_24h_mm"],
    }
    return envelope(
        data,
        source="Comparação com limiar A2C2 documentado",
        license_key="climatewise",
        status="fresh",
        extra_meta={"kind": "protocol_comparison"},
    )


def resolve_place(name: str) -> Dict[str, Any]:
    key = (name or "").strip().lower()
    aliases = {
        "rio de janeiro": "rio",
        "cidade do rio": "rio",
        "eta guandu": "guandu",
        "guandu": "guandu",
        "nova iguacu": "guandu",
        "nova iguaçu": "guandu",
        "funil": "funil",
        "paraiba": "funil",
        "paraíba": "funil",
    }
    slug = aliases.get(key, key)
    place = PLACES.get(slug)
    if not place:
        return _unavailable(f"Lugar desconhecido: {name}. Use rio, guandu ou funil, ou passe lat/lon.")
    return envelope(place, source="ClimateWise place registry", license_key="climatewise", status="fresh")


async def get_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    from services.climate_data_service import get_climate_data_service

    weather = await get_climate_data_service().fetch_current_weather(float(latitude), float(longitude))
    if not weather:
        return _unavailable("Tempo atual indisponível (Open-Meteo)", "open-meteo")
    return envelope(
        asdict(weather),
        source="Open-Meteo",
        license_key="open-meteo",
        status="fresh",
        observed_at=weather.timestamp or None,
    )


async def get_forecast(latitude: float, longitude: float, days: int = 7) -> Dict[str, Any]:
    from services.climate_data_service import get_climate_data_service

    days = max(1, min(16, int(days or 7)))
    forecast = await get_climate_data_service().fetch_daily_forecast(float(latitude), float(longitude), days)
    if not forecast:
        return _unavailable("Previsão indisponível (Open-Meteo)", "open-meteo")
    return envelope(
        {"latitude": latitude, "longitude": longitude, "days": days, "daily": forecast},
        source="Open-Meteo forecast",
        license_key="open-meteo",
        status="fresh",
    )


async def get_history(latitude: float, longitude: float, days: int = 90) -> Dict[str, Any]:
    import asyncio

    from services.pytorch_climate_pricing_service import fetch_openmeteo_daily_archive

    days = max(14, min(730, int(days or 90)))
    try:
        archive = await asyncio.to_thread(
            fetch_openmeteo_daily_archive, float(latitude), float(longitude), days
        )
    except Exception as exc:
        logger.warning("Poseidon history failed: %s", exc)
        return _unavailable("Histórico indisponível (Open-Meteo archive)", "open-meteo")
    n = int(archive.get("n_obs") or 0)
    sample = []
    dates = archive.get("dates") or []
    precip = archive.get("precipitation") or []
    temp = archive.get("temperature") or []
    for i in (0, max(0, n // 2), max(0, n - 1)):
        if i < n:
            sample.append(
                {
                    "date": dates[i],
                    "temperature": temp[i],
                    "precipitation": precip[i],
                }
            )
    payload = {
        "latitude": latitude,
        "longitude": longitude,
        "n_obs": n,
        "start": archive.get("start"),
        "end": archive.get("end"),
        "sample": sample,
        "precip_sum_mm": round(float(sum(precip[:n])), 1) if n else None,
    }
    return envelope(payload, source="Open-Meteo archive", license_key="open-meteo", status="fresh")


async def get_enso() -> Dict[str, Any]:
    from services.enso_service import ENSOService

    try:
        snap = await ENSOService().get_latest_snapshot()
    except Exception as exc:
        logger.warning("Poseidon ENSO failed: %s", exc)
        return _unavailable("ENSO indisponível (NOAA CPC)")
    return envelope(snap, source="NOAA CPC ONI/RONI", license_key="climatewise", status="fresh")


def _br_float(text: str) -> Optional[float]:
    cleaned = (text or "").strip().replace(".", "").replace(",", ".")
    if not cleaned or cleaned in {"-", "--"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _strip_html(cell: str) -> str:
    text = re.sub(r"<[^>]+>", " ", cell)
    return " ".join(text.split())


def parse_sar_sin_table(html: str) -> List[Dict[str, Any]]:
    """Parse ANA SAR MedicaoSin HTML table into measurement dicts."""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.I | re.S)
    measurements: List[Dict[str, Any]] = []
    for row in rows:
        cells = [_strip_html(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.I | re.S)]
        if len(cells) < 11:
            continue
        measured = None
        date_text = cells[-1]
        try:
            measured = datetime.strptime(date_text, "%d/%m/%Y").date().isoformat()
        except ValueError:
            continue
        vu = _br_float(cells[8])
        measurements.append(
            {
                "code": cells[0],
                "name": cells[1],
                "level_m": _br_float(cells[2]),
                "inflow_m3s": _br_float(cells[3]),
                "outflow_m3s": _br_float(cells[4]),
                "useful_volume_pct": vu,
                "measured_on": measured,
            }
        )
    measurements.sort(key=lambda item: item["measured_on"])
    return measurements


def _fetch_sar_html(code: str, start: date, end: date) -> str:
    params = {
        "dropDownListEstados": "",
        "dropDownListReservatorios": code,
        "dataInicial": start.strftime("%d/%m/%Y"),
        "dataFinal": end.strftime("%d/%m/%Y"),
        "button": "Buscar",
    }
    url = "https://www.ana.gov.br/sar0/MedicaoSin?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "ClimateWise-Poseidon/1.0"})
    with urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch_paraiba_reservoirs(lookback_days: int = 10) -> Dict[str, Any]:
    """Latest ANA SAR observation per Paraíba reservoir + equivalent VU %."""
    now = datetime.now(timezone.utc)
    cached_at = _SAR_CACHE.get("at")
    if cached_at and _SAR_CACHE.get("payload") and now - cached_at < _SAR_TTL:
        return _SAR_CACHE["payload"]

    end = date.today()
    start = end - timedelta(days=max(3, lookback_days))
    latest: List[Dict[str, Any]] = []
    errors: List[str] = []
    for slug, spec in PARAIBA_RESERVOIRS.items():
        try:
            html = _fetch_sar_html(spec["code"], start, end)
            rows = parse_sar_sin_table(html)
        except Exception as exc:
            errors.append(f"{spec['name']}: {exc}")
            continue
        if not rows:
            errors.append(f"{spec['name']}: tabela vazia")
            continue
        row = rows[-1]
        vu = row["useful_volume_pct"]
        stored = None if vu is None else round(vu / 100.0 * spec["useful_hm3"], 2)
        latest.append(
            {
                "id": slug,
                "code": spec["code"],
                "name": spec["name"],
                "useful_capacity_hm3": spec["useful_hm3"],
                "useful_volume_pct": vu,
                "useful_stored_hm3": stored,
                "level_m": row["level_m"],
                "inflow_m3s": row["inflow_m3s"],
                "outflow_m3s": row["outflow_m3s"],
                "measured_on": row["measured_on"],
            }
        )

    if not latest:
        return _unavailable(
            "ANA SAR não devolveu medições do Paraíba do Sul. " + "; ".join(errors)
        )

    stored_sum = sum(item["useful_stored_hm3"] or 0.0 for item in latest)
    capacity_sum = sum(item["useful_capacity_hm3"] for item in latest)
    equivalent_pct = round(100.0 * stored_sum / capacity_sum, 2) if capacity_sum else None
    observed = max(item["measured_on"] for item in latest)
    payload = envelope(
        {
            "basin": "Paraíba do Sul",
            "equivalent_useful_capacity_hm3": EQUIVALENT_USEFUL_HM3,
            "equivalent_useful_volume_pct": equivalent_pct,
            "equivalent_stored_hm3": round(stored_sum, 2),
            "reservoirs": latest,
            "notes": errors,
        },
        source="ANA SAR MedicaoSin (SIN)",
        license_key="climatewise",
        status="fresh",
        observed_at=f"{observed}T00:00:00Z",
        extra_meta={
            "lookback_days": lookback_days,
            "capacity_source": "CEIVAP (volume útil de projeto)",
        },
    )
    _SAR_CACHE["at"] = now
    _SAR_CACHE["payload"] = payload
    return payload


def get_paraiba_reservoirs() -> Dict[str, Any]:
    return fetch_paraiba_reservoirs()


def get_alerta_rio_stations() -> Dict[str, Any]:
    """Best-effort live stations. Protocol thresholds live in siren_protocol()."""
    url = "https://api.dados.rio/v2/clima_pluviometro/precipitacao_15min/"
    try:
        req = Request(url, headers={"User-Agent": "ClimateWise-Poseidon/1.0"})
        with urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read().decode())
        return envelope(
            raw if isinstance(raw, dict) else {"stations": raw},
            source="dados.rio / Alerta Rio",
            license_key="climatewise",
            status="fresh",
        )
    except Exception as exc:
        logger.info("Alerta Rio live feed unavailable: %s", exc)
        return _unavailable(
            "Pluviômetros ao vivo do Alerta Rio indisponíveis. Use siren_protocol para os limiares A2C2 e get_current_weather para chuva observada no ponto."
        )


HANDLERS: Dict[str, Callable[..., Any]] = {
    "resolve_place": resolve_place,
    "get_current_weather": get_current_weather,
    "get_forecast": get_forecast,
    "get_history": get_history,
    "get_enso": get_enso,
    "recommend_engine": recommend_engine,
    "siren_protocol": siren_protocol,
    "compare_to_siren": compare_to_siren,
    "get_alerta_rio_stations": get_alerta_rio_stations,
    "get_paraiba_reservoirs": get_paraiba_reservoirs,
}


async def execute_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    args = arguments or {}
    handler = HANDLERS.get(name)
    if handler is None:
        return _unavailable(f"Ferramenta desconhecida: {name}")
    try:
        result = handler(**args)
        if hasattr(result, "__await__"):
            result = await result  # type: ignore[misc]
        if not isinstance(result, dict) or "meta" not in result:
            return _unavailable("Ferramenta não devolveu envelope")
        return result
    except TypeError as exc:
        return _unavailable(f"Argumentos inválidos para {name}: {exc}")
    except Exception as exc:
        logger.warning("Tool %s failed: %s", name, exc)
        return _unavailable(f"{name} falhou: {exc}")

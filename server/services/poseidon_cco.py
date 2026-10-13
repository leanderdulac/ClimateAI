"""CEDAE command-center domain, advisory models, and fixture store.

Every payload is a {data, meta} envelope. meta.live is always False for
CEDAE telemetry — this module never invents live SCADA readings.
Ollama/Grok/Gemini are not on the write/control path.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from lib.partner_contract import envelope, utc_now
from services.poseidon_tools import PLACES, execute_tool, get_current_weather

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "Dados de demonstração — não é telemetria CEDAE ao vivo. "
    "IA advisory; SCADA permanece o comando."
)

# ---------------------------------------------------------------------------
# Domain fixtures (documented assumptions, not live CEDAE)
# ---------------------------------------------------------------------------

GUANDU_CAPACITY_L_S = 45000
GUANDU_SCENARIO_50 = {
    "id": "guandu-50-2026-07-21",
    "at": "2026-07-21T18:00:00-03:00",
    "production_fraction": 0.5,
    "note": (
        "Cenário de 50% da produção em 21/07/2026 18h. "
        "Não é leitura ao vivo."
    ),
}

NOVO_GUANDU = {
    "id": "novo_guandu",
    "name": "Novo Guandu",
    "role": "redundancia_virtual",
    "planned": "2030-03",
    "status": "planejado",
    "online": False,
    "notes": (
        "Redundância prevista para março de 2030. No cenário de 50% o CCO "
        "trata o Novo Guandu como capacidade virtual ainda indisponível."
    ),
}

# Assumed shares of Guandu production delivered to concessionaires.
# Documented fixtures — not billed volumes from CEDAE.
CONCESSIONAIRES: List[Dict[str, Any]] = [
    {
        "id": "aguas_do_rio",
        "name": "Águas do Rio",
        "blocks": ["1", "4"],
        "guandu_share": 0.68,
        "share_note": "Fixture: 68% da produção Guandu (blocos 1+4).",
        "municipalities": [
            "Rio de Janeiro (Centro, Zona Sul, Zona Norte, Ilha)",
            "Nova Iguaçu",
            "Nilópolis",
            "Mesquita",
            "São João de Meriti",
            "Belford Roxo",
            "Queimados",
            "Japeri",
            "Paracambi",
            "Seropédica",
            "Itaguaí",
        ],
    },
    {
        "id": "igua",
        "name": "Iguá",
        "blocks": ["2"],
        "guandu_share": 0.17,
        "share_note": "Fixture: 17% da produção Guandu (bloco 2).",
        "municipalities": [
            "Rio de Janeiro (Barra da Tijuca, Recreio, Jacarepaguá, Vargens)",
        ],
    },
    {
        "id": "rio_mais",
        "name": "Rio+",
        "blocks": ["3"],
        "guandu_share": 0.15,
        "share_note": "Fixture: 15% da produção Guandu (bloco 3).",
        "municipalities": [
            "Rio de Janeiro (Campo Grande, Santa Cruz, Bangu, Realengo)",
        ],
    },
]

SYSTEMS: List[Dict[str, Any]] = [
    {
        "id": "guandu",
        "name": "ETA Guandu",
        "kind": "eta",
        "capacity_l_s": GUANDU_CAPACITY_L_S,
        "production_l_s": 43200,
        "share_rm_pct": 80,
        "population": 9_000_000,
        "lat": PLACES["guandu"]["latitude"],
        "lon": PLACES["guandu"]["longitude"],
        "municipality": "Nova Iguaçu",
        "notes": (
            "Maior ETA em volume (~45.000 L/s; ~80% da RM; >9 milhões). "
            "Coordenadas iguais ao registry PLACES. Produção é fixture."
        ),
    },
    {
        "id": "imunana_laranjal",
        "name": "Imunana-Laranjal",
        "kind": "eta",
        "capacity_l_s": 7000,
        "production_l_s": 6500,
        "share_rm_pct": None,
        "population": 2_000_000,
        "lat": -22.72,
        "lon": -43.05,
        "municipality": "São Gonçalo / Niterói",
        "notes": "Leste da RM (~2 milhões). Capacidade e produção são fixtures.",
    },
    {
        "id": "lajes",
        "name": "Sistema Lajes",
        "kind": "manancial",
        "capacity_l_s": 4000,
        "production_l_s": 3600,
        "population": 500_000,
        "lat": -22.70,
        "lon": -43.87,
        "municipality": "Piraí / Rio Claro",
        "notes": "Manancial Lajes (fixture). Alimenta o complexo Guandu.",
    },
    {
        "id": "acari",
        "name": "Sistema Acari",
        "kind": "eta",
        "capacity_l_s": 1500,
        "production_l_s": 1200,
        "population": 250_000,
        "lat": -22.83,
        "lon": -43.34,
        "municipality": "Rio de Janeiro",
        "notes": "Sistema local Acari (capacidade fixture).",
    },
    {
        "id": "campos_eliseos",
        "name": "Campos Elíseos",
        "kind": "eta",
        "capacity_l_s": 2500,
        "production_l_s": 2100,
        "population": 400_000,
        "lat": -22.70,
        "lon": -43.29,
        "municipality": "Duque de Caxias",
        "notes": "ETA Campos Elíseos (capacidade fixture).",
    },
    {
        "id": "japeri",
        "name": "Sistema Japeri",
        "kind": "eta",
        "capacity_l_s": 800,
        "production_l_s": 650,
        "population": 120_000,
        "lat": -22.643,
        "lon": -43.653,
        "municipality": "Japeri",
        "notes": "Sistema Japeri (capacidade fixture).",
    },
]

DELIVERY_POINTS: List[Dict[str, Any]] = [
    {
        "id": "adutora_guandu_rj",
        "name": "Adutora Guandu → Rio",
        "kind": "adutora",
        "lat": -22.85,
        "lon": -43.40,
        "feeds": "Águas do Rio / Iguá / Rio+",
    },
    {
        "id": "entrega_aguas_do_rio",
        "name": "Ponto de entrega Águas do Rio",
        "kind": "entrega",
        "lat": -22.91,
        "lon": -43.20,
        "concessionaire": "aguas_do_rio",
    },
    {
        "id": "entrega_igua",
        "name": "Ponto de entrega Iguá",
        "kind": "entrega",
        "lat": -23.00,
        "lon": -43.37,
        "concessionaire": "igua",
    },
    {
        "id": "entrega_rio_mais",
        "name": "Ponto de entrega Rio+",
        "kind": "entrega",
        "lat": -22.90,
        "lon": -43.55,
        "concessionaire": "rio_mais",
    },
]

CMA = {
    "id": "cma_botafogo",
    "name": "CMA Botafogo",
    "opened": "2026-06-09",
    "lat": -22.951,
    "lon": -43.191,
    "cameras": 36,
    "points": 14,
    "cameras_online_fixture": 36,
    "status": "fixture",
    "notes": (
        "Centro de Monitoramento Aberto em 09/06/2026. "
        "36 câmeras / 14 pontos — status de fixture, não câmeras ao vivo."
    ),
}

GEOSMINA_THRESHOLDS = {
    "lab_geosmin_alerta_ug_l": 0.02,
    "lab_geosmin_critico_ug_l": 0.1,
    "phycocyanin_proxy_high": 2.0,
    "temp_high_c": 26.0,
    "sensor_online_geosmin_ngl": False,
    "note": (
        "Laudo de laboratório em µg/L (água bruta). "
        "O proxy de ficocianina NÃO é sensor de geosmina em ng/L. "
        "Este CCO nunca afirma sensor online de geosmina."
    ),
}

DEMO_GEOSMINA_INPUTS = {
    "phycocyanin_proxy": 2.6,
    "temp_c": 27.8,
    "low_flow": True,
    "lab_geosmin_ug_l": 0.038,
    "lab_2mib_ug_l": 0.015,
    "kind": "fixture",
    "note": "Entradas de demonstração (bloom de cianobactérias). Não é telemetria.",
}

# Hourly multipliers for a typical urban diurnal production/demand curve.
DIURNAL = [
    0.72, 0.68, 0.65, 0.64, 0.66, 0.74, 0.92, 1.12,
    1.18, 1.10, 1.02, 0.98, 0.96, 0.95, 0.97, 1.00,
    1.05, 1.12, 1.20, 1.18, 1.10, 0.98, 0.88, 0.78,
]

FIXTURE_WEATHER = {
    "temperature": 25.0,
    "rain": 0.0,
    "humidity": 70.0,
    "source": "fixture",
    "live": False,
}

CONNECTOR_SPECS: List[Dict[str, Any]] = [
    {
        "id": "inea",
        "name": "INEA",
        "status": "stub",
        "docs_url": "https://www.inea.rj.gov.br/",
    },
    {
        "id": "alerta_rio",
        "name": "Alerta Rio",
        "status": "live_tool",
        "tool": "get_alerta_rio_stations",
        "tool_args": {},
        "docs_url": "https://alertario.rio.rj.gov.br/",
    },
    {
        "id": "ana_hidroweb",
        "name": "ANA HidroWeb",
        "status": "stub",
        "docs_url": "https://www.snirh.gov.br/hidroweb/",
    },
    {
        "id": "ana_sar",
        "name": "ANA SAR (Paraíba do Sul)",
        "status": "live_tool",
        "tool": "get_paraiba_reservoirs",
        "tool_args": {},
        "docs_url": "https://www.ana.gov.br/sar0/MedicaoSin",
    },
    {
        "id": "cemaden",
        "name": "CEMADEN",
        "status": "stub",
        "docs_url": "https://www.gov.br/cemaden/",
    },
    {
        "id": "inmet",
        "name": "INMET",
        "status": "stub",
        "docs_url": "https://portal.inmet.gov.br/",
    },
    {
        "id": "cptec",
        "name": "CPTEC/INPE",
        "status": "stub",
        "docs_url": "https://www.cptec.inpe.br/",
    },
    {
        "id": "ons",
        "name": "ONS",
        "status": "stub",
        "docs_url": "https://www.ons.org.br/",
    },
    {
        "id": "el_nino",
        "name": "El Niño / ENSO",
        "status": "live_tool",
        "tool": "get_enso",
        "tool_args": {},
        "docs_url": (
            "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/"
            "ensostuff/"
        ),
    },
    {
        "id": "open_meteo",
        "name": "Open-Meteo",
        "status": "live_tool",
        "tool": "get_current_weather",
        "tool_args": {
            "latitude": PLACES["guandu"]["latitude"],
            "longitude": PLACES["guandu"]["longitude"],
        },
        "docs_url": "https://open-meteo.com/",
    },
]

_LEVEL_RANK = {"normal": 0, "advisory": 1, "alerta": 2, "critico": 3}

_incidents: List[Dict[str, Any]] = []
_psa: Dict[str, Any] = {}
_last_geosmina: Optional[Dict[str, Any]] = None
_last_outage: Optional[Dict[str, Any]] = None
_last_demanda: Optional[Dict[str, Any]] = None


def _default_psa() -> Dict[str, Any]:
    return {
        "level": "normal",
        "components": {
            "geosmina": "normal",
            "oferta": "normal",
            "demanda": "normal",
        },
        "updated_at": utc_now(),
        "disclaimer": DISCLAIMER,
    }


def reset_cco_state() -> None:
    """Clear in-memory incidents and PSA (tests + process start)."""
    global _incidents, _psa, _last_geosmina, _last_outage, _last_demanda
    _incidents = []
    _psa = _default_psa()
    _last_geosmina = None
    _last_outage = None
    _last_demanda = None


reset_cco_state()


def _fx(
    data: Any,
    source: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta = {"live": False, "kind": "fixture", "disclaimer": DISCLAIMER}
    if extra:
        meta.update(extra)
    return envelope(
        data,
        source=source,
        license_key="climatewise",
        status="fresh",
        extra_meta=meta,
    )


def clamp_horizon(horizonte_h: Any, default: int = 24) -> int:
    try:
        value = int(horizonte_h)
    except (TypeError, ValueError):
        value = default
    return max(1, min(48, value))


def _sop_geosmina(level: str) -> List[str]:
    steps = [
        (
            "Confirmar o laudo de laboratório em água bruta "
            "(geosmina / 2-MIB em µg/L). Não há sensor online de geosmina "
            "em ng/L neste CCO."
        ),
        (
            "Intensificar o monitoramento de cianobactérias "
            "(proxy de ficocianina + microscopia), sem tratar o proxy "
            "como concentração de geosmina."
        ),
        (
            "Avaliar carvão ativado pulverizado (CAP) e a dosagem de PAC "
            "na ETA Guandu conforme o SOP da estação."
        ),
        (
            "Notificar Águas do Rio, Iguá e Rio+ sobre risco de gosto/odor. "
            "Não afirmar risco sanitário sem laudo de água tratada."
        ),
        (
            "Registrar o evento no PSA. Este modelo é advisory; "
            "o SCADA permanece o comando."
        ),
    ]
    if level == "critico":
        steps.append(
            "Elevar o PSA para crítico. Comunicar a reguladora e as "
            "prefeituras abastecidas. Avaliar restrição de produção se o "
            "tratamento não abater o odor."
        )
    return steps


def evaluate_geosmina(
    phycocyanin_proxy: Optional[float] = None,
    temp_c: Optional[float] = None,
    low_flow: bool = False,
    lab_geosmin_ug_l: Optional[float] = None,
    lab_2mib_ug_l: Optional[float] = None,
) -> Dict[str, Any]:
    """Advisory geosmin / 2-MIB rules. Never claims an online ng/L sensor."""
    thr = GEOSMINA_THRESHOLDS
    lab = float(lab_geosmin_ug_l or 0.0)
    proxy = float(phycocyanin_proxy) if phycocyanin_proxy is not None else None
    temp = float(temp_c) if temp_c is not None else None
    high_proxy = proxy is not None and proxy >= thr["phycocyanin_proxy_high"]
    high_temp = temp is not None and temp >= thr["temp_high_c"]
    lab_alerta = lab >= thr["lab_geosmin_alerta_ug_l"]
    lab_critico = lab >= thr["lab_geosmin_critico_ug_l"]
    bloom_proxy = bool(high_proxy and high_temp and low_flow)
    proxy_and_lab = bool(high_proxy and lab_alerta)

    reasons: List[str] = []
    if lab_critico:
        reasons.append(
            f"Laudo de geosmina {lab} µg/L ≥ "
            f"{thr['lab_geosmin_critico_ug_l']} µg/L (crítico)."
        )
    if proxy_and_lab:
        reasons.append(
            "Proxy de ficocianina elevado e laudo de geosmina elevado."
        )
    if lab_alerta and not lab_critico:
        reasons.append(
            f"Laudo de geosmina {lab} µg/L ≥ "
            f"{thr['lab_geosmin_alerta_ug_l']} µg/L (alerta, água bruta)."
        )
    if bloom_proxy:
        reasons.append(
            "Proxy alto + temperatura alta + vazão baixa "
            "(condição de bloom, sem sensor de geosmina)."
        )

    if lab_critico or proxy_and_lab:
        level = "critico"
    elif lab_alerta or bloom_proxy:
        level = "alerta"
    else:
        level = "normal"
        reasons.append("Abaixo dos limiares de alerta (fixture / laudo).")

    return {
        "level": level,
        "reasons": reasons,
        "inputs": {
            "phycocyanin_proxy": phycocyanin_proxy,
            "temp_c": temp_c,
            "low_flow": bool(low_flow),
            "lab_geosmin_ug_l": lab_geosmin_ug_l,
            "lab_2mib_ug_l": lab_2mib_ug_l,
            "kind": "fixture_or_lab",
        },
        "thresholds": dict(thr),
        "psa": {
            "component": "geosmina",
            "level": level,
            "plan": "Plano de Segurança da Água — palatabilidade / odor.",
        },
        "sop": _sop_geosmina(level),
        "sensor_online_geosmin_ngl": False,
        "note": thr["note"],
        "advisory": True,
    }


def allocate_guandu_outage(production_fraction: float = 0.5) -> Dict[str, Any]:
    """Split remaining Guandu production by fixture concessionaire shares."""
    frac = max(0.0, min(1.0, float(production_fraction)))
    remaining = round(GUANDU_CAPACITY_L_S * frac, 2)
    allocations: List[Dict[str, Any]] = []
    at_risk: List[Dict[str, Any]] = []
    for conc in CONCESSIONAIRES:
        share = float(conc["guandu_share"])
        nominal = round(GUANDU_CAPACITY_L_S * share, 2)
        remaining_share = round(remaining * share, 2)
        deficit = round(nominal - remaining_share, 2)
        row = {
            "id": conc["id"],
            "name": conc["name"],
            "blocks": list(conc["blocks"]),
            "guandu_share": share,
            "share_note": conc["share_note"],
            "nominal_l_s": nominal,
            "remaining_l_s": remaining_share,
            "deficit_l_s": deficit,
            "municipalities": list(conc["municipalities"]),
        }
        allocations.append(row)
        if deficit > 0:
            at_risk.append(
                {
                    "concessionaire": conc["name"],
                    "blocks": list(conc["blocks"]),
                    "deficit_l_s": deficit,
                    "municipalities": list(conc["municipalities"]),
                }
            )

    level = "normal"
    if frac <= 0.5:
        level = "critico"
    elif frac < 1.0:
        level = "alerta"

    return {
        "model": "guandu_outage",
        "production_fraction": frac,
        "capacity_l_s": GUANDU_CAPACITY_L_S,
        "remaining_l_s": remaining,
        "allocations": allocations,
        "at_risk": at_risk,
        "scenario": dict(GUANDU_SCENARIO_50),
        "novo_guandu": dict(NOVO_GUANDU),
        "virtual_novo_guandu": {
            "online": False,
            "planned": NOVO_GUANDU["planned"],
            "note": (
                "Virtual Novo Guandu: redundância ainda não disponível "
                "(mar/2030). Não soma capacidade neste cenário."
            ),
        },
        "level": level,
        "advisory": True,
        "disclaimer": DISCLAIMER,
    }


def forecast_demanda(
    horizonte_h: Any = 24,
    weather: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """1–48 h advisory production (L/s) from diurnal curve + weather."""
    hours = clamp_horizon(horizonte_h)
    wx = dict(FIXTURE_WEATHER if weather is None else weather)
    temp = float(wx.get("temperature") or 25.0)
    rain = float(wx.get("rain") or 0.0)
    weather_factor = 1.0 + 0.008 * (temp - 24.0) - 0.02 * min(rain, 10.0) / 10.0
    start = now or datetime.now(timezone.utc)
    series: List[Dict[str, Any]] = []
    by_system: Dict[str, List[Dict[str, Any]]] = {s["id"]: [] for s in SYSTEMS}

    for offset in range(hours):
        ts = start + timedelta(hours=offset)
        # America/Sao_Paulo is UTC-3 (no DST since 2019).
        local_hour = (ts.hour - 3) % 24
        diurnal = DIURNAL[local_hour]
        band_frac = 0.08 + 0.02 * abs(weather_factor - 1.0)
        hour_row: Dict[str, Any] = {
            "offset_h": offset,
            "at": ts.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "local_hour": local_hour,
            "diurnal": diurnal,
            "systems": {},
        }
        for system in SYSTEMS:
            base = float(system["production_l_s"])
            point = round(base * diurnal * weather_factor, 1)
            band = round(point * band_frac, 1)
            cell = {
                "point_l_s": point,
                "low_l_s": round(max(0.0, point - band), 1),
                "high_l_s": round(point + band, 1),
                "capacity_l_s": system["capacity_l_s"],
            }
            hour_row["systems"][system["id"]] = cell
            by_system[system["id"]].append({"offset_h": offset, **cell})
        series.append(hour_row)

    return {
        "model": "demanda",
        "horizonte_h": hours,
        "horizonte_h_requested": horizonte_h,
        "weather": wx,
        "weather_factor": round(weather_factor, 4),
        "series": series,
        "by_system": by_system,
        "advisory": True,
        "disclaimer": DISCLAIMER,
        "note": (
            "Curva diurna fixture + covariáveis de tempo. "
            "Não é despacho nem telemetria CEDAE."
        ),
    }


def _record_incident(
    *,
    kind: str,
    level: str,
    title: str,
    summary: str,
    playbook: List[str],
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    item = {
        "id": str(uuid.uuid4()),
        "kind": kind,
        "level": level,
        "title": title,
        "summary": summary,
        "playbook": playbook,
        "at": utc_now(),
        "fixture": True,
        "advisory": True,
    }
    if extra:
        item.update(extra)
    _incidents.insert(0, item)
    return item


def _bump_psa(component: str, level: str) -> Dict[str, Any]:
    _psa["components"][component] = level
    overall = "normal"
    for value in _psa["components"].values():
        if _LEVEL_RANK.get(value, 0) > _LEVEL_RANK.get(overall, 0):
            overall = value
    _psa["level"] = overall
    _psa["updated_at"] = utc_now()
    return dict(_psa)


def get_systems() -> Dict[str, Any]:
    return _fx(
        {
            "systems": [dict(item) for item in SYSTEMS],
            "concessionaires": [dict(item) for item in CONCESSIONAIRES],
            "delivery_points": [dict(item) for item in DELIVERY_POINTS],
            "novo_guandu": dict(NOVO_GUANDU),
            "share_assumption": (
                "Parcelas de entrega da produção Guandu são fixtures "
                "(Águas do Rio 68% blocos 1+4, Iguá 17% bloco 2, "
                "Rio+ 15% bloco 3)."
            ),
        },
        "Poseidon CCO systems (fixture)",
    )


def get_cma() -> Dict[str, Any]:
    return _fx(dict(CMA), "Poseidon CCO CMA Botafogo (fixture)")


def get_psa() -> Dict[str, Any]:
    return _fx(
        {
            "psa": dict(_psa),
            "thresholds": dict(GEOSMINA_THRESHOLDS),
            "last_geosmina": _last_geosmina,
            "last_outage": (
                None
                if _last_outage is None
                else {
                    "level": _last_outage.get("level"),
                    "remaining_l_s": _last_outage.get("remaining_l_s"),
                    "production_fraction": _last_outage.get(
                        "production_fraction"
                    ),
                }
            ),
            "sensor_online_geosmin_ngl": False,
        },
        "Poseidon CCO PSA (fixture)",
    )


def get_incidents() -> Dict[str, Any]:
    return _fx(
        {"incidents": list(_incidents), "count": len(_incidents)},
        "Poseidon CCO incidents (in-memory fixture store)",
    )


async def _probe_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return await asyncio.wait_for(
            execute_tool(name, arguments), timeout=2.5
        )
    except Exception as exc:
        logger.info("CCO connector probe %s failed: %s", name, exc)
        return envelope(
            None,
            source=f"Poseidon CCO probe {name}",
            license_key="climatewise",
            status="unavailable",
            extra_meta={"live": False, "reason": str(exc)},
        )


async def list_connectors() -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for spec in CONNECTOR_SPECS:
        row = {
            "id": spec["id"],
            "name": spec["name"],
            "docs_url": spec["docs_url"],
            "status": spec["status"],
        }
        tool = spec.get("tool")
        if tool:
            probe = await _probe_tool(tool, spec.get("tool_args") or {})
            meta = probe.get("meta") or {}
            row["tool"] = tool
            row["probe_status"] = meta.get("status")
            row["probe_source"] = meta.get("source")
            if meta.get("status") == "fresh":
                row["status"] = "live"
            elif spec["status"] == "live_tool":
                row["status"] = "unavailable"
        else:
            row["status"] = "stub"
        items.append(row)
    return _fx(
        {"connectors": items},
        "Poseidon CCO connectors",
        extra={"live": False},
    )


def demo_geosmina(
    inputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    global _last_geosmina
    payload = dict(DEMO_GEOSMINA_INPUTS if inputs is None else inputs)
    evaluation = evaluate_geosmina(
        phycocyanin_proxy=payload.get("phycocyanin_proxy"),
        temp_c=payload.get("temp_c"),
        low_flow=bool(payload.get("low_flow")),
        lab_geosmin_ug_l=payload.get("lab_geosmin_ug_l"),
        lab_2mib_ug_l=payload.get("lab_2mib_ug_l"),
    )
    _last_geosmina = evaluation
    psa = _bump_psa("geosmina", evaluation["level"])
    incident = _record_incident(
        kind="geosmina",
        level=evaluation["level"],
        title="Simulação geosmina / 2-MIB (água bruta)",
        summary=(
            f"Nível {evaluation['level']}. "
            + " ".join(evaluation["reasons"])
        ),
        playbook=evaluation["sop"],
        extra={"inputs": evaluation["inputs"], "scenario": "fixture"},
    )
    return _fx(
        {
            "model": "geosmina",
            "evaluation": evaluation,
            "incident": incident,
            "psa": psa,
        },
        "Poseidon CCO geosmina demo (fixture)",
    )


def demo_guandu_50(production_fraction: float = 0.5) -> Dict[str, Any]:
    global _last_outage
    evaluation = allocate_guandu_outage(production_fraction)
    _last_outage = evaluation
    psa = _bump_psa("oferta", evaluation["level"])
    playbook = [
        "Tratar como cenário (21/07/2026 18h a 50%) — não como leitura ao vivo.",
        "Ratear os 22.500 L/s restantes pelas parcelas fixture das concessionárias.",
        "Acionar Águas do Rio (1+4), Iguá (2) e Rio+ (3) com municípios em risco.",
        (
            "Virtual Novo Guandu: redundância só em mar/2030 — "
            "não há capacidade extra agora."
        ),
        "SCADA permanece o comando. Este CCO é advisory.",
    ]
    remaining = evaluation["remaining_l_s"]
    incident = _record_incident(
        kind="guandu_outage",
        level=evaluation["level"],
        title="Simulação Guandu 50%",
        summary=(
            f"Produção a {evaluation['production_fraction']*100:.0f}% "
            f"({remaining} L/s restantes). Cenário 21/07/2026 18h."
        ),
        playbook=playbook,
        extra={"scenario": evaluation["scenario"]},
    )
    return _fx(
        {
            "model": "guandu_outage",
            "evaluation": evaluation,
            "incident": incident,
            "psa": psa,
        },
        "Poseidon CCO Guandu 50% demo (fixture)",
    )


async def _weather_covariates() -> Dict[str, Any]:
    try:
        out = await asyncio.wait_for(
            get_current_weather(
                float(PLACES["guandu"]["latitude"]),
                float(PLACES["guandu"]["longitude"]),
            ),
            timeout=2.5,
        )
        data = out.get("data") or {}
        meta = out.get("meta") or {}
        if data and not meta.get("unavailable"):
            return {
                "temperature": data.get("temperature"),
                "rain": data.get("rain"),
                "humidity": data.get("humidity"),
                "source": meta.get("source") or "Open-Meteo",
                "live": True,
            }
    except Exception as exc:
        logger.info("CCO demanda weather fallback: %s", exc)
    return dict(FIXTURE_WEATHER)


async def forecast_demanda_envelope(horizonte_h: Any = 24) -> Dict[str, Any]:
    global _last_demanda
    weather = await _weather_covariates()
    evaluation = forecast_demanda(horizonte_h, weather=weather)
    _last_demanda = evaluation
    _bump_psa("demanda", "advisory")
    return _fx(
        evaluation,
        "Poseidon CCO demanda (fixture + weather covariate)",
        extra={
            "live": False,
            "weather_live": bool(weather.get("live")),
        },
    )


__all__ = [
    "CONCESSIONAIRES",
    "GEOSMINA_THRESHOLDS",
    "GUANDU_CAPACITY_L_S",
    "allocate_guandu_outage",
    "clamp_horizon",
    "demo_geosmina",
    "demo_guandu_50",
    "evaluate_geosmina",
    "forecast_demanda",
    "forecast_demanda_envelope",
    "get_cma",
    "get_incidents",
    "get_psa",
    "get_systems",
    "list_connectors",
    "reset_cco_state",
]

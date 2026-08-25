"""Shared contract for the ClimateWise Partner API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

LICENSES: Dict[str, Dict[str, str]] = {
    "open-meteo": {
        "license": "CC BY 4.0 (via Open-Meteo)",
        "attribution": "Weather data by Open-Meteo.com",
        "url": "https://open-meteo.com/en/license",
    },
    "openstreetmap": {
        "license": "ODbL 1.0",
        "attribution": "© OpenStreetMap contributors",
        "url": "https://www.openstreetmap.org/copyright",
    },
    "nasa-gibs": {
        "license": "NASA GIBS public imagery",
        "attribution": "Imagery courtesy NASA EOSDIS GIBS",
        "url": "https://nasa-gibs.github.io/gibs-api-docs/",
    },
    "esri-imagery": {
        "license": "Esri World Imagery terms of use",
        "attribution": "Esri, Maxar, Earthstar Geographics and the GIS User Community",
        "url": "https://www.esri.com/en-us/legal/terms/full-master-agreement",
    },
    "atlas-mdr": {
        "license": "Dados abertos — Atlas Digital de Desastres (MDR)",
        "attribution": "Ministério da Integração e do Desenvolvimento Regional (Brasil)",
        "url": "https://www.gov.br/mdr/pt-br",
    },
    "climatewise": {
        "license": "Contrato de parceria ClimateWise / FIMCE",
        "attribution": "ClimateWise — Framework Integrado de Modelagem Climático-Econômica",
        "url": "https://climatewise.com.br",
    },
}

REFRESH = {
    "current": "15 minutes",
    "forecast": "1 hour",
    "history": "24 hours",
    "atlas": "15 minutes (live) / daily (historical atlas)",
    "pricing": "on demand",
    "agri": "on demand",
    "geo": "static templates",
}

RATE_LIMIT = {
    "requests_per_minute": 60,
    "burst": 20,
    "daily_quota": 10000,
    "header": "X-API-Key",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def envelope(
    data: Any,
    *,
    source: str,
    license_key: str,
    status: str = "fresh",
    stale: bool = False,
    cache_ttl_seconds: int = 900,
    refresh_frequency: Optional[str] = None,
    observed_at: Optional[str] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    generated = utc_now()
    observed = observed_at or generated
    meta: Dict[str, Any] = {
        "updated_at": observed,
        "observed_at": observed,
        "generated_at": generated,
        "source": source,
        "status": status,
        "stale": stale or status == "stale",
        "unavailable": status == "unavailable",
        "cache_ttl_seconds": cache_ttl_seconds,
        "refresh_frequency": refresh_frequency,
        "license": LICENSES.get(license_key, LICENSES["climatewise"]),
    }
    if extra_meta:
        meta.update(extra_meta)
    return {"data": data, "meta": meta}

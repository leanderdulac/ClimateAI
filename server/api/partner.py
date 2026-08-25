"""ClimateWise Partner Integration API.

Machine-to-machine surface for third-party platforms. Authenticate with `X-API-Key`.
Every payload uses the `{data, meta}` envelope (source, timestamps, stale/unavailable, license).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from config.config import settings
from config.database import get_db_session
from lib.partner_contract import LICENSES, RATE_LIMIT, REFRESH, envelope, utc_now
from lib.security import RateLimiter

router = APIRouter(prefix="/partner", tags=["Partner API"])

DEV_PARTNER_KEY = os.getenv("PARTNER_API_KEY", "cw_dev_partner_key")
_partner_limiter = RateLimiter(max_requests=RATE_LIMIT["requests_per_minute"], window_seconds=60)


class PartnerContext(BaseModel):
    id: str
    name: str
    slug: str


class PartnerQuoteRequest(BaseModel):
    asset_value: float = Field(..., gt=0, examples=[250000])
    severity_amount: float = Field(..., gt=0, examples=[40000])
    frequency_pct: float = Field(..., ge=0, le=100, examples=[12])
    coverage_period_years: int = Field(default=1, ge=1, le=20)
    latitude: float = Field(default=-23.55, ge=-90, le=90)
    longitude: float = Field(default=-46.63, ge=-180, le=180)


class PartnerAgriRequest(BaseModel):
    crop_type: str = Field(..., examples=["soybean"])
    phenological_stage: str = Field(..., examples=["flowering"])
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    planning_horizon_days: int = Field(default=120, ge=7, le=365)
    risk_tolerance: str = Field(default="medium")


async def require_partner(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> PartnerContext:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not _partner_limiter.is_allowed(f"partner:{x_api_key[:24]}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Partner rate limit exceeded (60 requests/minute)",
            headers={"Retry-After": "60"},
        )

    env = settings.ENVIRONMENT.lower()
    if x_api_key == DEV_PARTNER_KEY and env != "production":
        return PartnerContext(id="dev", name="Development Partner", slug="dev")

    try:
        from models.sqlalchemy_models import APIKey, Partner
        from sqlalchemy.ext.asyncio import AsyncSession

        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        async for session in get_db_session():
            result = await session.execute(
                select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
            )
            db_key = result.scalars().first()
            if not db_key:
                break
            partner_row = await session.execute(select(Partner).where(Partner.id == db_key.partner_id))
            partner = partner_row.scalars().first()
            if partner and partner.api_enabled:
                request.state.partner = partner
                return PartnerContext(id=partner.id, name=partner.name, slug=partner.slug)
            break
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def _unavailable(reason: str, license_key: str = "climatewise") -> Dict[str, Any]:
    return envelope(
        {"message": reason},
        source="ClimateWise",
        license_key=license_key,
        status="unavailable",
        stale=True,
        cache_ttl_seconds=60,
        refresh_frequency="retry",
    )


# ---------------------------------------------------------------------------
# Catalog (public)
# ---------------------------------------------------------------------------

@router.get(
    "/catalog",
    summary="Partner API catalog",
    description="Public discovery document: base URL, auth, endpoints, geo formats, licenses, rate limits.",
)
async def partner_catalog(request: Request) -> Dict[str, Any]:
    base = str(request.base_url).rstrip("/")
    prefix = f"{base}{os.getenv('API_PREFIX', '/api/v1')}/partner"
    return {
        "name": "ClimateWise Partner API",
        "version": "1.0.0",
        "base_url": prefix,
        "openapi": f"{base}/openapi.json",
        "authentication": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "development_key": None if settings.ENVIRONMENT.lower() == "production" else DEV_PARTNER_KEY,
            "notes": "Production keys are issued as sk_live_* by a ClimateWise admin.",
        },
        "rate_limits": RATE_LIMIT,
        "refresh_frequency": REFRESH,
        "response_envelope": {
            "data": "Domain payload",
            "meta.updated_at": "Observation time (ISO-8601 UTC)",
            "meta.source": "Upstream or ClimateWise engine",
            "meta.status": "fresh | stale | unavailable",
            "meta.stale": "true when cached/fallback data is served",
            "meta.license": "License and attribution for this payload",
        },
        "geo": {
            "feature_format": "GeoJSON Feature / FeatureCollection (RFC 7946)",
            "xyz_tiles": [
                {
                    "id": "osm-standard",
                    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                    "minzoom": 0,
                    "maxzoom": 19,
                    "license": LICENSES["openstreetmap"],
                },
                {
                    "id": "esri-world-imagery",
                    "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                    "minzoom": 0,
                    "maxzoom": 19,
                    "license": LICENSES["esri-imagery"],
                },
            ],
            "wmts": [
                {
                    "id": "nasa-gibs-modis-terra",
                    "url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{Time}/GoogleMapsCompatible_Level9/{TileMatrix}/{TileRow}/{TileCol}.jpg",
                    "license": LICENSES["nasa-gibs"],
                }
            ],
            "wms": None,
            "static_images": "GET /geo/satellite returns a static preview URL per point",
        },
        "endpoints": [
            {"method": "GET", "path": "/catalog", "auth": False, "desc": "This document"},
            {"method": "GET", "path": "/climate/current", "auth": True, "desc": "Current conditions"},
            {"method": "GET", "path": "/climate/forecast", "auth": True, "desc": "Daily forecast"},
            {"method": "GET", "path": "/climate/history", "auth": True, "desc": "Recent history"},
            {"method": "GET", "path": "/analytics/indicators", "auth": True, "desc": "Climate risk indicators"},
            {"method": "GET", "path": "/analytics/extremes", "auth": True, "desc": "Extreme-event signals"},
            {"method": "GET", "path": "/atlas/events", "auth": True, "desc": "Live atlas/oracle events (GeoJSON)"},
            {"method": "GET", "path": "/atlas/risk-summary", "auth": True, "desc": "National risk summary"},
            {"method": "GET", "path": "/geo/layers", "auth": True, "desc": "Map layer catalog"},
            {"method": "GET", "path": "/geo/feature", "auth": True, "desc": "GeoJSON point for a coordinate"},
            {"method": "GET", "path": "/geo/satellite", "auth": True, "desc": "Satellite preview URL"},
            {"method": "POST", "path": "/pricing/quote", "auth": True, "desc": "Actuarial quote from live indicators"},
            {"method": "GET", "path": "/agri/catalog", "auth": True, "desc": "Supported crops and stages"},
            {"method": "POST", "path": "/agri/plan", "auth": True, "desc": "Agroclimatic strategy plan"},
        ],
        "licenses": LICENSES,
    }


# ---------------------------------------------------------------------------
# Climate
# ---------------------------------------------------------------------------

@router.get("/climate/current")
async def climate_current(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    try:
        from services.climate_data_service import get_climate_data_service

        weather = await get_climate_data_service().fetch_current_weather(lat, lon)
        if weather:
            payload = asdict(weather)
            return envelope(
                payload,
                source=payload.get("source") or "Open-Meteo",
                license_key="open-meteo",
                status="fresh",
                cache_ttl_seconds=900,
                refresh_frequency=REFRESH["current"],
                observed_at=payload.get("timestamp") or utc_now(),
            )
    except Exception:
        pass
    return _unavailable("Current weather upstream is unavailable", "open-meteo")


@router.get("/climate/forecast")
async def climate_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=16),
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    try:
        from services.climate_data_service import get_climate_data_service

        forecast = await get_climate_data_service().fetch_daily_forecast(lat, lon, days)
        if forecast:
            return envelope(
                forecast,
                source="Open-Meteo",
                license_key="open-meteo",
                status="fresh",
                cache_ttl_seconds=3600,
                refresh_frequency=REFRESH["forecast"],
            )
    except Exception:
        pass
    return _unavailable("Forecast upstream is unavailable", "open-meteo")


@router.get("/climate/history")
async def climate_history(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    days: int = Query(15, ge=1, le=90),
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    try:
        from services.openmeteo_service import OpenMeteoService

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        service = OpenMeteoService()
        rows = await service.obter_historico(lat, lon, start, end)
        series = []
        for row in rows or []:
            if hasattr(row, "model_dump"):
                series.append(row.model_dump())
            elif hasattr(row, "dict"):
                series.append(row.dict())
            else:
                series.append(row)
        return envelope(
            {"latitude": lat, "longitude": lon, "days": days, "observations": series},
            source="Open-Meteo archive",
            license_key="open-meteo",
            status="fresh" if series else "stale",
            stale=not bool(series),
            cache_ttl_seconds=86400,
            refresh_frequency=REFRESH["history"],
        )
    except Exception:
        return _unavailable("Historical weather upstream is unavailable", "open-meteo")


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@router.get("/analytics/indicators")
async def analytics_indicators(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    weather_env = await climate_current(lat=lat, lon=lon, _partner=_partner)
    data = weather_env.get("data") or {}
    temp = float(data.get("temperature") or 0)
    rain = float(data.get("rain") or 0)
    wind = float(data.get("wind_speed") or 0)
    humidity = float(data.get("humidity") or 0)
    heat = min(100.0, max(0.0, (temp - 20) * 5))
    drought = min(100.0, max(0.0, 80 - rain * 20 - humidity * 0.3))
    flood = min(100.0, rain * 15)
    wind_risk = min(100.0, wind * 2)
    composite = round((heat + drought + flood + wind_risk) / 4, 1)
    stale = weather_env.get("meta", {}).get("stale", False)
    status_flag = weather_env.get("meta", {}).get("status", "unavailable")
    return envelope(
        {
            "latitude": lat,
            "longitude": lon,
            "indicators": {
                "heat_index": round(heat, 1),
                "drought_index": round(drought, 1),
                "flood_index": round(flood, 1),
                "wind_index": round(wind_risk, 1),
                "composite_risk": composite,
            },
            "inputs": {"temperature_c": temp, "rain_mm": rain, "wind_kmh": wind, "humidity_pct": humidity},
        },
        source="ClimateWise indicators over Open-Meteo",
        license_key="climatewise",
        status=status_flag if status_flag != "unavailable" else "stale",
        stale=stale or status_flag != "fresh",
        cache_ttl_seconds=900,
        refresh_frequency=REFRESH["current"],
        extra_meta={"derived_from": "GET /climate/current"},
    )


@router.get("/analytics/extremes")
async def analytics_extremes(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    try:
        from services.climate_data_service import get_climate_data_service

        alerts = get_climate_data_service().get_alerts(min_severity="baixa") or []
        nearby = []
        for alert in alerts:
            payload = asdict(alert) if hasattr(alert, "__dataclass_fields__") else dict(alert)
            nearby.append(payload)
        return envelope(
            {"latitude": lat, "longitude": lon, "events": nearby[:50], "count": len(nearby)},
            source="Open-Meteo + CEMADEN via ClimateWise",
            license_key="climatewise",
            status="fresh" if nearby else "stale",
            stale=not bool(nearby),
            cache_ttl_seconds=900,
            refresh_frequency=REFRESH["current"],
        )
    except Exception:
        return _unavailable("Extreme-event feed is unavailable")


# ---------------------------------------------------------------------------
# Atlas
# ---------------------------------------------------------------------------

@router.get("/atlas/events")
async def atlas_events(
    limit: int = Query(20, ge=1, le=100),
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    features: List[Dict[str, Any]] = []
    source = "ClimateWise Atlas"
    license_key = "atlas-mdr"
    try:
        from services.climate_data_service import get_climate_data_service

        events = get_climate_data_service().get_oracle_events() or []
        for event in events[:limit]:
            if not isinstance(event, dict):
                if hasattr(event, "__dataclass_fields__"):
                    event = asdict(event)
                else:
                    continue
            lat = event.get("latitude")
            lon = event.get("longitude")
            if lat is None or lon is None:
                continue
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                    "properties": {k: v for k, v in event.items() if k not in {"latitude", "longitude"}},
                }
            )
    except Exception:
        events = []

    collection = {"type": "FeatureCollection", "features": features}
    return envelope(
        collection,
        source=source,
        license_key=license_key,
        status="fresh" if features else "stale",
        stale=not bool(features),
        cache_ttl_seconds=900,
        refresh_frequency=REFRESH["atlas"],
        extra_meta={"geojson": True, "feature_count": len(features)},
    )


@router.get("/atlas/risk-summary")
async def atlas_risk_summary(_partner: PartnerContext = Depends(require_partner)) -> Dict[str, Any]:
    try:
        from services.atlas_realtime_climate_service import atlas_realtime_climate

        summary = atlas_realtime_climate.get_risk_summary()
        return envelope(
            summary,
            source="Open-Meteo + ClimateWise Atlas",
            license_key="open-meteo",
            status="fresh",
            cache_ttl_seconds=900,
            refresh_frequency=REFRESH["atlas"],
        )
    except Exception:
        return _unavailable("Atlas risk summary is unavailable", "open-meteo")


# ---------------------------------------------------------------------------
# Geo
# ---------------------------------------------------------------------------

@router.get("/geo/layers")
async def geo_layers(_partner: PartnerContext = Depends(require_partner)) -> Dict[str, Any]:
    layers = {
        "geojson": "GeoJSON FeatureCollection (RFC 7946) on /atlas/events and /geo/feature",
        "xyz": [
            {
                "id": "osm-standard",
                "type": "raster-xyz",
                "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                "attribution": LICENSES["openstreetmap"]["attribution"],
                "license": LICENSES["openstreetmap"],
            },
            {
                "id": "esri-world-imagery",
                "type": "raster-xyz",
                "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "attribution": LICENSES["esri-imagery"]["attribution"],
                "license": LICENSES["esri-imagery"],
            },
        ],
        "wmts": [
            {
                "id": "nasa-gibs-modis-terra-truecolor",
                "type": "wmts",
                "url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{Time}/GoogleMapsCompatible_Level9/{TileMatrix}/{TileRow}/{TileCol}.jpg",
                "time": "latest",
                "license": LICENSES["nasa-gibs"],
            }
        ],
        "wms": [],
        "static": ["GET /geo/satellite"],
    }
    return envelope(
        layers,
        source="ClimateWise geo catalog",
        license_key="climatewise",
        status="fresh",
        cache_ttl_seconds=86400,
        refresh_frequency=REFRESH["geo"],
    )


@router.get("/geo/feature")
async def geo_feature(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {"latitude": lat, "longitude": lon},
        "bbox": [lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05],
    }
    return envelope(
        feature,
        source="ClimateWise",
        license_key="climatewise",
        status="fresh",
        cache_ttl_seconds=86400,
        refresh_frequency=REFRESH["geo"],
        extra_meta={"geojson": True},
    )


@router.get("/geo/satellite")
async def geo_satellite(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    zoom: int = Query(10, ge=3, le=18),
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    n = 2 ** zoom
    lat_rad = __import__("math").radians(lat)
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - __import__("math").log(__import__("math").tan(lat_rad) + (1 / __import__("math").cos(lat_rad))) / __import__("math").pi) / 2.0 * n)
    static = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}"
    return envelope(
        {
            "preview_url": static,
            "xyz_url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "wmts_modis": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/latest/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
            "tile": {"z": zoom, "x": x, "y": y},
            "point": {"lat": lat, "lon": lon},
        },
        source="Esri World Imagery + NASA GIBS",
        license_key="esri-imagery",
        status="fresh",
        cache_ttl_seconds=3600,
        refresh_frequency=REFRESH["geo"],
        extra_meta={"licenses": [LICENSES["esri-imagery"], LICENSES["nasa-gibs"]]},
    )


# ---------------------------------------------------------------------------
# Pricing + Agri
# ---------------------------------------------------------------------------

@router.post("/pricing/quote")
async def partner_quote(
    payload: PartnerQuoteRequest,
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    try:
        from api.policy_pricing import PolicyRequest, calculate_policy_endpoint

        result = await calculate_policy_endpoint(
            PolicyRequest(
                asset_value=payload.asset_value,
                severity_amount=payload.severity_amount,
                frequency_pct=payload.frequency_pct,
                coverage_period_years=payload.coverage_period_years,
                latitude=payload.latitude,
                longitude=payload.longitude,
            )
        )
        dumped = result.model_dump() if hasattr(result, "model_dump") else result
        return envelope(
            dumped,
            source="ClimateWise actuarial engine (Open-Meteo indicators)",
            license_key="climatewise",
            status="fresh",
            cache_ttl_seconds=0,
            refresh_frequency=REFRESH["pricing"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        return _unavailable(f"Quote engine unavailable: {exc}")


@router.get("/agri/catalog")
async def agri_catalog(_partner: PartnerContext = Depends(require_partner)) -> Dict[str, Any]:
    try:
        from services.agri_strategy_service import agri_strategy_service

        catalog = {
            "supported_crops": agri_strategy_service.supported_crops,
            "supported_stages": agri_strategy_service.supported_stages,
            "risk_dimensions": ["heat", "drought", "excess_rain", "flood", "wind", "disease"],
        }
        return envelope(
            catalog,
            source="ClimateWise agri-strategy",
            license_key="climatewise",
            status="fresh",
            cache_ttl_seconds=86400,
            refresh_frequency=REFRESH["agri"],
        )
    except Exception as exc:
        return _unavailable(f"Agri catalog unavailable: {exc}")


@router.post("/agri/plan")
async def agri_plan(
    payload: PartnerAgriRequest,
    _partner: PartnerContext = Depends(require_partner),
) -> Dict[str, Any]:
    try:
        from services.agri_strategy_service import agri_strategy_service

        plan = await agri_strategy_service.generate_plan(
            crop_type=payload.crop_type,
            phenological_stage=payload.phenological_stage,
            latitude=payload.latitude,
            longitude=payload.longitude,
            planning_horizon_days=payload.planning_horizon_days,
            risk_tolerance=payload.risk_tolerance,
            farm_profile=None,
            db=None,
        )
        dumped = plan.model_dump() if hasattr(plan, "model_dump") else plan
        return envelope(
            dumped,
            source="ClimateWise agri-strategy over Open-Meteo",
            license_key="climatewise",
            status="fresh",
            cache_ttl_seconds=0,
            refresh_frequency=REFRESH["agri"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        return _unavailable(f"Agri plan unavailable: {exc}")

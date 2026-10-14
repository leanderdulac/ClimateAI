"""
WeatherNext 2 ensemble forecast endpoints.

GET /api/v1/forecast/ensemble?lat&lon
GET /api/v1/forecast/ensemble/municipality/{ibge_code}
GET /api/v1/forecast/ensemble/brazil
POST /api/v1/forecast/ensemble/brazil/refresh  (optional cache warm)
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from middleware.auth_middleware import require_admin
from models.schemas import User
from services.ibge_municipalities import MunicipalityNotFound
from services.weathernext_ensemble_service import (
    OutsideBrazilError,
    WeatherNextDisabledError,
    WeatherNextEnsembleService,
    get_weathernext_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast/ensemble", tags=["weathernext-ensemble"])


class BatchCoordinate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class BatchForecastRequest(BaseModel):
    coordinates: List[BatchCoordinate] = Field(..., min_length=1, max_length=100)
    forecast_days: int = Field(7, ge=1, le=7)


def _service() -> WeatherNextEnsembleService:
    return get_weathernext_service()


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, WeatherNextDisabledError):
        return HTTPException(status_code=404, detail="Feature 'weathernext' is disabled")
    if isinstance(exc, OutsideBrazilError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, MunicipalityNotFound):
        return HTTPException(status_code=404, detail=f"Unknown IBGE municipality: {exc}")
    logger.exception("WeatherNext ensemble error: %s", exc)
    return HTTPException(status_code=502, detail="WeatherNext ensemble upstream error")


@router.get("")
async def forecast_ensemble(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    forecast_days: int = Query(7, ge=1, le=7),
    include_members: bool = Query(False),
    service: WeatherNextEnsembleService = Depends(_service),
):
    """Point forecast: daily ensemble stats, fan chart, and exceedance probabilities."""
    try:
        return await service.forecast_point(
            lat, lon, include_members=include_members, forecast_days=forecast_days
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@router.post("/batch")
async def forecast_ensemble_batch(
    request: BatchForecastRequest,
    service: WeatherNextEnsembleService = Depends(_service),
):
    """Multi-coordinate request (Open-Meteo comma-separated lat/lon lists)."""
    try:
        coords = [(item.lat, item.lon) for item in request.coordinates]
        results = await service.forecast_batch(
            coords, forecast_days=request.forecast_days
        )
        return {"count": len(results), "results": results}
    except Exception as exc:
        raise _translate_error(exc) from exc


@router.get("/municipality/{ibge_code}")
async def forecast_ensemble_municipality(
    ibge_code: str,
    forecast_days: int = Query(7, ge=1, le=7),
    include_members: bool = Query(False),
    service: WeatherNextEnsembleService = Depends(_service),
):
    """Forecast at an IBGE municipality centroid (includes Monte Alegre)."""
    try:
        return await service.forecast_municipality(
            ibge_code, include_members=include_members, forecast_days=forecast_days
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@router.get("/brazil")
async def forecast_ensemble_brazil(
    resolution: float = Query(1.0, ge=0.5, le=2.0, description="Grid step in degrees"),
    forecast_days: int = Query(7, ge=1, le=7),
    service: WeatherNextEnsembleService = Depends(_service),
):
    """Brazil-wide grid summary of P(heavy rain), cached 1–3h."""
    try:
        return await service.forecast_brazil_grid(
            resolution=resolution, forecast_days=forecast_days
        )
    except Exception as exc:
        raise _translate_error(exc) from exc


@router.post("/brazil/refresh")
async def refresh_brazil_grid(
    resolution: float = Query(1.0, ge=0.5, le=2.0),
    current_user: User = Depends(require_admin),
    service: WeatherNextEnsembleService = Depends(_service),
):
    """Admin-only scheduled/manual refresh of the Brazil grid cache."""
    try:
        summary = await service.forecast_brazil_grid(
            resolution=resolution, force_refresh=True
        )
        return {
            "refreshed_by": current_user.email if current_user else "admin",
            "cell_count": summary.get("cell_count"),
            "p_heavy_rain_mean": summary.get("p_heavy_rain_mean"),
        }
    except Exception as exc:
        raise _translate_error(exc) from exc

"""
API Router for NOAA (National Oceanic and Atmospheric Administration) Integration
Provides access to climate data and weather forecasts
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session
from models.sqlalchemy_models import ClimateEnsoSignal
from services.enso_service import ENSOService
from services.noaa_service import NOAAService

router = APIRouter()

# Instância global do serviço
noaa_service = NOAAService()
enso_service = ENSOService()


class ClimateDataRequest(BaseModel):
    location: str
    start_date: str
    end_date: str
    data_type: Optional[str] = "TMAX"


class WeatherForecastRequest(BaseModel):
    latitude: float
    longitude: float


@router.post("/climate-data")
async def get_climate_data_endpoint(request: ClimateDataRequest):
    """
    Get historical climate data from NOAA
    """
    if not os.getenv("NOAA_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="NOAA_API_KEY not configured in environment variables",
        )

    try:
        result = await noaa_service.get_climate_data(
            location=request.location,
            start_date=request.start_date,
            end_date=request.end_date,
            data_type=request.data_type
        )
        return result
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"NOAA climate data error: {str(e)}\nTraceback: {tb}")


@router.post("/weather-forecast")
async def get_weather_forecast_endpoint(request: WeatherForecastRequest):
    """
    Get weather forecast from National Weather Service
    """
    try:
        result = await noaa_service.get_weather_forecast(
            latitude=request.latitude,
            longitude=request.longitude
        )
        return result
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"NOAA weather forecast error: {str(e)}\nTraceback: {tb}")


@router.get("/status")
async def get_noaa_status():
    """
    Get NOAA integration status
    """
    try:
        status = noaa_service.get_service_status()
        return status
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return {
            "service": "NOAA Integration",
            "status": "error",
            "error": f"{str(e)}\nTraceback: {tb}",
            "api_key_configured": bool(os.getenv("NOAA_API_KEY")),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/data-types")
async def get_available_data_types():
    """
    Get available climate data types from NOAA
    """
    return {
        "data_types": [
            {
                "id": "TMAX",
                "name": "Maximum Temperature",
                "unit": "Celsius",
                "description": "Daily maximum temperature"
            },
            {
                "id": "TMIN",
                "name": "Minimum Temperature",
                "unit": "Celsius",
                "description": "Daily minimum temperature"
            },
            {
                "id": "TAVG",
                "name": "Average Temperature",
                "unit": "Celsius",
                "description": "Daily average temperature"
            },
            {
                "id": "PRCP",
                "name": "Precipitation",
                "unit": "Millimeters",
                "description": "Daily precipitation amount"
            },
            {
                "id": "SNOW",
                "name": "Snowfall",
                "unit": "Millimeters",
                "description": "Daily snowfall amount"
            },
            {
                "id": "SNWD",
                "name": "Snow Depth",
                "unit": "Millimeters",
                "description": "Snow depth at end of day"
            },
            {
                "id": "AWND",
                "name": "Average Wind Speed",
                "unit": "m/s",
                "description": "Average daily wind speed"
            },
            {
                "id": "WSF2",
                "name": "Fastest 2-minute Wind Speed",
                "unit": "m/s",
                "description": "Fastest 2-minute wind speed"
            }
        ],
        "source": "NOAA Climate Data Online (GHCND)",
        "dataset": "Global Historical Climatology Network Daily"
    }


@router.get("/enso/snapshot")
async def get_enso_snapshot(
    persist: bool = Query(False, description="Persist latest ENSO snapshot into climate_enso_signals"),
    db: AsyncSession = Depends(get_db_session),
):
    """Get latest ENSO snapshot built from CPC RONI/ONI sources."""
    try:
        snapshot = await enso_service.get_latest_snapshot()
        persisted_id = None
        if persist:
            row = await enso_service.persist_snapshot(db, snapshot)
            persisted_id = row.id

        return {
            "snapshot": {
                **snapshot,
                "reference_date": snapshot["reference_date"].isoformat(),
                "ingestion_timestamp": snapshot["ingestion_timestamp"].isoformat(),
            },
            "persisted": bool(persist),
            "persisted_id": persisted_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ENSO snapshot error: {str(e)}")


@router.get("/enso/series")
async def get_enso_series(
    index_name: str = Query("roni", pattern="^(roni|oni)$"),
    limit: int = Query(24, ge=1, le=900),
):
    """Return latest seasonal RONI/ONI values for model feature pipelines."""
    try:
        if index_name == "oni":
            series = await enso_service.get_oni_series()
        else:
            series = await enso_service.get_roni_series()

        sliced = series[-limit:]
        return {
            "index": index_name,
            "count": len(sliced),
            "series": sliced,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ENSO series error: {str(e)}")


@router.get("/enso/persisted/latest")
async def get_latest_persisted_enso_signal(db: AsyncSession = Depends(get_db_session)):
    """Read latest persisted ENSO snapshot from climate_enso_signals table."""
    try:
        stmt = select(ClimateEnsoSignal).order_by(ClimateEnsoSignal.reference_date.desc()).limit(1)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return {"found": False, "message": "No ENSO signals persisted yet"}

        return {
            "found": True,
            "id": row.id,
            "reference_date": row.reference_date.isoformat() if row.reference_date else None,
            "roni": row.roni,
            "oni": row.oni,
            "soi": row.soi,
            "olr": row.olr,
            "regime_label": row.regime_label,
            "regime_confidence": row.regime_confidence,
            "provisional_flag": row.provisional_flag,
            "enso_score": row.enso_score,
            "p_el_nino": row.p_el_nino,
            "p_la_nina": row.p_la_nina,
            "p_neutral": row.p_neutral,
            "transition_score": row.transition_score,
            "impact_risk_modifier": row.impact_risk_modifier,
            "source_url": row.source_url,
            "ingestion_timestamp": row.ingestion_timestamp.isoformat() if row.ingestion_timestamp else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persisted ENSO read error: {str(e)}")


@router.post("/enso/ingest-now")
async def ingest_enso_now(
    db: AsyncSession = Depends(get_db_session),
):
    """Administrative endpoint to fetch and persist latest ENSO snapshot immediately."""
    try:
        snapshot = await enso_service.get_latest_snapshot()
        row = await enso_service.persist_snapshot(db, snapshot)

        return {
            "status": "ok",
            "message": "ENSO ingestion executed successfully",
            "persisted_id": row.id,
            "reference_date": row.reference_date.isoformat() if row.reference_date else None,
            "regime_label": row.regime_label,
            "regime_confidence": row.regime_confidence,
            "impact_risk_modifier": row.impact_risk_modifier,
            "ingestion_timestamp": row.ingestion_timestamp.isoformat() if row.ingestion_timestamp else None,
            "source_url": row.source_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ENSO ingest-now error: {str(e)}")
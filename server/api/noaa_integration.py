"""
API Router for NOAA (National Oceanic and Atmospheric Administration) Integration
Provides access to climate data and weather forecasts
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.noaa_service import NOAAService

router = APIRouter()

# Instância global do serviço
noaa_service = NOAAService()


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
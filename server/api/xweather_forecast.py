"""
Router para endpoints de previsão climática da API xWeather
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from models.schemas import ClimaData
from services.xweather_service import xweather_service

router = APIRouter()


@router.get("/brazil-forecast", tags=["Climate Forecast - xWeather"])
async def get_xweather_brazil_forecast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude do local"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude do local"),
    days: int = Query(
        7, ge=1, le=7, description="Número de dias para previsão (máximo 7)"
    ),
):
    """
    Obter previsão climática para o Brasil usando a API xWeather

    - **latitude**: Latitude da localização (-90 a 90)
    - **longitude**: Longitude da localização (-180 a 180)
    - **days**: Número de dias para previsão (padrão: 7, máx: 7)
    """
    try:
        forecast_data = await xweather_service.get_brazil_climate_forecast_for_location(
            latitude=latitude, longitude=longitude, days=days
        )

        return {
            "forecast_data": forecast_data,
            "location": {"latitude": latitude, "longitude": longitude},
            "days_requested": days,
            "source": "xWeather API",
            "timestamp": datetime.now().isoformat(),
            "api_endpoint": "/api/v1/xweather/brazil-forecast",
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter previsão da API xWeather: {str(e)}"
        )


@router.get("/brazil-raw-forecast", tags=["Climate Forecast - xWeather"])
async def get_xweather_brazil_raw_forecast(
    days: int = Query(
        7, ge=1, le=7, description="Número de dias para previsão (máximo 7)"
    )
):
    """
    Obter dados brutos da previsão climática para o Brasil usando a API xWeather

    - **days**: Número de dias para previsão (padrão: 7, máx: 7)
    """
    try:
        raw_data = await xweather_service.get_brazil_climate_forecast(days=days)

        return {
            "raw_data": raw_data,
            "days_requested": days,
            "source": "xWeather API",
            "timestamp": datetime.now().isoformat(),
            "api_endpoint": "/api/v1/xweather/brazil-raw-forecast",
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter dados brutos da API xWeather: {str(e)}",
        )


@router.get("/health-check", tags=["Climate Forecast - xWeather"])
async def xweather_health_check():
    """
    Verifica a saúde e conectividade com a API xWeather
    """
    try:
        # Testar conexão fazendo uma chamada rápida
        test_data = await xweather_service.get_brazil_climate_forecast(days=1)

        return {
            "status": "healthy",
            "source": "xWeather API",
            "connected": True,
            "timestamp": datetime.now().isoformat(),
            "api_endpoint": "/api/v1/xweather/health-check",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"xWeather API não disponível: {str(e)}"
        )

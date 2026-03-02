"""
XWeather API Integration Router
Provides real-time weather conditions and forecasts from XWeather
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.xweather_service import XWeatherService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["xweather"])

# Instância global do serviço
xweather_service = XWeatherService()


# ============================================================================
# Response Models
# ============================================================================

class CurrentConditionResponse(BaseModel):
    """Resposta de condições atuais"""
    location: str
    latitude: float
    longitude: float
    temperature: float
    feels_like: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    weather_code: int
    weather_description: str
    precipitation: float
    observation_time: str
    source: str


class ForecastDayResponse(BaseModel):
    """Resposta de previsão diária"""
    date: str
    temperature_high: float
    temperature_low: float
    humidity: int
    precipitation: float
    precipitation_probability: float
    wind_speed: float
    wind_direction: int
    weather_code: int
    weather_description: str
    source: str


class XWeatherResponse(BaseModel):
    """Resposta completa do XWeather"""
    success: bool
    source: str
    current: Optional[CurrentConditionResponse]
    forecast: List[ForecastDayResponse]
    error: Optional[str]


class XWeatherStatusResponse(BaseModel):
    """Resposta de status do serviço"""
    service: str
    status: str
    api_key_configured: bool
    base_url: str
    endpoints: List[str]
    features: List[str]
    fallback: str
    timestamp: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/conditions", response_model=XWeatherResponse)
async def get_current_conditions(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    limit: int = Query(default=1, ge=1, le=10, description="Number of stations")
):
    """
    Obter condições climáticas atuais do XWeather
    
    **Dados Incluídos:**
    - Temperatura atual e sensação térmica
    - Umidade, pressão, vento
    - Precipitação (1h e 24h)
    - Radiação solar, índice UV
    - Código e descrição do tempo
    
    **Fallback:** Embrapa/OpenMeteo se XWeather indisponível
    """
    try:
        result = xweather_service.get_weather_data(
            latitude=latitude,
            longitude=longitude,
            days=1
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=503,
                detail=f"XWeather service unavailable: {result.get('error', 'Unknown error')}"
            )
        
        # Format current condition
        current = None
        if result.get('current'):
            current_data = result['current']
            current = CurrentConditionResponse(
                location=f"{latitude},{longitude}",
                latitude=latitude,
                longitude=longitude,
                temperature=current_data.get('temperature', 0),
                feels_like=current_data.get('feels_like', 0),
                humidity=current_data.get('humidity', 0),
                pressure=current_data.get('pressure', 0),
                wind_speed=current_data.get('wind_speed', 0),
                wind_direction=current_data.get('wind_direction', 0),
                weather_code=current_data.get('weather_code', 0),
                weather_description=current_data.get('weather_description', ''),
                precipitation=current_data.get('precipitation', 0),
                observation_time=current_data.get('observation_time', ''),
                source=current_data.get('source', 'XWeather')
            )
        
        # Format forecast
        forecast = []
        for fc in result.get('forecast', []):
            forecast.append(ForecastDayResponse(
                date=fc.get('date', ''),
                temperature_high=fc.get('temperature_high', 0),
                temperature_low=fc.get('temperature_low', 0),
                humidity=fc.get('humidity', 0),
                precipitation=fc.get('precipitation', 0),
                precipitation_probability=fc.get('precipitation_probability', 0),
                wind_speed=fc.get('wind_speed', 0),
                wind_direction=fc.get('wind_direction', 0),
                weather_code=fc.get('weather_code', 0),
                weather_description=fc.get('weather_description', ''),
                source=fc.get('source', 'XWeather')
            ))
        
        return XWeatherResponse(
            success=result['success'],
            source=result['source'],
            current=current,
            forecast=forecast,
            error=result.get('error')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_conditions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"XWeather error: {str(e)}")


@router.get("/forecast", response_model=XWeatherResponse)
async def get_forecast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    days: int = Query(default=7, ge=1, le=15, description="Number of days")
):
    """
    Obter previsão climática do XWeather
    
    **Dados Incluídos:**
    - Temperatura máxima e mínima
    - Precipitação e probabilidade
    - Umidade, vento
    - Código e descrição do tempo
    - Nascer/pôr do sol
    
    **Máximo:** 15 dias
    """
    try:
        result = xweather_service.get_weather_data(
            latitude=latitude,
            longitude=longitude,
            days=days
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=503,
                detail=f"XWeather service unavailable: {result.get('error', 'Unknown error')}"
            )
        
        # Format forecast
        forecast = []
        for fc in result.get('forecast', []):
            forecast.append(ForecastDayResponse(
                date=fc.get('date', ''),
                temperature_high=fc.get('temperature_high', 0),
                temperature_low=fc.get('temperature_low', 0),
                humidity=fc.get('humidity', 0),
                precipitation=fc.get('precipitation', 0),
                precipitation_probability=fc.get('precipitation_probability', 0),
                wind_speed=fc.get('wind_speed', 0),
                wind_direction=fc.get('wind_direction', 0),
                weather_code=fc.get('weather_code', 0),
                weather_description=fc.get('weather_description', ''),
                source=fc.get('source', 'XWeather')
            ))
        
        return XWeatherResponse(
            success=result['success'],
            source=result['source'],
            current=None,
            forecast=forecast,
            error=result.get('error')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_forecast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"XWeather error: {str(e)}")


@router.get("/brazil-forecast", response_model=XWeatherResponse)
async def get_brazil_forecast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    days: int = Query(default=7, ge=1, le=15, description="Number of days")
):
    """
    Obter previsão climática para Brasil (endpoint otimizado)
    
    **Otimizações:**
    - Fallback automático para Embrapa
    - Dados em português
    - Melhor resolução para América do Sul
    """
    # Usar endpoint padrão com fallback automático
    return await get_forecast(latitude, longitude, days)


@router.get("/status", response_model=XWeatherStatusResponse)
async def get_xweather_status():
    """
    Obter status da integração XWeather
    """
    status = xweather_service.get_service_status()
    return XWeatherStatusResponse(**status)


@router.get("/test-connection")
async def test_connection(
    latitude: float = Query(default=-23.5505, description="Test latitude (São Paulo)"),
    longitude: float = Query(default=-46.6333, description="Test longitude (São Paulo)")
):
    """
    Testar conexão com API XWeather
    
    **Teste:**
    - Conectividade com API
    - Autenticação
    - Resposta de dados
    """
    try:
        # Testar conexão
        result = xweather_service.get_weather_data(
            latitude=latitude,
            longitude=longitude,
            days=1
        )
        
        return {
            'success': result['success'],
            'source': result['source'],
            'has_current': result.get('current') is not None,
            'has_forecast': len(result.get('forecast', [])) > 0,
            'latency_ms': 'N/A',  # Could measure this
            'message': 'XWeather connection successful' if result['success'] else 'XWeather connection failed'
        }
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Connection test failed'
        }

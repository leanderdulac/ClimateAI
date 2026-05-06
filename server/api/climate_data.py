"""
Climate Data API Router
Endpoints para dados meteorológicos em tempo real (Open-Meteo + CEMADEN + Embrapa)
"""

from typing import Optional
from fastapi import APIRouter, Query

from services.climate_data_service import get_climate_data_service

router = APIRouter(
    prefix="/climate-data",
    tags=["Climate Data"],
)


@router.get("/current")
async def get_current_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """Condições meteorológicas atuais via Open-Meteo"""
    service = get_climate_data_service()
    weather = await service.fetch_current_weather(lat, lon)
    if weather:
        from dataclasses import asdict
        return asdict(weather)
    return {"error": "Não foi possível obter dados meteorológicos"}


@router.get("/forecast")
async def get_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    days: int = Query(7, ge=1, le=16, description="Dias de previsão"),
):
    """Previsão diária via Open-Meteo"""
    service = get_climate_data_service()
    forecast = await service.fetch_daily_forecast(lat, lon, days)
    if forecast:
        return forecast
    return {"error": "Não foi possível obter previsão"}


@router.get("/soil")
async def get_soil_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """Dados de solo e vegetação — proxy Embrapa via Open-Meteo"""
    service = get_climate_data_service()
    return await service.fetch_soil_vegetation_data(lat, lon)


@router.get("/alerts")
async def get_climate_alerts(
    severity: str = Query("baixa", description="Severidade mínima: baixa, media, alta, critica"),
):
    """Alertas climáticos ativos (Open-Meteo + CEMADEN)"""
    service = get_climate_data_service()
    alerts = service.get_alerts(min_severity=severity)
    return {"alerts": alerts, "total": len(alerts)}


@router.post("/scan")
async def force_scan():
    """Força uma varredura imediata de todas as capitais brasileiras"""
    service = get_climate_data_service()
    result = await service.scan_brazil_conditions()
    return result


@router.get("/risk-factor")
async def get_risk_factor(
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
):
    """Fator de ajuste de risco baseado em dados meteorológicos reais"""
    service = get_climate_data_service()
    return service.get_weather_risk_factor(uf=uf)


@router.get("/oracle-events")
async def get_oracle_events(
    limit: int = Query(20, ge=1, le=100),
):
    """Alertas climáticos já em formato Oracle"""
    service = get_climate_data_service()
    events = service.get_oracle_events()
    return {"events": events[:limit], "total": len(events)}

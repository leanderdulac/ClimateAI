"""
External APIs Router - Endpoints para dados de APIs externas (clima, economia, commodities)
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from services.audit_service import log_operation
from services.external_api_service import (
    get_commodity_prices,
    get_economic_indicators,
    get_real_time_data,
    get_weather_data,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/weather")
async def get_weather_endpoint(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Obter dados meteorológicos em tempo real

    Args:
        latitude: Latitude da localização
        longitude: Longitude da localização

    Returns:
        Dados meteorológicos atuais
    """
    try:
        result = await get_weather_data(latitude, longitude)
        return result
    except Exception as e:
        logger.error(f"Erro ao obter dados meteorológicos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro meteorológico: {str(e)}")


@router.get("/economic-indicators")
async def get_economic_indicators_endpoint() -> Dict[str, Any]:
    """
    Obter indicadores econômicos atuais

    Returns:
        Taxa de inflação e crescimento do PIB
    """
    try:
        result = await get_economic_indicators()
        return result
    except Exception as e:
        logger.error(f"Erro ao obter indicadores econômicos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro econômico: {str(e)}")


@router.get("/commodity-prices")
async def get_commodity_prices_endpoint(
    symbols: List[str] = Query(..., description="Símbolos das commodities")
) -> Dict[str, Any]:
    """
    Obter preços de commodities

    Args:
        symbols: Lista de símbolos de commodities

    Returns:
        Preços atuais das commodities
    """
    try:
        result = await get_commodity_prices(symbols)
        return result
    except Exception as e:
        logger.error(f"Erro ao obter preços de commodities: {e}")
        raise HTTPException(status_code=500, detail=f"Erro commodities: {str(e)}")


@router.get("/real-time-data")
async def get_real_time_data_endpoint(
    latitude: float,
    longitude: float,
    commodities: List[str] = Query(
        ["CORN", "SOYBEAN"], description="Símbolos das commodities"
    ),
) -> Dict[str, Any]:
    """
    Obter dados abrangentes em tempo real de todas as APIs externas

    Args:
        latitude: Latitude da localização
        longitude: Longitude da localização
        commodities: Lista de símbolos de commodities

    Returns:
        Dados combinados de clima, economia e commodities
    """
    try:
        result = await get_real_time_data(latitude, longitude, commodities)

        # Registrar operação de auditoria
        log_operation(
            operation="external_data_retrieval",
            resource_type="external_api",
            action="fetch",
            status="success",
            resource_id=f"lat_{latitude}_lon_{longitude}",
            details={
                "latitude": latitude,
                "longitude": longitude,
                "commodities": commodities,
                "data_sources": ["weather", "economic", "commodity"],
            },
        )

        return result
    except Exception as e:
        # Registrar erro de auditoria
        log_operation(
            operation="external_data_retrieval",
            resource_type="external_api",
            action="fetch",
            status="error",
            resource_id=f"lat_{latitude}_lon_{longitude}",
            details={
                "error": str(e),
                "latitude": latitude,
                "longitude": longitude,
                "commodities": commodities,
            },
            compliance_flags=["external_api_error"],
        )
        logger.error(f"Erro ao obter dados em tempo real: {e}")
        raise HTTPException(status_code=500, detail=f"Erro dados tempo real: {str(e)}")

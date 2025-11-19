"""
Router para endpoints de previsão climática
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models.schemas import PrevisaoClima
from services.previsao_service import PrevisaoService

router = APIRouter()
previsao_service = PrevisaoService()


@router.get("/clima", response_model=PrevisaoClima)
async def get_previsao_clima(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    dias: int = Query(7, ge=1, le=15),
):
    """
    Obter previsão climática para uma localização específica
    """
    try:
        return previsao_service.obter_previsao_clima(
            latitude=latitude, longitude=longitude, dias=dias
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/eventos", response_model=List[str])
async def get_previsao_eventos(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    dias: int = Query(30, ge=1, le=90),
):
    """
    Obter previsão de eventos climáticos extremos
    """
    try:
        return previsao_service.obter_previsao_eventos(
            latitude=latitude, longitude=longitude, dias=dias
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

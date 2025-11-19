"""
Router para endpoints de detecção de eventos climáticos
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models.schemas import EventoClimatico, EventoClimaticoTipo
from models.token_schemas import EventoToken
from services.eventos_service import EventosService

router = APIRouter()
eventos_service = EventosService()


@router.get("/", response_model=List[EventoClimatico])
async def get_eventos_climaticos(
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    tipo: Optional[EventoClimaticoTipo] = Query(None),
    data_inicio: Optional[datetime] = Query(None),
    data_fim: Optional[datetime] = Query(None),
    raio: Optional[float] = Query(50.0, ge=1.0, le=500.0),  # em km
):
    """
    Obter eventos climáticos detectados em uma área específica
    """
    try:
        return eventos_service.obter_eventos(
            latitude=latitude,
            longitude=longitude,
            tipo=tipo,
            data_inicio=data_inicio,
            data_fim=data_fim,
            raio=raio,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/severidade", response_model=List[EventoClimatico])
async def get_eventos_por_severidade(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    severidade_minima: int = Query(3, ge=1, le=5),
    dias: int = Query(30, ge=1, le=90),
):
    """
    Obter eventos climáticos com severidade mínima em uma área
    """
    try:
        return eventos_service.obter_eventos_por_severidade(
            latitude=latitude,
            longitude=longitude,
            severidade_minima=severidade_minima,
            dias=dias,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

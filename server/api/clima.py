"""
Router para endpoints de dados climáticos
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from models.schemas import ClimaData
from services.clima_service import ClimaService

router = APIRouter()
clima_service = ClimaService()


@router.get("/clima/historico", response_model=List[ClimaData])
async def get_historico_clima(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    data_inicio: datetime = Query(...),
    data_fim: datetime = Query(...),
    variavel: Optional[str] = Query(None)
):
    """
    Obter dados climáticos históricos para uma localização específica
    """
    try:
        return clima_service.obter_historico(
            latitude=latitude,
            longitude=longitude,
            data_inicio=data_inicio,
            data_fim=data_fim,
            variavel=variavel
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clima/atual", response_model=ClimaData)
async def get_clima_atual(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """
    Obter condições climáticas atuais para uma localização específica
    """
    try:
        return clima_service.obter_clima_atual(
            latitude=latitude,
            longitude=longitude
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
Router para endpoints de modelagem econômica
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
from models.schemas import PrevisaoPreco
from services.modelagem_service import ModelagemService

router = APIRouter()
modelagem_service = ModelagemService()


@router.get("/previsao-precos", response_model=List[PrevisaoPreco])
async def get_previsao_precos(
    simbolos: List[str] = Query(..., description="Símbolos de commodities"),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    dias: int = Query(30, ge=1, le=90)
):
    """
    Obter previsões de preços de commodities considerando fatores climáticos
    """
    try:
        return modelagem_service.obter_previsao_precos(
            simbolos=simbolos,
            latitude=latitude,
            longitude=longitude,
            dias=dias
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/impacto-climatico", response_model=List[Dict])
async def get_impacto_climatico(
    simbolo: str = Query(...),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    periodo: int = Query(30, ge=1, le=365)
):
    """
    Obter análise de impacto climático sobre o preço de uma commodity
    """
    try:
        return modelagem_service.obter_impacto_climatico(
            simbolo=simbolo,
            latitude=latitude,
            longitude=longitude,
            periodo=periodo
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

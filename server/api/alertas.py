"""
Router para endpoints de sistema de alertas
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models.schemas import Alerta
from services.alertas_service import AlertasService

router = APIRouter()
alertas_service = AlertasService()


@router.get("/", response_model=List[Alerta])
async def get_alertas(
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    nivel_minimo: Optional[int] = Query(1, ge=1, le=5),
    ativo: bool = Query(True),
    limite: int = Query(50, ge=1, le=1000),
):
    """
    Obter alertas ativos em uma área específica
    """
    try:
        return alertas_service.obter_alertas(
            latitude=latitude,
            longitude=longitude,
            nivel_minimo=nivel_minimo,
            ativo=ativo,
            limite=limite,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usuario", response_model=List[Alerta])
async def get_alertas_usuario(
    usuario_id: str = Query(...), lido: Optional[bool] = Query(None)
):
    """
    Obter alertas específicos de um usuário
    """
    try:
        return alertas_service.obter_alertas_usuario(usuario_id=usuario_id, lido=lido)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{alerta_id}/marcar-lido")
async def marcar_alerta_lido(alerta_id: str):
    """
    Marcar um alerta como lido
    """
    try:
        alertas_service.marcar_como_lido(alerta_id)
        return {"message": "Alerta marcado como lido"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

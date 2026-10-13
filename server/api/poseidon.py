"""HTTP surface for the local Poseidon assistant and CEDAE CCO."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from middleware.auth_middleware import get_current_active_user
from models.sqlalchemy_models import User
from services import poseidon_cco as cco
from services.poseidon_service import chat, poseidon_status

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatTurn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class PoseidonChatRequest(BaseModel):
    messages: List[ChatTurn] = Field(..., min_length=1)
    model: Optional[str] = None


@router.get("/status")
async def status_endpoint(_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    return poseidon_status()


@router.post("/chat")
async def chat_endpoint(
    payload: PoseidonChatRequest,
    _user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    try:
        result = await chat(
            [turn.model_dump() for turn in payload.messages],
            model=payload.model,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("Poseidon chat unavailable: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# CEDAE command center (advisory fixtures — not SCADA)
# ---------------------------------------------------------------------------


@router.get("/cco/systems")
async def cco_systems(_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    return cco.get_systems()


@router.get("/cco/cma")
async def cco_cma(_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    return cco.get_cma()


@router.get("/cco/connectors")
async def cco_connectors(
    _user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    return await cco.list_connectors()


@router.get("/cco/psa")
async def cco_psa(_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    return cco.get_psa()


@router.get("/cco/incidents")
async def cco_incidents(
    _user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    return cco.get_incidents()


@router.post("/cco/demo/geosmina")
async def cco_demo_geosmina(
    _user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    return cco.demo_geosmina()


@router.post("/cco/demo/guandu-50")
async def cco_demo_guandu_50(
    _user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    return cco.demo_guandu_50()


@router.get("/cco/demanda")
async def cco_demanda(
    horizonte_h: int = Query(24, description="Horizonte em horas (clampeado 1–48)"),
    _user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    return await cco.forecast_demanda_envelope(horizonte_h)

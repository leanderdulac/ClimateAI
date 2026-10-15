"""Base L2 status for Atlas and dashboard telemetry."""

from __future__ import annotations

from fastapi import APIRouter

from services.base_status import probe_base_status

router = APIRouter(prefix="/blockchain/base", tags=["base-l2"])


@router.get("/status")
async def base_l2_status():
    """Probe optional Base RPC. Returns not_configured when env is unset."""
    return await probe_base_status()

"""Compute / DePIN inference status for the dashboard Akash card."""

from __future__ import annotations

from fastapi import APIRouter

from services.inference_compute import probe_inference_health

router = APIRouter(prefix="/compute", tags=["compute"])


@router.get("/status")
async def compute_status():
    """Probe the optional remote inference host. Never returns URL or secrets."""
    return await probe_inference_health()

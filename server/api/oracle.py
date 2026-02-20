"""
Oracle API — Climate Settlement Oracle Endpoints
Exposes the Oracle Service for severity evaluation, payout triggering,
and system status monitoring.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from services.oracle_service import OracleService, SeverityEvent
from services.kms_signer_service import KMSSigner

router = APIRouter(prefix="/oracle", tags=["Oracle"])

# Initialize services
kms_signer = KMSSigner()
oracle = OracleService(kms_signer=kms_signer)


# ─── Request Models ────────────────────────────────────────────────

class SeverityEventRequest(BaseModel):
    token_id: int = Field(..., description="On-chain token ID")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity_score: float = Field(..., ge=1.0, le=5.0, description="Severity score (1–5)")
    ndvi: float = Field(0.45, description="Current NDVI value")
    soil_moisture: float = Field(0.25, description="Current soil moisture")
    source: str = Field("vertex_ai", description="Score source")


class BatchEvalRequest(BaseModel):
    events: List[SeverityEventRequest]


class ConsensusVoteRequest(BaseModel):
    event: SeverityEventRequest
    oracle_id: str = Field(..., description="ID of the voting oracle instance")


# ─── Endpoints ─────────────────────────────────────────────────────

@router.post("/evaluate")
async def evaluate_severity_event(request: SeverityEventRequest):
    """
    Evaluate a climate severity event and decide whether to trigger payout.

    - If severity >= 3.0 → triggers payout (LOCAL mode: simulated)
    - Returns decision, payout percentage, and transaction details
    """
    event = SeverityEvent(
        token_id=request.token_id,
        latitude=request.latitude,
        longitude=request.longitude,
        severity_score=request.severity_score,
        ndvi=request.ndvi,
        soil_moisture=request.soil_moisture,
        source=request.source
    )
    result = await oracle.evaluate_event(event)
    return result


@router.post("/evaluate/batch")
async def evaluate_batch(request: BatchEvalRequest):
    """Evaluate multiple severity events in batch (e.g. from scheduled scan)."""
    events = [
        SeverityEvent(
            token_id=e.token_id,
            latitude=e.latitude,
            longitude=e.longitude,
            severity_score=e.severity_score,
            ndvi=e.ndvi,
            soil_moisture=e.soil_moisture,
            source=e.source
        )
        for e in request.events
    ]
    results = await oracle.evaluate_batch(events)
    return {"results": results, "total": len(results)}


@router.post("/consensus/vote")
async def submit_consensus_vote(request: ConsensusVoteRequest):
    """
    Submit a vote in the multi-oracle consensus mechanism.
    Payout only triggers when the required number of votes is reached.
    """
    event = SeverityEvent(
        token_id=request.event.token_id,
        latitude=request.event.latitude,
        longitude=request.event.longitude,
        severity_score=request.event.severity_score,
        ndvi=request.event.ndvi,
        soil_moisture=request.event.soil_moisture,
        source=request.event.source,
        consensus_required=3  # Multi-oracle: 3 votes required
    )
    result = await oracle.submit_vote(event, request.oracle_id)
    return result


@router.get("/status")
async def get_oracle_status():
    """Returns the operational status of the Oracle and KMS Signer."""
    return {
        "oracle": oracle.get_status(),
        "kms_signer": kms_signer.get_status()
    }


@router.get("/history")
async def get_oracle_history():
    """Returns the history of processed events."""
    return {
        "events": oracle.processed_events[-50:],  # Last 50 events
        "total": len(oracle.processed_events)
    }

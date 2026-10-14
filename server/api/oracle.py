"""
Oracle API — Parametric Settlement & Cryptographic Truth Engine Endpoints
Exposes the Oracle Service for:
- 2-of-3 Multi-source Triangulated Evaluation (Satellite + Ground + News)
- Verifiable Cryptographic Audit Dossiers (SHA-256 / IPFS CID)
- M-of-N Cryptographic Node Consensus Voting
- System Status & Transparency Monitoring
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from config.database import get_db_session
from fastapi import APIRouter, Depends, HTTPException, status
from middleware.auth_middleware import require_admin
from models.schemas import User
from pydantic import BaseModel, Field
from services.kms_signer_service import KMSSigner
from services.oracle_service import (
    OracleService,
    SeverityEvent,
    SignedOracleVote,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/oracle", tags=["Oracle"])

# Initialize services
kms_signer = KMSSigner()
oracle = OracleService(kms_signer=kms_signer)


# ─── Request Models ────────────────────────────────────────────────

class SeverityEventRequest(BaseModel):
    token_id: int = Field(..., description="On-chain policy token ID")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity_score: float = Field(..., ge=1.0, le=5.0, description="Severity score (1–5)")
    ndvi: float = Field(0.45, description="Current NDVI value")
    soil_moisture: float = Field(0.25, description="Current soil moisture")
    source: str = Field("vertex_ai", description="Score source")
    disaster_type: str = Field("general_climate", description="Type of disaster")


class BatchEvalRequest(BaseModel):
    events: List[SeverityEventRequest]


class TriangulatedEvalRequest(BaseModel):
    token_id: int = Field(..., description="Policy token ID")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    disaster_type: str = Field(..., description="e.g. flood, drought, frost, windstorm")
    satellite_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sentinel-2/GEE metrics (ndwi_water_index, ndvi_anomaly, confidence)",
    )
    ground_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Physical station metrics (INMET/CEMADEN precip_72h_mm, temp_c, wind_speed)",
    )
    news_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Media intelligence & Civil Defense alerts (severity_score, confidence, decree)",
    )
    auto_trigger_if_quorum: bool = Field(
        default=True,
        description="Automatically trigger on-chain settlement if 2-of-3 quorum is met",
    )


class SignedVoteRequest(BaseModel):
    token_id: int = Field(..., description="On-chain token ID")
    oracle_node_id: str = Field(..., description="ID of the voting node (e.g. akash-validator-eu-1)")
    node_address: str = Field(..., description="Ethereum/EVM address of the oracle node")
    evidence_hash: str = Field(..., description="0x-prefixed SHA-256 hash of canonical evidence")
    decision: str = Field(..., description="APPROVE_PAYOUT or REJECT")
    payout_bps: int = Field(default=10000, ge=0, le=10000, description="Payout basis points")
    signature: str = Field(..., description="ECDSA cryptographic signature of the evidence hash")


class ConsensusVoteRequest(BaseModel):
    event: SeverityEventRequest
    oracle_id: str = Field(..., description="ID of the voting oracle instance")


# ─── Endpoints ─────────────────────────────────────────────────────

@router.post("/evaluate")
async def evaluate_severity_event(
    request: SeverityEventRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Evaluate a climate severity event and decide whether to trigger payout.
    Automatically attaches cryptographic SHA-256 evidence hash and simulated IPFS CID.
    """
    event = SeverityEvent(
        token_id=request.token_id,
        latitude=request.latitude,
        longitude=request.longitude,
        severity_score=request.severity_score,
        ndvi=request.ndvi,
        soil_moisture=request.soil_moisture,
        source=request.source,
        disaster_type=request.disaster_type,
    )
    result = await oracle.evaluate_event(event, db=db)
    return result


@router.post("/evaluate/triangulated")
async def evaluate_triangulated(
    request: TriangulatedEvalRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Multi-Source Truth Engine:
    Triangulates Satellite (GEE/Sentinel-2) + Physical Ground Stations (INMET) + Media (Defesa Civil).
    Requires a 2-of-3 independent source quorum to approve payout.
    """
    dossier = oracle.build_triangulated_dossier(
        token_id=request.token_id,
        latitude=request.latitude,
        longitude=request.longitude,
        disaster_type=request.disaster_type,
        satellite_data=request.satellite_data,
        ground_data=request.ground_data,
        news_data=request.news_data,
    )

    settlement_result = None
    if dossier.quorum_reached and request.auto_trigger_if_quorum:
        event = SeverityEvent(
            token_id=request.token_id,
            latitude=request.latitude,
            longitude=request.longitude,
            severity_score=3.5 if dossier.corroborating_sources_count == 2 else 5.0,
            ndvi=0.2,
            soil_moisture=0.1,
            source="triangulated_truth_engine",
            disaster_type=request.disaster_type,
            evidence_hash=dossier.evidence_hash,
        )
        settlement_result = await oracle.evaluate_event(event, db=db)

    return {
        "dossier": dossier,
        "quorum_reached": dossier.quorum_reached,
        "corroborating_sources": dossier.corroborating_sources_count,
        "composite_confidence": dossier.composite_confidence,
        "evidence_hash": dossier.evidence_hash,
        "ipfs_cid": dossier.ipfs_cid,
        "settlement": settlement_result,
    }


@router.post("/consensus/submit-signed-vote")
async def submit_signed_vote(
    request: SignedVoteRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Submits an ECDSA cryptographically signed vote from an autonomous validator node (e.g., Akash DePIN node).
    When M-of-N quorum is reached, the oracle settles the payout with proof on-chain.
    """
    vote = SignedOracleVote(
        vote_id=f"vote_{int(datetime.utcnow().timestamp())}_{request.oracle_node_id}",
        token_id=request.token_id,
        oracle_node_id=request.oracle_node_id,
        node_address=request.node_address,
        evidence_hash=request.evidence_hash,
        decision=request.decision,
        payout_bps=request.payout_bps,
        signature=request.signature,
    )
    result = await oracle.submit_signed_vote(vote, db=db)
    return result


@router.get("/evidence/{hash_or_cid}")
async def get_audit_evidence(hash_or_cid: str):
    """
    Public Transparency & Audit Endpoint:
    Returns the canonical JSON dossier of meteorological & satellite evidence by hash or IPFS CID.
    """
    dossier = oracle.get_audit_dossier(hash_or_cid)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence dossier with hash/CID '{hash_or_cid}' not found in active audit registry.",
        )
    return {
        "status": "VERIFIED",
        "hash_or_cid": hash_or_cid,
        "dossier": dossier,
    }


@router.post("/evaluate/batch")
async def evaluate_batch(
    request: BatchEvalRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Evaluate multiple severity events in batch (e.g. from scheduled scan)."""
    events = [
        SeverityEvent(
            token_id=e.token_id,
            latitude=e.latitude,
            longitude=e.longitude,
            severity_score=e.severity_score,
            ndvi=e.ndvi,
            soil_moisture=e.soil_moisture,
            source=e.source,
            disaster_type=e.disaster_type,
        )
        for e in request.events
    ]
    results = await oracle.evaluate_batch(events, db=db)
    return {"results": results, "total": len(results)}


@router.post("/consensus/vote")
async def submit_consensus_vote(
    request: ConsensusVoteRequest,
    current_user: User = Depends(require_admin),
):
    """Legacy endpoint for simple vote counting."""
    event = SeverityEvent(
        token_id=request.event.token_id,
        latitude=request.event.latitude,
        longitude=request.event.longitude,
        severity_score=request.event.severity_score,
        ndvi=request.event.ndvi,
        soil_moisture=request.event.soil_moisture,
        source=request.event.source,
        consensus_required=3,
    )
    result = await oracle.submit_vote(event, request.oracle_id)
    return result


@router.get("/status")
async def get_oracle_status(current_user: User = Depends(require_admin)):
    """Returns the operational status of the Oracle and KMS Signer."""
    return {
        "oracle": oracle.get_status(),
        "kms_signer": kms_signer.get_status(),
    }


@router.get("/history")
async def get_oracle_history(current_user: User = Depends(require_admin)):
    """Returns the history of processed events."""
    return {
        "events": oracle.processed_events[-50:],
        "total": len(oracle.processed_events),
    }

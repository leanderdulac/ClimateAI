"""
Base Blockchain API Endpoints (Coinbase Ethereum L2)
Exposes routes for parametric insurance tokenization (ERC-3525), settlement, and network health on Base.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from blockchain.base.base_service import BaseService, get_base_service
from blockchain.base.climate_policy_service import ClimatePolicyBaseService, get_climate_policy_base_service
from middleware.auth_middleware import require_admin
from models.schemas import User

router = APIRouter(prefix="/blockchain/base", tags=["Base Blockchain (Coinbase L2)"])


class MintPolicyRequest(BaseModel):
    beneficiary_address: str = Field(..., description="EVM wallet address of the insured party")
    coverage_amount_brl: float = Field(..., gt=0, description="Insured coverage amount in BRL")
    disaster_type: str = Field(default="flood", description="Type of risk (flood, drought, frost, windstorm)")
    latitude: float = Field(default=-23.55, ge=-90, le=90)
    longitude: float = Field(default=-46.63, ge=-180, le=180)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Supplemental risk and actuarial details")


class SettlePayoutRequest(BaseModel):
    token_id: int = Field(..., description="On-chain token ID on Base")
    payout_percentage: float = Field(..., ge=0.0, le=1.0, description="Payout ratio (0.0 to 1.0)")
    evidence_hash: str = Field(..., description="0x-prefixed cryptographic SHA-256 proof hash")


@router.get("/status")
async def get_base_status():
    """
    Returns real-time status of the Base blockchain connection,
    including current block height, gas metrics (EIP-1559 base fee), and explorer endpoints.
    """
    service = get_base_service()
    return service.get_status()


@router.get("/balance/{address}")
async def get_address_balance(address: str):
    """
    Queries native ETH and Circle native USDC balances for an address on Base.
    """
    service = get_base_service()
    return service.get_balance(address)


@router.post("/policy/mint")
async def mint_policy_on_base(
    request: MintPolicyRequest,
    current_user: User = Depends(require_admin),
):
    """
    Mints a new semi-fungible ClimatePolicy token on Base Layer-2 representing an approved policy.
    """
    policy_service = get_climate_policy_base_service()
    try:
        record = policy_service.tokenize_policy(
            beneficiary_address=request.beneficiary_address,
            coverage_amount_brl=request.coverage_amount_brl,
            disaster_type=request.disaster_type,
            latitude=request.latitude,
            longitude=request.longitude,
            metadata=request.metadata,
        )
        return {
            "status": "MINTED",
            "blockchain": "Base (Coinbase Ethereum L2)",
            "policy": record,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mint policy on Base: {exc}",
        )


@router.post("/policy/payout")
async def settle_policy_payout_on_base(
    request: SettlePayoutRequest,
    current_user: User = Depends(require_admin),
):
    """
    Executes parametric settlement on Base with cryptographic proof.
    Triggered when the Oracle detects a corroborated climate breach.
    """
    policy_service = get_climate_policy_base_service()
    try:
        tx_result = policy_service.settle_policy_payout(
            token_id=request.token_id,
            payout_percentage=request.payout_percentage,
            evidence_hash=request.evidence_hash,
        )
        return {
            "status": "SETTLED",
            "blockchain": "Base (Coinbase Ethereum L2)",
            "transaction": tx_result,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to settle payout on Base: {exc}",
        )

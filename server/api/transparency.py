from fastapi import APIRouter, HTTPException
from services.transparency_service import TransparencyService
from typing import Dict, Any

router = APIRouter(tags=["Transparency & Audit"])
transparency_service = TransparencyService()

@router.get("/transparency/audit/{tx_hash}", response_model=Dict[str, Any])
async def get_transaction_audit(tx_hash: str):
    """
    Retrieves a public audit trail for a specific blockchain payout.
    Links the transaction to satellite evidence from Google Earth Engine.
    """
    try:
        audit_data = await transparency_service.get_audit_trail(tx_hash)
        if not audit_data:
            raise HTTPException(status_code=404, detail="Audit trail not found")
        return audit_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transparency/vault/stats", response_model=Dict[str, Any])
async def get_vault_stats():
    """
    Returns real-time statistics for the Risk Vault (ERC-4626), 
    including Current APY, TVL, and locked collateral.
    """
    # Mocked for Phase 4
    return {
        "tvl_usdc": 1250000.0,
        "active_collateral": 450000.0,
        "current_apy": "12.4%",
        "total_claims_paid": 85000.0,
        "investor_count": 42
    }

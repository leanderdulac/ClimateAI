from fastapi import APIRouter, HTTPException
from services.carbon_bridge_service import CarbonCreditBridgeService
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter(tags=["Carbon Ecosystem"])
carbon_service = CarbonCreditBridgeService()

class CarbonOffsetRequest(BaseModel):
    amount_usd: float
    beneficiary_address: str
    policy_id: Optional[str] = None

@router.post("/carbon/offset")
async def register_offset(request: CarbonOffsetRequest):
    """
    Triggers an automated carbon offset (credit retirement).
    Usually called by the system when a premium is received.
    """
    result = await carbon_service.retire_carbon_credits(
        request.amount_usd, 
        request.beneficiary_address
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@router.get("/carbon/registries")
def get_registries():
    """Returns the list of supported carbon registries (Verra, Gold Standard, etc)."""
    return carbon_service.get_supported_registries()

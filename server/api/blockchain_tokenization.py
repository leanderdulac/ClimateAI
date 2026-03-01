from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.tokenization_service import TokenizationService

router = APIRouter()
service = TokenizationService()

class MintRequest(BaseModel):
    to: str
    amount: int

@router.post("/mint", response_model=dict)
async def mint_token(request: MintRequest):
    """Mint a ClimateToken to the specified address."""
    try:
        receipt = await service.mint(request.to, request.amount)
        # Handle both Web3 AttributeDict (real) and dict (mock)
        tx_hash = receipt.get("transactionHash") if isinstance(receipt, dict) else receipt.transactionHash
        status = receipt.get("status") if isinstance(receipt, dict) else receipt.status
        
        # Convert bytes to hex string if needed
        if hasattr(tx_hash, 'hex'):
            tx_hash = tx_hash.hex()
        elif isinstance(tx_hash, bytes):
            tx_hash = tx_hash.hex()
            
        return {"tx_hash": tx_hash, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

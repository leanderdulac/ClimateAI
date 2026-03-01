"""
Hathor Blockchain API Endpoints

REST API for Hathor blockchain operations:
- Token creation (mint)
- Token transfers
- Payout execution
- Oracle data queries
- Nano Contract management
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field

from blockchain.hathor.hathor_service import (
    HathorService,
    TransactionResult,
    get_hathor_service,
)
from blockchain.hathor.climate_token_service import (
    ClimateTokenService,
    ClimateToken,
    ClimateTokenMetadata,
    ClimateIndexType,
    TokenStatus,
    get_climate_token_service,
)
from blockchain.hathor.oracle_service import (
    ClimateOracleService,
    ClimateIndex,
    get_climate_oracle_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Hathor Blockchain"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateTokenRequest(BaseModel):
    """Request to create a climate token"""
    name: str = Field(..., description="Token name")
    symbol: str = Field(..., description="Token symbol")
    total_supply: int = Field(..., description="Total token supply")
    index_type: ClimateIndexType = Field(..., description="Climate index type")
    region: str = Field(..., description="Region name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    start_date: str = Field(..., description="Index start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Index end date (YYYY-MM-DD)")
    trigger_value: float = Field(..., description="Trigger threshold value")
    trigger_condition: str = Field(..., pattern="^(above|below)$", description="Trigger condition")
    payout_amount: int = Field(..., description="Payout amount in smallest unit")
    currency: str = Field(default="BRL", description="Currency code")
    oracle_source: str = Field(default="INMET/NOAA", description="Oracle data source")


class CreateTokenResponse(BaseModel):
    """Response from token creation"""
    success: bool
    token_uid: str
    name: str
    symbol: str
    total_supply: int
    tx_hash: str
    explorer_url: str
    message: str


class TransferTokenRequest(BaseModel):
    """Request to transfer tokens"""
    token_uid: str = Field(..., description="Token UID to transfer")
    amount: int = Field(..., gt=0, description="Amount to transfer")
    destination_address: str = Field(..., description="Recipient address")
    message: str = Field(default="", description="Optional memo/message")


class TransferTokenResponse(BaseModel):
    """Response from token transfer"""
    success: bool
    tx_hash: str
    token_uid: str
    amount: int
    destination_address: str
    explorer_url: str
    message: str


class ExecutePayoutRequest(BaseModel):
    """Request to execute token payout"""
    token_uid: str = Field(..., description="Token UID")
    beneficiary_address: str = Field(..., description="Beneficiary wallet address")
    oracle_value: Optional[float] = Field(None, description="Oracle value (auto-fetched if not provided)")


class ExecutePayoutResponse(BaseModel):
    """Response from payout execution"""
    success: bool
    tx_hash: str
    token_uid: str
    payout_amount: int
    beneficiary_address: str
    oracle_value: float
    trigger_value: float
    trigger_met: bool
    explorer_url: str
    message: str


class ClimateIndexRequest(BaseModel):
    """Request to get climate index"""
    index_type: str = Field(..., description="Index type (precipitation, temperature, etc.)")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    trigger_value: float = Field(..., description="Trigger threshold")
    trigger_condition: str = Field(..., pattern="^(above|below)$", description="Trigger condition")
    source: str = Field(default="openmeteo", description="Data source")


class ClimateIndexResponse(BaseModel):
    """Response with climate index data"""
    index_type: str
    region: str
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    index_value: float
    trigger_value: float
    trigger_condition: str
    trigger_met: bool
    data_points_count: int
    calculation_method: str


class TokenInfoResponse(BaseModel):
    """Token information response"""
    token_uid: str
    name: str
    symbol: str
    status: str
    total_supply: int
    index_type: str
    region: str
    trigger_value: float
    trigger_condition: str
    payout_amount: int
    payout_executed: bool
    created_at: str


class WalletBalanceResponse(BaseModel):
    """Wallet balance response"""
    token_uid: str
    available: int
    locked: int
    total: int


# ============================================================================
# API Endpoints
# ============================================================================

from config.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from models.sqlalchemy_models import BlockchainTransaction

@router.post("/tokens/create", response_model=CreateTokenResponse)
async def create_climate_token(
    request: CreateTokenRequest,
    token_service: ClimateTokenService = Depends(lambda: get_climate_token_service()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new climate index token on Hathor blockchain
    
    **Requirements:**
    - Hathor wallet initialized
    - Sufficient HTR for token creation fee (~1 HTR)
    
    **Process:**
    1. Creates native Hathor token
    2. Stores metadata (index type, region, trigger conditions)
    3. Returns token UID for future operations
    """
    try:
        # Create metadata
        metadata = ClimateTokenMetadata(
            index_type=request.index_type,
            region=request.region,
            latitude=request.latitude,
            longitude=request.longitude,
            start_date=request.start_date,
            end_date=request.end_date,
            trigger_value=request.trigger_value,
            trigger_condition=request.trigger_condition,
            payout_amount=request.payout_amount,
            currency=request.currency,
            oracle_source=request.oracle_source,
        )
        
        # Create token
        token = token_service.create_climate_token(
            name=request.name,
            symbol=request.symbol,
            total_supply=request.total_supply,
            metadata=metadata,
        )
        
        # Get last transaction for explorer URL
        # (In production, would get from hathor_service)
        explorer_url = f"https://explorer.testnet.hathor.network/token/{token.token_uid}"
        
        # Persist transaction to DB
        db_tx = BlockchainTransaction(
            tx_hash=token.token_uid,
            token_uid=token.token_uid,
            from_address="platform_admin",
            to_address="platform_admin",
            amount=request.total_supply,
            status="CONFIRMED",
            message=f"Climate token {request.symbol} created",
            explorer_url=explorer_url
        )
        try:
            db.add(db_tx)
            await db.commit()
        except Exception as db_e:
            await db.rollback()
            logger.error(f"Failed to persist Token Creation to DB: {db_e}")
        
        return CreateTokenResponse(
            success=True,
            token_uid=token.token_uid,
            name=token.name,
            symbol=token.symbol,
            total_supply=token.total_supply,
            tx_hash=token.token_uid,  # In production, get actual tx hash
            explorer_url=explorer_url,
            message=f"Climate token {request.symbol} created successfully",
        )
        
    except Exception as e:
        logger.error(f"Failed to create climate token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tokens/transfer", response_model=TransferTokenResponse)
async def transfer_tokens(
    request: TransferTokenRequest,
    hathor_service: HathorService = Depends(lambda: get_hathor_service()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Transfer climate tokens to another address
    
    **Requirements:**
    - Sufficient token balance
    - Valid destination address
    """
    try:
        result = hathor_service.transfer_tokens(
            token_uid=request.token_uid,
            amount=request.amount,
            destination_address=request.destination_address,
            message=request.message,
        )
        
        # Persist transfer to DB
        db_tx = BlockchainTransaction(
            tx_hash=result.tx_hash,
            token_uid=request.token_uid,
            from_address="platform_admin",
            to_address=request.destination_address,
            amount=request.amount,
            status="CONFIRMED",
            message=request.message,
            explorer_url=result.explorer_url
        )
        try:
            db.add(db_tx)
            await db.commit()
        except Exception as db_e:
            await db.rollback()
            logger.error(f"Failed to persist Token Transfer to DB: {db_e}")

        return TransferTokenResponse(
            success=result.success,
            tx_hash=result.tx_hash,
            token_uid=result.token_uid,
            amount=result.amount,
            destination_address=result.address,
            explorer_url=result.explorer_url,
            message=result.message,
        )
        
    except Exception as e:
        logger.error(f"Failed to transfer tokens: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tokens/{token_uid}/payout", response_model=ExecutePayoutResponse)
async def execute_payout(
    token_uid: str,
    request: ExecutePayoutRequest,
    token_service: ClimateTokenService = Depends(lambda: get_climate_token_service()),
    oracle_service: ClimateOracleService = Depends(lambda: get_climate_oracle_service()),
):
    """
    Execute automatic payout for a climate token
    
    **Process:**
    1. Fetch oracle data (if not provided)
    2. Check if trigger condition is met
    3. Execute payout if triggered
    4. Update token status
    
    **Payout Conditions:**
    - Token must be ACTIVE
    - Oracle value must meet trigger condition
    - Sufficient token balance for payout
    """
    try:
        # Get token
        token = token_service.get_token(token_uid)
        if not token:
            raise HTTPException(status_code=404, detail=f"Token not found: {token_uid}")
        
        # Fetch oracle data if not provided
        oracle_value = request.oracle_value
        if oracle_value is None:
            # Calculate index from oracle data
            index = oracle_service.get_climate_index(
                index_type=token.metadata.index_type.value,
                latitude=token.metadata.latitude,
                longitude=token.metadata.longitude,
                start_date=datetime.strptime(token.metadata.start_date, "%Y-%m-%d"),
                end_date=datetime.strptime(token.metadata.end_date, "%Y-%m-%d"),
                trigger_value=token.metadata.trigger_value,
                trigger_condition=token.metadata.trigger_condition,
            )
            oracle_value = index.value
        
        # Execute payout
        result = token_service.execute_payout(
            token_uid=token_uid,
            oracle_value=oracle_value,
            beneficiary_address=request.beneficiary_address,
        )
        
        return ExecutePayoutResponse(
            success=result.success,
            tx_hash=result.tx_hash,
            token_uid=result.token_uid,
            payout_amount=result.amount,
            beneficiary_address=result.address,
            oracle_value=oracle_value,
            trigger_value=token.metadata.trigger_value,
            trigger_met=True,
            explorer_url=result.explorer_url,
            message=f"Payout of {result.amount} executed successfully",
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute payout: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens", response_model=List[TokenInfoResponse])
async def list_tokens(
    status: Optional[str] = Query(None, description="Filter by status"),
    index_type: Optional[str] = Query(None, description="Filter by index type"),
    token_service: ClimateTokenService = Depends(lambda: get_climate_token_service()),
):
    """
    List all climate tokens with optional filters
    """
    try:
        # Convert string filters to enums if provided
        status_enum = TokenStatus(status) if status else None
        index_type_enum = ClimateIndexType(index_type) if index_type else None
        
        tokens = token_service.list_tokens(
            status=status_enum,
            index_type=index_type_enum,
        )
        
        return [
            TokenInfoResponse(
                token_uid=t.token_uid,
                name=t.name,
                symbol=t.symbol,
                status=t.status.value,
                total_supply=t.total_supply,
                index_type=t.metadata.index_type.value,
                region=t.metadata.region,
                trigger_value=t.metadata.trigger_value,
                trigger_condition=t.metadata.trigger_condition,
                payout_amount=t.metadata.payout_amount,
                payout_executed=t.payout_executed,
                created_at=t.created_at.isoformat(),
            )
            for t in tokens
        ]
        
    except Exception as e:
        logger.error(f"Failed to list tokens: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens/{token_uid}", response_model=TokenInfoResponse)
async def get_token_info(
    token_uid: str,
    token_service: ClimateTokenService = Depends(lambda: get_climate_token_service()),
):
    """
    Get detailed information about a climate token
    """
    token = token_service.get_token(token_uid)
    
    if not token:
        raise HTTPException(status_code=404, detail=f"Token not found: {token_uid}")
    
    return TokenInfoResponse(
        token_uid=token.token_uid,
        name=token.name,
        symbol=token.symbol,
        status=token.status.value,
        total_supply=token.total_supply,
        index_type=token.metadata.index_type.value,
        region=token.metadata.region,
        trigger_value=token.metadata.trigger_value,
        trigger_condition=token.metadata.trigger_condition,
        payout_amount=token.metadata.payout_amount,
        payout_executed=token.payout_executed,
        created_at=token.created_at.isoformat(),
    )


@router.post("/oracle/index", response_model=ClimateIndexResponse)
async def get_climate_index(
    request: ClimateIndexRequest,
    oracle_service: ClimateOracleService = Depends(lambda: get_climate_oracle_service()),
):
    """
    Get climate index value and trigger evaluation
    
    **Data Sources:**
    - OpenMeteo (default, free, global)
    - INMET (Brazil only, requires station lookup)
    - NOAA (US, requires API token)
    """
    try:
        index = oracle_service.get_climate_index(
            index_type=request.index_type,
            latitude=request.latitude,
            longitude=request.longitude,
            start_date=datetime.strptime(request.start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(request.end_date, "%Y-%m-%d"),
            trigger_value=request.trigger_value,
            trigger_condition=request.trigger_condition,
            source=request.source,
        )
        
        return ClimateIndexResponse(
            index_type=index.index_type,
            region=index.region,
            latitude=index.latitude,
            longitude=index.longitude,
            start_date=index.start_date.strftime("%Y-%m-%d"),
            end_date=index.end_date.strftime("%Y-%m-%d"),
            index_value=index.value,
            trigger_value=index.trigger_value,
            trigger_condition=index.trigger_condition,
            trigger_met=index.trigger_met,
            data_points_count=len(index.data_points),
            calculation_method=index.calculation_method,
        )
        
    except Exception as e:
        logger.error(f"Failed to get climate index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallet/balance/{token_uid}", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    token_uid: str,
    hathor_service: HathorService = Depends(lambda: get_hathor_service()),
):
    """
    Get wallet balance for a specific token
    """
    try:
        balance = hathor_service.get_balance(token_uid=token_uid)
        
        return WalletBalanceResponse(
            token_uid=balance["token_uid"],
            available=balance["available"],
            locked=balance["locked"],
            total=balance["total"],
        )
        
    except Exception as e:
        logger.error(f"Failed to get balance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction/{tx_hash}")
async def get_transaction_status(
    tx_hash: str,
    hathor_service: HathorService = Depends(lambda: get_hathor_service()),
):
    """
    Get transaction status and confirmations
    """
    try:
        status = hathor_service.get_transaction_status(tx_hash)
        return status
        
    except Exception as e:
        logger.error(f"Failed to get transaction status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Convenience Endpoints for Specific Index Types
# ============================================================================

@router.post("/tokens/create/drought", response_model=CreateTokenResponse)
async def create_drought_token(
    region: str = Query(..., description="Region name"),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    trigger_precipitation_mm: float = Query(..., description="Precipitation threshold (mm)"),
    payout_amount: int = Query(..., description="Payout amount"),
    total_supply: int = Query(default=10_000, description="Total supply"),
    token_service: ClimateTokenService = Depends(lambda: get_climate_token_service()),
):
    """
    Create a drought index token (convenience endpoint)
    
    **Trigger:** Payout when precipitation < trigger_precipitation_mm
    """
    try:
        token = token_service.create_drought_token(
            region=region,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            trigger_precipitation_mm=trigger_precipitation_mm,
            payout_amount=payout_amount,
            total_supply=total_supply,
        )
        
        return CreateTokenResponse(
            success=True,
            token_uid=token.token_uid,
            name=token.name,
            symbol=token.symbol,
            total_supply=token.total_supply,
            tx_hash=token.token_uid,
            explorer_url=f"https://explorer.testnet.hathor.network/token/{token.token_uid}",
            message=f"Drought token created for {region}",
        )
        
    except Exception as e:
        logger.error(f"Failed to create drought token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tokens/create/flood", response_model=CreateTokenResponse)
async def create_flood_token(
    region: str = Query(..., description="Region name"),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    trigger_precipitation_mm: float = Query(..., description="Precipitation threshold (mm)"),
    payout_amount: int = Query(..., description="Payout amount"),
    total_supply: int = Query(default=10_000, description="Total supply"),
    token_service: ClimateTokenService = Depends(lambda: get_climate_token_service()),
):
    """
    Create a flood index token (convenience endpoint)
    
    **Trigger:** Payout when precipitation > trigger_precipitation_mm
    """
    try:
        token = token_service.create_flood_token(
            region=region,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            trigger_precipitation_mm=trigger_precipitation_mm,
            payout_amount=payout_amount,
            total_supply=total_supply,
        )
        
        return CreateTokenResponse(
            success=True,
            token_uid=token.token_uid,
            name=token.name,
            symbol=token.symbol,
            total_supply=token.total_supply,
            tx_hash=token.token_uid,
            explorer_url=f"https://explorer.testnet.hathor.network/token/{token.token_uid}",
            message=f"Flood token created for {region}",
        )
        
    except Exception as e:
        logger.error(f"Failed to create flood token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

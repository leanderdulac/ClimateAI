"""
Climate Token Service

Service for tokenizing climate indices on Hathor Network.
Handles creation, management, and lifecycle of climate tokens.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from blockchain.hathor.hathor_service import (
    HathorService,
    TransactionResult,
    TokenInfo,
    get_hathor_service,
)

logger = logging.getLogger(__name__)


class ClimateIndexType(str, Enum):
    """Types of climate indices"""
    DROUGHT = "drought"
    FLOOD = "flood"
    TEMPERATURE = "temperature"
    PRECIPITATION = "precipitation"
    WIND = "wind"
    HURRICANE = "hurricane"
    FROST = "frost"
    HEATWAVE = "heatwave"


class TokenStatus(str, Enum):
    """Token lifecycle status"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAID_OUT = "paid_out"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ClimateTokenMetadata:
    """Metadata for climate index token"""
    index_type: ClimateIndexType
    region: str
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    trigger_value: float
    trigger_condition: str  # "above" or "below"
    payout_amount: int
    currency: str = "BRL"
    oracle_source: str = ""
    ipfs_hash: str = ""
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClimateToken:
    """Climate Index Token representation"""
    token_uid: str
    name: str
    symbol: str
    total_supply: int
    metadata: ClimateTokenMetadata
    status: TokenStatus = TokenStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    payout_executed: bool = False
    payout_amount: int = 0
    payout_timestamp: Optional[datetime] = None


class ClimateTokenService:
    """
    Service for managing climate index tokens on Hathor.
    
    Features:
    - Create climate tokens with metadata
    - Track token lifecycle
    - Execute payouts based on oracle data
    - Query token information
    """
    
    def __init__(self, hathor_service: Optional[HathorService] = None):
        """
        Initialize Climate Token Service
        
        Args:
            hathor_service: Hathor service instance (uses default if not provided)
        """
        self.hathor = hathor_service or get_hathor_service()
        self.tokens: Dict[str, ClimateToken] = {}
        
        logger.info("ClimateTokenService initialized")
    
    def create_climate_token(
        self,
        name: str,
        symbol: str,
        total_supply: int,
        metadata: ClimateTokenMetadata,
    ) -> ClimateToken:
        """
        Create a new climate index token
        
        Args:
            name: Token name
            symbol: Token symbol
            total_supply: Total token supply
            metadata: Climate index metadata
            
        Returns:
            ClimateToken with details
        """
        try:
            # Prepare metadata for storage
            metadata_dict = {
                "index_type": metadata.index_type.value,
                "region": metadata.region,
                "latitude": metadata.latitude,
                "longitude": metadata.longitude,
                "start_date": metadata.start_date,
                "end_date": metadata.end_date,
                "trigger_value": metadata.trigger_value,
                "trigger_condition": metadata.trigger_condition,
                "payout_amount": metadata.payout_amount,
                "currency": metadata.currency,
                "oracle_source": metadata.oracle_source,
                "version": "1.0",
            }
            
            # Create token on Hathor
            result = self.hathor.create_climate_token(
                name=name,
                symbol=symbol,
                amount=total_supply,
                metadata=metadata_dict,
            )
            
            # Create ClimateToken object
            token = ClimateToken(
                token_uid=result.token_uid,
                name=name,
                symbol=symbol,
                total_supply=total_supply,
                metadata=metadata,
                status=TokenStatus.ACTIVE,
            )
            
            # Store in local registry
            self.tokens[result.token_uid] = token
            
            logger.info(f"Climate token created: {symbol} ({result.token_uid})")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create climate token: {str(e)}")
            raise
    
    def get_token(self, token_uid: str) -> Optional[ClimateToken]:
        """
        Get climate token by UID
        
        Args:
            token_uid: Token UID to retrieve
            
        Returns:
            ClimateToken or None if not found
        """
        return self.tokens.get(token_uid)
    
    def list_tokens(
        self,
        status: Optional[TokenStatus] = None,
        index_type: Optional[ClimateIndexType] = None,
    ) -> List[ClimateToken]:
        """
        List climate tokens with optional filters
        
        Args:
            status: Filter by status
            index_type: Filter by index type
            
        Returns:
            List of matching ClimateTokens
        """
        tokens = list(self.tokens.values())
        
        if status:
            tokens = [t for t in tokens if t.status == status]
        
        if index_type:
            tokens = [t for t in tokens if t.metadata.index_type == index_type]
        
        return tokens
    
    def update_token_status(
        self,
        token_uid: str,
        status: TokenStatus,
    ) -> bool:
        """
        Update token status
        
        Args:
            token_uid: Token to update
            status: New status
            
        Returns:
            True if updated successfully
        """
        if token_uid not in self.tokens:
            return False
        
        self.tokens[token_uid].status = status
        logger.info(f"Token {token_uid} status updated to {status.value}")
        return True
    
    def execute_payout(
        self,
        token_uid: str,
        oracle_value: float,
        beneficiary_address: str,
    ) -> TransactionResult:
        """
        Execute payout for a climate token if trigger conditions are met
        
        Args:
            token_uid: Token to execute payout for
            oracle_value: Current oracle value (e.g., rainfall, temperature)
            beneficiary_address: Address to receive payout
            
        Returns:
            TransactionResult with payout details
        """
        if token_uid not in self.tokens:
            raise ValueError(f"Token not found: {token_uid}")
        
        token = self.tokens[token_uid]
        
        if token.status != TokenStatus.ACTIVE:
            raise ValueError(f"Token not active for payout: {token.status.value}")
        
        # Check if trigger condition is met
        trigger_met = self._check_trigger_condition(
            oracle_value=oracle_value,
            trigger_value=token.metadata.trigger_value,
            condition=token.metadata.trigger_condition,
        )
        
        if not trigger_met:
            logger.info(f"Payout condition not met for token {token_uid}")
            raise ValueError(
                f"Trigger condition not met: {oracle_value} vs {token.metadata.trigger_value}"
            )
        
        # Execute payout
        result = self.hathor.transfer_tokens(
            token_uid=token_uid,
            amount=token.metadata.payout_amount,
            destination_address=beneficiary_address,
            message=f"Payout for climate index {token.symbol}",
        )
        
        # Update token status
        token.payout_executed = True
        token.payout_amount = token.metadata.payout_amount
        token.payout_timestamp = datetime.now()
        token.status = TokenStatus.PAID_OUT
        
        logger.info(
            f"Payout executed for token {token_uid}: "
            f"{token.metadata.payout_amount} to {beneficiary_address[:20]}..."
        )
        
        return result
    
    def _check_trigger_condition(
        self,
        oracle_value: float,
        trigger_value: float,
        condition: str,
    ) -> bool:
        """
        Check if oracle value meets trigger condition
        
        Args:
            oracle_value: Current value from oracle
            trigger_value: Threshold value
            condition: "above" or "below"
            
        Returns:
            True if trigger condition is met
        """
        if condition == "above":
            return oracle_value >= trigger_value
        elif condition == "below":
            return oracle_value <= trigger_value
        else:
            raise ValueError(f"Unknown trigger condition: {condition}")
    
    def melt_tokens(
        self,
        token_uid: str,
        amount: int,
        melt_authority: str,
    ) -> TransactionResult:
        """
        Melt (burn) climate tokens
        
        Args:
            token_uid: Token to melt
            amount: Amount to melt
            melt_authority: Melt authority address
            
        Returns:
            TransactionResult with melt details
        """
        result = self.hathor.melt_tokens(
            token_uid=token_uid,
            amount=amount,
            melt_authority=melt_authority,
        )
        
        # Update local supply tracking
        if token_uid in self.tokens:
            self.tokens[token_uid].total_supply -= amount
        
        logger.info(f"Melted {amount} tokens from {token_uid}")
        return result
    
    def get_token_info(self, token_uid: str) -> TokenInfo:
        """
        Get token information from blockchain
        
        Args:
            token_uid: Token UID to query
            
        Returns:
            TokenInfo with blockchain details
        """
        return self.hathor.get_token_info(token_uid)
    
    def create_drought_token(
        self,
        region: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        trigger_precipitation_mm: float,
        payout_amount: int,
        total_supply: int = 10_000,
    ) -> ClimateToken:
        """
        Create a drought index token (convenience method)
        
        Args:
            region: Region name
            latitude: Region latitude
            longitude: Region longitude
            start_date: Index start date (YYYY-MM-DD)
            end_date: Index end date (YYYY-MM-DD)
            trigger_precipitation_mm: Precipitation threshold (mm)
            payout_amount: Payout amount in smallest unit
            total_supply: Total token supply
            
        Returns:
            ClimateToken for drought index
        """
        metadata = ClimateTokenMetadata(
            index_type=ClimateIndexType.DROUGHT,
            region=region,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            trigger_value=trigger_precipitation_mm,
            trigger_condition="below",  # Drought = precipitation BELOW threshold
            payout_amount=payout_amount,
            currency="BRL",
            oracle_source="INMET/NOAA",
        )
        
        name = f"ClimateWise Drought Index {region} {start_date[:4]}"
        symbol = f"CLMT-DROUGHT-{region[:3].upper()}-{start_date[:4].replace('-', '')}"
        
        return self.create_climate_token(
            name=name,
            symbol=symbol,
            total_supply=total_supply,
            metadata=metadata,
        )
    
    def create_flood_token(
        self,
        region: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        trigger_precipitation_mm: float,
        payout_amount: int,
        total_supply: int = 10_000,
    ) -> ClimateToken:
        """
        Create a flood index token (convenience method)
        
        Args:
            region: Region name
            latitude: Region latitude
            longitude: Region longitude
            start_date: Index start date (YYYY-MM-DD)
            end_date: Index end date (YYYY-MM-DD)
            trigger_precipitation_mm: Precipitation threshold (mm)
            payout_amount: Payout amount in smallest unit
            total_supply: Total token supply
            
        Returns:
            ClimateToken for flood index
        """
        metadata = ClimateTokenMetadata(
            index_type=ClimateIndexType.FLOOD,
            region=region,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            trigger_value=trigger_precipitation_mm,
            trigger_condition="above",  # Flood = precipitation ABOVE threshold
            payout_amount=payout_amount,
            currency="BRL",
            oracle_source="INMET/NOAA",
        )
        
        name = f"ClimateWise Flood Index {region} {start_date[:4]}"
        symbol = f"CLMT-FLOOD-{region[:3].upper()}-{start_date[:4].replace('-', '')}"
        
        return self.create_climate_token(
            name=name,
            symbol=symbol,
            total_supply=total_supply,
            metadata=metadata,
        )
    
    def create_temperature_token(
        self,
        region: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        trigger_temperature_c: float,
        trigger_condition: str,  # "above" for heatwave, "below" for frost
        payout_amount: int,
        total_supply: int = 10_000,
    ) -> ClimateToken:
        """
        Create a temperature index token (convenience method)
        
        Args:
            region: Region name
            latitude: Region latitude
            longitude: Region longitude
            start_date: Index start date (YYYY-MM-DD)
            end_date: Index end date (YYYY-MM-DD)
            trigger_temperature_c: Temperature threshold (°C)
            trigger_condition: "above" (heatwave) or "below" (frost)
            payout_amount: Payout amount in smallest unit
            total_supply: Total token supply
            
        Returns:
            ClimateToken for temperature index
        """
        index_type = (
            ClimateIndexType.HEATWAVE if trigger_condition == "above"
            else ClimateIndexType.FROST
        )
        
        metadata = ClimateTokenMetadata(
            index_type=index_type,
            region=region,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            trigger_value=trigger_temperature_c,
            trigger_condition=trigger_condition,
            payout_amount=payout_amount,
            currency="BRL",
            oracle_source="INMET/NOAA",
        )
        
        name = f"ClimateWise {index_type.value.title()} Index {region} {start_date[:4]}"
        symbol = f"CLMT-{index_type.value.upper()[:4]}-{region[:3].upper()}-{start_date[:4].replace('-', '')}"
        
        return self.create_climate_token(
            name=name,
            symbol=symbol,
            total_supply=total_supply,
            metadata=metadata,
        )


# Singleton instance
climate_token_service = ClimateTokenService()


def get_climate_token_service() -> ClimateTokenService:
    """Get Climate Token Service instance"""
    return climate_token_service

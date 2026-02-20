from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from models.sqlalchemy_models import Base
from datetime import datetime

class RWAPolicy(Base):
    """
    Local persistence for ERC-3525 Semi-Fungible Tokens (Climate Policies).
    Tracks the relationship between the user, the on-chain token, and the satellite data.
    """
    __tablename__ = "rwa_policies"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, unique=True, index=True) # On-chain ID
    slot = Column(Integer, index=True) # ERC-3525 Slot (Risk Type)
    owner_address = Column(String, index=True)
    sum_insured = Column(Float)
    currency = Column(String, default="USDC")
    
    # Discovery data
    latitude = Column(Float)
    longitude = Column(Float)
    severity_score = Column(Float)
    
    # Blockchain status
    tx_hash = Column(String, nullable=True)
    status = Column(String, default="pending") # pending, minted, claimed, expired
    
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RWAVault(Base):
    """
    Local persistence for ERC-4626 Tokenized Vaults.
    Tracks total liquidity and investor positions.
    """
    __tablename__ = "rwa_vaults"

    id = Column(Integer, primary_key=True, index=True)
    contract_address = Column(String, unique=True, index=True)
    name = Column(String)
    symbol = Column(String)
    total_assets = Column(Float, default=0.0)
    locked_collateral = Column(Float, default=0.0)
    apy_estimate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

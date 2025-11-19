"""
Schemas específicos para tokenização de eventos climáticos
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from models.schemas import EventoClimatico, EventoClimaticoTipo


class EventoToken(BaseModel):
    """Modelo para tokens de eventos climáticos"""

    token_id: str
    event_type: EventoClimaticoTipo
    severity_level: int
    latitude: float
    longitude: float
    start_date: datetime
    end_date: Optional[datetime] = None
    intensity: float
    probability: float
    location_hash: str
    temporal_hash: str
    metadata: Dict[str, Any]
    created_at: datetime


class TokenAnalysis(BaseModel):
    """Modelo para análise de tokens"""

    total_tokens: int
    tokens_by_type: Dict[str, int]
    tokens_by_severity: Dict[int, int]
    risk_distribution: Dict[str, float]
    temporal_clusters: List[Dict[str, Any]]
    spatial_clusters: List[Dict[str, Any]]


class TokenGroup(BaseModel):
    """Modelo para grupos de tokens similares"""

    group_id: str
    group_type: str
    tokens: List[str]  # Lista de token_ids
    centroid_location: Dict[str, float]
    average_severity: float
    risk_score: float
    metadata: Dict[str, Any]


class BlockchainToken(BaseModel):
    """Modelo para tokens blockchain de eventos climáticos"""

    token_uid: str
    token_data: Dict[str, Any]
    owner_address: str
    initial_supply: int
    decimals: int


class BlockchainTransaction(BaseModel):
    """Modelo para transações blockchain"""

    tx_id: str
    type: str  # "token_mint", "token_transfer", etc.
    token_uid: Optional[str]
    timestamp: str
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    token_data: Optional[Dict[str, Any]]
    network: str
    status: str


class TokenMintRequest(BaseModel):
    """Modelo para requisição de mint de token"""

    evento: EventoClimatico
    wallet_address: str
    token_supply: int = 1000000
    decimals: int = 0
    metadata: Optional[Dict[str, Any]] = None


class TokenTransferRequest(BaseModel):
    """Modelo para requisição de transferência de token"""

    token_uid: str
    from_address: str
    to_address: str
    amount: int

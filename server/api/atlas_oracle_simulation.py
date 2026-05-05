"""
Atlas Oracle Simulation API Router
Endpoints para simulação de dados reais do Oracle e Blockchain
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.atlas_oracle_simulation_service import atlas_oracle_simulation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/atlas-simulation", tags=["atlas-simulation"])


# ============================================================================
# Response Models
# ============================================================================

class OracleEventResponse(BaseModel):
    """Resposta de evento do Oracle"""
    event_id: str
    token_id: str
    municipio: Optional[str] = None
    uf: Optional[str] = None
    latitude: float
    longitude: float
    disaster_type: str
    severity_score: float
    ndvi: float
    soil_moisture: float
    timestamp: str
    payout_triggered: bool
    payout_percentage: float
    payout_amount: float
    blockchain_tx_id: Optional[str] = None
    status: str


class PortfolioRiskResponse(BaseModel):
    """Resposta de risco de portfólio"""
    summary: Dict[str, Any]
    impacted_policies: List[Dict[str, Any]]
    blockchain_transactions: List[Dict[str, Any]]
    timestamp: str


class OracleStatusResponse(BaseModel):
    """Resposta de status do Oracle"""
    status: str
    mode: str
    total_events_processed: int
    total_payouts_triggered: int
    total_blockchain_transactions: int
    last_update: str
    network: str
    contract_address: str


# ============================================================================
# API Endpoints
# ============================================================================

from config.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from middleware.auth_middleware import require_admin
from models.schemas import User

@router.get("/live-events", response_model=List[OracleEventResponse])
async def get_live_events(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Obter eventos em tempo real (simulados)
    
    **Retorna:**
    - Lista de eventos do Oracle
    - Severity score (1.0-5.0)
    - Status de payout
    - Transações blockchain
    """
    events = await atlas_oracle_simulation.get_live_events(db=db, limit=limit)
    return events


@router.get("/portfolio-risk", response_model=PortfolioRiskResponse)
async def get_portfolio_risk():
    """
    Obter análise de risco de portfólio em tempo real
    
    **Retorna:**
    - Total exposure (valor total de apólices)
    - Potential payout (payout estimado)
    - Impacted policies (apólices afetadas)
    - Blockchain transactions (transações recentes)
    
    **Integração com RealTimeRiskMonitor:**
    Este endpoint é usado pelo componente RealTimeRiskMonitor.tsx
    """
    risk_data = atlas_oracle_simulation.get_portfolio_risk()
    return risk_data


@router.get("/oracle-status", response_model=OracleStatusResponse)
async def get_oracle_status():
    """
    Obter status do serviço Oracle
    
    **Retorna:**
    - Status do serviço
    - Modo de operação (SIMULATION)
    - Total de eventos processados
    - Total de payouts triggerados
    - Transações blockchain
    - Rede (Hathor Testnet Simulated)
    """
    status = atlas_oracle_simulation.get_oracle_status()
    return status


@router.post("/trigger-event", response_model=OracleEventResponse)
async def trigger_new_event(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Triggerar novo evento simulado (para demonstração)
    
    **Uso:**
    - Testar reatividade do frontend
    - Simular novos desastres em tempo real
    - Demonstrar triggers automáticos de payout
    """
    event = await atlas_oracle_simulation.trigger_new_event(db=db)
    return event


@router.get("/demo")
async def get_demo_data(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Obter dados completos para demonstração
    
    **Retorna:**
    - Eventos em tempo real
    - Risco de portfólio
    - Status do Oracle
    - Estatísticas consolidadas
    """
    from sqlalchemy.future import select
    from models.sqlalchemy_models import OracleEvent, BlockchainTransaction
    
    # Calculate stats roughly
    query_events = select(OracleEvent)
    res_events = await db.execute(query_events)
    all_events = res_events.scalars().all()
    
    if not all_events:
        all_events = atlas_oracle_simulation.events
        
    payouts = len([e for e in all_events if e.payout_triggered])
    avg_sev = sum(e.severity_score for e in all_events) / max(1, len(all_events))
    
    live_events = await atlas_oracle_simulation.get_live_events(db=db, limit=10)
    
    return {
        'live_events': live_events,
        'portfolio_risk': atlas_oracle_simulation.get_portfolio_risk(),
        'oracle_status': atlas_oracle_simulation.get_oracle_status(),
        'statistics': {
            'total_events': len(all_events),
            'payouts_triggered': payouts,
            'total_transactions': len(atlas_oracle_simulation.transactions), # fallback to memory
            'average_severity': avg_sev,
        }
    }


@router.get("/health")
async def health_check():
    """Health check do serviço de simulação"""
    return {
        'status': 'healthy',
        'service': 'atlas-oracle-simulation',
        'events_count': len(atlas_oracle_simulation.events),
        'transactions_count': len(atlas_oracle_simulation.transactions),
    }

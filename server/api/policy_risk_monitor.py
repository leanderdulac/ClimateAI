import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from config.database import get_db_session
from services.policy_risk_monitor_service import PolicyRiskMonitorService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["risk-monitor"])

class RiskSummary(BaseModel):
    total_alerts: int
    impacted_policies_count: int
    total_exposure: float
    potential_payout: float
    risk_level: str

class ImpactedPolicy(BaseModel):
    policy_id: str
    policy_number: str
    location: str
    coverage_amount: float
    alert_title: str
    severity: str
    disaster_type: str
    potential_payout: float

class RealTimeRiskResponse(BaseModel):
    timestamp: str
    summary: RiskSummary
    impacted_policies: List[ImpactedPolicy]
    active_alerts: List[Dict[str, Any]]

@router.get("/portfolio-risk", response_model=RealTimeRiskResponse)
async def get_portfolio_risk(db: AsyncSession = Depends(get_db_session)):
    """
    Retorna a análise de risco do portfólio em tempo real com base nos alertas meteorológicos ativos.
    """
    try:
        service = PolicyRiskMonitorService(db)
        analysis = await service.get_real_time_risk_analysis()
        return analysis
    except Exception as e:
        logger.error(f"Error fetching portfolio risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live-alerts")
async def get_live_alerts_impact(db: AsyncSession = Depends(get_db_session)):
    """
    Lista detalhada de alertas e apólices impactadas.
    """
    service = PolicyRiskMonitorService(db)
    return await service.get_real_time_risk_analysis()

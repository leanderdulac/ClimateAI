import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.sqlalchemy_models import Policy, Location, Claim
from services.brazil_disaster_alerts_service import BrazilDisasterAlertService, BrazilDisasterAlert

logger = logging.getLogger(__name__)

class PolicyRiskMonitorService:
    """
    Serviço para monitoramento de risco em tempo real correlacionando 
    alertas meteorológicos com o portfólio de apólices.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alerts_service = BrazilDisasterAlertService()
        
    async def get_real_time_risk_analysis(self) -> Dict[str, Any]:
        """
        Analisa o impacto dos alertas atuais no portfólio de apólices.
        """
        try:
            # 1. Obter alertas ativos (Síncrono pois o serviço usa requests)
            alerts = self.alerts_service.fetch_alerts()
            if not alerts:
                return self._empty_result()
                
            # 2. Obter apólices ativas
            stmt = select(Policy).filter(
                Policy.status == "active",
                Policy.expiration_date >= datetime.now().date()
            )
            result = await self.db.execute(stmt)
            active_policies = result.scalars().all()
            
            if not active_policies:
                return self._empty_result(alerts_count=len(alerts))
                
            # 3. Correlacionar alertas e apólices
            impacted_policies = []
            total_exposure = 0.0
            potential_payout = 0.0
            
            # Mapear alertas por cidade/estado para busca rápida
            alert_map = {} # (city, state) -> alert
            for alert in alerts:
                for city in alert.cities:
                    key = (city.upper(), alert.state.upper())
                    if key not in alert_map:
                        alert_map[key] = []
                    alert_map[key].append(alert)
            
            for policy in active_policies:
                stmt_loc = select(Location).filter(Location.id == policy.location_id)
                res_loc = await self.db.execute(stmt_loc)
                location = res_loc.scalars().first()
                if not location:
                    continue
                    
                key = (location.city.upper() if location.city else "", location.state.upper() if location.state else "")
                relevant_alerts = alert_map.get(key, [])
                
                if relevant_alerts:
                    # Verificar se o tipo de desastre do alerta corresponde ao gatilho da apólice
                    is_impacted = False
                    matching_alert = None
                    
                    for alert in relevant_alerts:
                        # Lógica de match por tipo
                        if self._is_alert_relevant_to_policy(alert, policy):
                            is_impacted = True
                            matching_alert = alert
                            break
                            
                    if is_impacted:
                        impacted_policies.append({
                            "policy_id": policy.id,
                            "policy_number": policy.policy_number,
                            "location": f"{location.city} - {location.state}",
                            "coverage_amount": float(policy.coverage_amount),
                            "alert_title": matching_alert.title,
                            "severity": matching_alert.severity,
                            "disaster_type": matching_alert.disaster_type,
                            "potential_payout": float(policy.coverage_amount) * 0.5 # Estimativa simplificada
                        })
                        total_exposure += float(policy.coverage_amount)
                        potential_payout += float(policy.coverage_amount) * 0.5
            
            return {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_alerts": len(alerts),
                    "impacted_policies_count": len(impacted_policies),
                    "total_exposure": total_exposure,
                    "potential_payout": potential_payout,
                    "risk_level": "High" if len(impacted_policies) > 5 else "Medium" if impacted_policies else "Low"
                },
                "impacted_policies": impacted_policies,
                "active_alerts": [
                    {
                        "alert_id": a.alert_id,
                        "title": a.title,
                        "state": a.state,
                        "severity": a.severity,
                        "type": a.disaster_type
                    } for a in alerts[:10] # Top 10 alertas
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in real-time risk analysis: {e}")
            return self._empty_result(error=str(e))
            
    def _is_alert_relevant_to_policy(self, alert: BrazilDisasterAlert, policy: Policy) -> bool:
        """
        Verifica se o alerta meteorológico é relevante para os gatilhos da apólice.
        """
        # Se for chuva extrema ou inundação, é relevante para a maioria das apólices climáticas
        # que monitoramos (rainfall, flood, drought).
        relevant_types = {
            "Chuva": ["rainfall", "flood", "excessive_rain"],
            "Inundação": ["flood", "rainfall"],
            "Deslizamento": ["rainfall", "geological_risk"],
            "Seca": ["drought", "fire_risk"]
        }
        
        policy_triggers = policy.trigger_conditions or {}
        policy_type = policy.policy_type.lower()
        
        # Match direto por tipo ou se estiver no mapeamento de relevância
        if alert.disaster_type in relevant_types:
            if policy_type in relevant_types[alert.disaster_type]:
                return True
                
        # Fallback genérico para severidade alta
        if alert.severity_level >= 3:
            return True
            
        return False
        
    def _empty_result(self, alerts_count: int = 0, error: Optional[str] = None) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_alerts": alerts_count,
                "impacted_policies_count": 0,
                "total_exposure": 0.0,
                "potential_payout": 0.0,
                "risk_level": "none"
            },
            "impacted_policies": [],
            "error": error
        }

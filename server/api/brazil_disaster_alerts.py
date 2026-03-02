"""
Brazil Disaster Alerts API Router
Endpoints para alertas de desastres naturais no Brasil
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.brazil_disaster_alerts_service import BrazilDisasterAlertService, BrazilDisasterAlert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["brazil-alerts"])

# Instância global do serviço
alerts_service = BrazilDisasterAlertService()


# ============================================================================
# Response Models
# ============================================================================

class BrazilDisasterAlertResponse(BaseModel):
    """Resposta de alerta de desastre"""
    alert_id: str
    title: str
    disaster_type: str
    severity: str
    severity_level: int
    start_time: str
    end_time: Optional[str]
    state: str
    cities: List[str]
    description: str
    source: str
    link: Optional[str]


class BrazilAlertsSummaryResponse(BaseModel):
    """Resumo de alertas"""
    total_alerts: int
    by_state: Dict[str, int]
    by_disaster_type: Dict[str, int]
    by_severity: Dict[str, int]
    sources: List[str]
    last_update: Optional[str]


class BrazilServiceStatusResponse(BaseModel):
    """Status do serviço"""
    service: str
    status: str
    sources: Dict[str, Dict[str, Any]]
    total_alerts_cached: int
    last_update: Optional[str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/fetch", response_model=List[BrazilDisasterAlertResponse])
async def fetch_alerts(
    use_cache: bool = Query(default=True, description="Usar cache se disponível"),
    cache_timeout_minutes: int = Query(default=30, ge=1, description="Tempo de cache em minutos"),
    sources: Optional[str] = Query(default=None, description="Fontes (comma-separated): cemaden,inmet,cptec")
):
    """
    Buscar alertas de desastres de múltiplas fontes
    
    **Fontes:**
    - CEMADEN: Centro Nacional de Monitoramento e Alertas de Desastres Naturais
    - INMET: Alertas meteorológicos (mock - API indisponível)
    - CPTEC: Previsão de tempo severo
    
    **Tipos de Desastres:**
    - Chuva
    - Deslizamento
    - Seca
    - Inundação
    - Tempestade
    """
    try:
        sources_list = sources.split(',') if sources else None
        alerts = alerts_service.fetch_alerts(use_cache, cache_timeout_minutes, sources_list)
        
        return [
            BrazilDisasterAlertResponse(
                alert_id=a.alert_id,
                title=a.title,
                disaster_type=a.disaster_type,
                severity=a.severity,
                severity_level=a.severity_level,
                start_time=a.start_time.isoformat(),
                end_time=a.end_time.isoformat() if a.end_time else None,
                state=a.state,
                cities=a.cities,
                description=a.description,
                source=a.source,
                link=a.link
            )
            for a in alerts
        ]
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/active", response_model=List[BrazilDisasterAlertResponse])
async def get_active_alerts(
    state: Optional[str] = Query(default=None, description="Estado (UF)"),
    city: Optional[str] = Query(default=None, description="Cidade"),
    disaster_type: Optional[str] = Query(default=None, description="Tipo de desastre"),
    severity_level: Optional[int] = Query(default=None, ge=1, le=4, description="Severidade mínima (1-4)")
):
    """
    Obter alertas ativos com filtros
    
    **Filtros:**
    - state: Estado (ex: SP, RJ, RS)
    - city: Cidade (busca parcial)
    - disaster_type: Chuva, Deslizamento, Seca, etc
    - severity_level: 1=Baixo, 2=Médio, 3=Alto, 4=Muito Alto
    """
    try:
        alerts = alerts_service.get_active_alerts(
            state=state,
            city=city,
            disaster_type=disaster_type,
            severity_level=severity_level
        )
        
        return [
            BrazilDisasterAlertResponse(
                alert_id=a.alert_id,
                title=a.title,
                disaster_type=a.disaster_type,
                severity=a.severity,
                severity_level=a.severity_level,
                start_time=a.start_time.isoformat(),
                end_time=a.end_time.isoformat() if a.end_time else None,
                state=a.state,
                cities=a.cities,
                description=a.description,
                source=a.source,
                link=a.link
            )
            for a in alerts
        ]
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/summary", response_model=BrazilAlertsSummaryResponse)
async def get_alerts_summary():
    """
    Obter resumo dos alertas
    
    **Inclui:**
    - Total de alertas
    - Por estado
    - Por tipo de desastre
    - Por severidade
    """
    try:
        summary = alerts_service.get_alerts_summary()
        
        return BrazilAlertsSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting alerts summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/by-state")
async def get_alerts_by_state():
    """
    Obter alertas agrupados por estado
    """
    try:
        grouped = alerts_service.get_alerts_by_state()
        
        return {
            state: [
                {
                    'alert_id': a.alert_id,
                    'title': a.title,
                    'disaster_type': a.disaster_type,
                    'severity': a.severity,
                    'cities': a.cities
                }
                for a in alerts
            ]
            for state, alerts in grouped.items()
        }
        
    except Exception as e:
        logger.error(f"Error grouping alerts by state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/status", response_model=BrazilServiceStatusResponse)
async def get_service_status():
    """
    Obter status do serviço de alertas
    """
    try:
        status = alerts_service.get_service_status()
        
        return BrazilServiceStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/example")
async def get_example_alert():
    """
    Obter exemplo de alerta para referência
    """
    return {
        "example": {
            "alert_id": "CEMADEN-001",
            "title": "Alerta de Chuva - Alto",
            "disaster_type": "Chuva",
            "severity": "Alto",
            "severity_level": 3,
            "start_time": "2026-02-16T10:00:00",
            "end_time": "2026-02-16T22:00:00",
            "state": "SP",
            "cities": ["São Paulo", "Guarulhos", "Osasco"],
            "description": "Alerta de chuva intensa para região metropolitana de São Paulo",
            "source": "CEMADEN",
            "link": "http://www.cemaden.gov.br/dados-abertos/"
        },
        "severity_levels": {
            "1": "Baixo",
            "2": "Médio",
            "3": "Alto",
            "4": "Muito Alto"
        },
        "disaster_types": [
            "Chuva",
            "Deslizamento",
            "Inundação",
            "Seca",
            "Tempestade",
            "Granizo",
            "Vendaval"
        ],
        "data_sources": {
            "CEMADEN": "Centro Nacional de Monitoramento e Alertas de Desastres Naturais",
            "INMET": "Instituto Nacional de Meteorologia (mock - API indisponível)",
            "CPTEC": "Centro de Previsão de Tempo e Estudos Climáticos"
        }
    }

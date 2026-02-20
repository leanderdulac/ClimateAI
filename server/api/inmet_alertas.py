"""
INMET Alertas RSS API Router
Endpoints para alertas meteorológicos do INMET
"""

import logging
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.inmet_alertas_service import INMETAlertService, INMETAlert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/inmet-alertas", tags=["inmet-alertas"])

# Instância global do serviço
alertas_service = INMETAlertService()


# ============================================================================
# Response Models
# ============================================================================

class INMETAlertResponse(BaseModel):
    """Resposta de alerta do INMET"""
    alert_id: str
    title: str
    event_type: str
    severity: str
    severity_level: int
    start_time: str
    end_time: str
    description: str
    affected_areas: List[str]
    link: str
    published: str
    source: str


class INMETAlertsSummaryResponse(BaseModel):
    """Resumo de alertas"""
    total_alerts: int
    active_alerts: int
    by_severity: Dict[str, int]
    by_event_type: Dict[str, int]
    last_update: Optional[str]


class INMETServiceStatusResponse(BaseModel):
    """Status do serviço"""
    service: str
    status: str
    feed_url: str
    total_alerts_cached: int
    last_update: Optional[str]
    cache_timeout_minutes: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/fetch", response_model=List[INMETAlertResponse])
async def fetch_alerts(
    use_cache: bool = Query(default=True, description="Usar cache se disponível"),
    cache_timeout_minutes: int = Query(default=15, ge=1, description="Tempo de cache em minutos")
):
    """
    Buscar alertas do feed RSS do INMET
    
    **Fontes:**
    - INMET Alertas RSS: https://alertas2.inmet.gov.br/rss
    
    **Tipos de Alertas:**
    - Chuvas Intensas
    - Baixa Umidade
    - Ventos Costeiros
    - Tempestade
    - Declínio de Temperatura
    - Acumulado de Chuva
    
    **Severidade:**
    - Perigo Potencial (Amarelo)
    - Perigo (Laranja)
    - Grande Perigo (Vermelho)
    """
    try:
        alerts = alertas_service.fetch_alerts(use_cache, cache_timeout_minutes)
        
        return [
            INMETAlertResponse(
                alert_id=a.alert_id,
                title=a.title,
                event_type=a.event_type,
                severity=a.severity,
                severity_level=a.severity_level,
                start_time=a.start_time.isoformat(),
                end_time=a.end_time.isoformat(),
                description=a.description,
                affected_areas=a.affected_areas,
                link=a.link,
                published=a.published.isoformat(),
                source=a.source
            )
            for a in alerts
        ]
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")


@router.get("/active", response_model=List[INMETAlertResponse])
async def get_active_alerts(
    event_type: Optional[str] = Query(default=None, description="Filtrar por tipo de evento"),
    severity_level: Optional[int] = Query(default=None, ge=1, le=3, description="Nível mínimo de severidade (1-3)"),
    location: Optional[str] = Query(default=None, description="Filtrar por localização")
):
    """
    Obter alertas ativos com filtros opcionais
    
    **Filtros:**
    - event_type: Chuvas Intensas, Baixa Umidade, Tempestade, etc
    - severity_level: 1=Perigo Potencial, 2=Perigo, 3=Grande Perigo
    - location: Busca parcial no nome da área afetada
    """
    try:
        alerts = alertas_service.get_active_alerts(
            event_type=event_type,
            severity_level=severity_level,
            location=location
        )
        
        return [
            INMETAlertResponse(
                alert_id=a.alert_id,
                title=a.title,
                event_type=a.event_type,
                severity=a.severity,
                severity_level=a.severity_level,
                start_time=a.start_time.isoformat(),
                end_time=a.end_time.isoformat(),
                description=a.description,
                affected_areas=a.affected_areas,
                link=a.link,
                published=a.published.isoformat(),
                source=a.source
            )
            for a in alerts
        ]
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/summary", response_model=INMETAlertsSummaryResponse)
async def get_alerts_summary():
    """
    Obter resumo dos alertas
    
    **Inclui:**
    - Total de alertas
    - Alertas ativos
    - Contagem por severidade
    - Contagem por tipo de evento
    """
    try:
        summary = alertas_service.get_alerts_summary()
        
        return INMETAlertsSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting alerts summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/by-severity")
async def get_alerts_by_severity():
    """
    Obter alertas agrupados por severidade
    
    **Retorna:**
    - Perigo Potencial (Amarelo)
    - Perigo (Laranja)
    - Grande Perigo (Vermelho)
    """
    try:
        grouped = alertas_service.get_alerts_by_severity()
        
        return {
            severity: [
                {
                    'alert_id': a.alert_id,
                    'title': a.title,
                    'event_type': a.event_type,
                    'start_time': a.start_time.isoformat(),
                    'end_time': a.end_time.isoformat(),
                    'affected_areas': a.affected_areas
                }
                for a in alerts
            ]
            for severity, alerts in grouped.items()
        }
        
    except Exception as e:
        logger.error(f"Error grouping alerts by severity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/status", response_model=INMETServiceStatusResponse)
async def get_service_status():
    """
    Obter status do serviço de alertas
    """
    try:
        status = alertas_service.get_service_status()
        
        return INMETServiceStatusResponse(**status)
        
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
            "alert_id": "53326",
            "title": "Aviso de Chuvas Intensas. Severidade Grau: Perigo Potencial",
            "event_type": "Chuvas Intensas",
            "severity": "Perigo Potencial",
            "severity_level": 1,
            "start_time": "2026-02-16T09:00:00",
            "end_time": "2026-02-17T23:59:00",
            "description": "INMET publica aviso iniciando em: 16/02/2026 09:00. Chuva entre 20 e 30 mm/h ou até 50 mm/dia, ventos intensos (40-60 km/h). Baixo risco de corte de energia elétrica, queda de galhos de árvores, alagamentos e de descargas elétricas.",
            "affected_areas": [
                "Centro Goiano",
                "Leste Goiano",
                "Nordeste Paraense",
                "Serrana",
                "Oeste Catarinense"
            ],
            "link": "https://alertas2.inmet.gov.br/53326",
            "published": "2026-02-16T09:00:00",
            "source": "INMET"
        },
        "severity_levels": {
            "1": "Perigo Potencial (Amarelo)",
            "2": "Perigo (Laranja)",
            "3": "Grande Perigo (Vermelho)"
        },
        "event_types": [
            "Chuvas Intensas",
            "Baixa Umidade",
            "Ventos Costeiros",
            "Tempestade",
            "Declínio de Temperatura",
            "Acumulado de Chuva",
            "Onda de Calor",
            "Granizo"
        ]
    }

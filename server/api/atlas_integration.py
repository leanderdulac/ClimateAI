"""
Atlas Integration API Router
Endpoints para integrar dados do Atlas com Oracle e Precificação
"""

import logging
from typing import Dict, Any, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from services.atlas_integration_service import (
    AtlasIntegrationService,
    HistoricalRiskProfile,
    OracleBaselineEvent,
)
from services.atlas_disaster_service import AtlasDisasterService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/atlas-integration", tags=["atlas-integration"])

# Instâncias dos serviços
atlas_service = AtlasDisasterService()
integration_service = AtlasIntegrationService(
    atlas_service=atlas_service
)


# ============================================================================
# Request/Response Models
# ============================================================================

class HistoricalRiskRequest(BaseModel):
    """Requisição para cálculo de perfil de risco histórico"""
    municipio: str = Field(..., description="Nome do município")
    uf: str = Field(..., description="Sigla da UF", max_length=2)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    ano_inicio: int = Field(default=1991, ge=1900, le=2100)
    ano_fim: int = Field(default=2024, ge=1900, le=2100)


class HistoricalRiskResponse(BaseModel):
    """Resposta com perfil de risco histórico"""
    municipio: str
    uf: str
    total_eventos: int
    eventos_por_ano: float
    tipo_mais_comum: str
    severidade_media: float
    severidade_maxima: float
    total_mortes: int
    total_afetados: int
    total_prejuizo: float
    tendencia_crescimento: float
    risk_score: float
    risk_category: str
    periodo_analise: Tuple[int, int]


class OracleBaselineRequest(BaseModel):
    """Requisição para geração de baseline do Oracle"""
    municipio: str
    uf: str
    latitude: float
    longitude: float
    token_id: Optional[int] = None
    disaster_type: Optional[str] = None


class OracleBaselineResponse(BaseModel):
    """Resposta com baseline do Oracle"""
    event_id: str
    token_id: Optional[int]
    municipio: str
    uf: str
    disaster_type: str
    severity_score: float
    severity_category: str
    severity_percentile: float
    annual_probability: float
    return_period_years: float
    payout_threshold_severity: float
    payout_percentage: float
    expected_mortes: float
    expected_afetados: float
    expected_prejuizo: float


class PricingAdjustmentRequest(BaseModel):
    """Requisição para ajuste de precificação"""
    base_premium: float = Field(..., gt=0)
    municipio: str
    uf: str
    latitude: float
    longitude: float
    coverage_amount: float = Field(..., gt=0)


class PricingAdjustmentResponse(BaseModel):
    """Resposta com ajuste de precificação"""
    base_premium: float
    adjusted_premium: float
    composite_factor: float
    risk_score: float
    risk_category: str
    expected_loss_ratio: float
    expected_losses: float
    factors: Dict[str, float]


class RealTimeEventRequest(BaseModel):
    """Requisição para cross-check de evento em tempo real"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    real_time_severity: float = Field(..., ge=1.0, le=5.0)
    disaster_type: str


class RealTimeEventResponse(BaseModel):
    """Resposta com análise de evento em tempo real"""
    real_time_severity: float
    baseline_severity: float
    severity_difference: float
    severity_ratio: float
    current_percentile: float
    payout_triggered: bool
    payout_percentage: float
    payout_threshold: float
    recommendation: str
    historical_context: Dict[str, Any]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/risk-profile", response_model=HistoricalRiskResponse)
async def calculate_historical_risk(request: HistoricalRiskRequest):
    """
    Calcular perfil de risco histórico baseado em dados do Atlas
    
    **Retorna:**
    - Total de eventos históricos
    - Severidade média e máxima
    - Impacto humano e econômico
    - Tendência temporal
    - Risk score (0-10) e categoria
    """
    try:
        profile = integration_service.calculate_historical_risk_profile(
            municipio=request.municipio,
            uf=request.uf,
            latitude=request.latitude,
            longitude=request.longitude,
            anos=(request.ano_inicio, request.ano_fim),
        )
        
        return HistoricalRiskResponse(
            municipio=profile.municipio,
            uf=profile.uf,
            total_eventos=profile.total_eventos,
            eventos_por_ano=profile.eventos_por_ano,
            tipo_mais_comum=profile.tipo_mais_comum,
            severidade_media=profile.severidade_media,
            severidade_maxima=profile.severidade_maxima,
            total_mortes=profile.total_mortes,
            total_afetados=profile.total_afetados,
            total_prejuizo=profile.total_prejuizo,
            tendencia_crescimento=profile.tendencia_crescimento,
            risk_score=profile.risk_score,
            risk_category=profile.risk_category,
            periodo_analise=profile.periodo_analise,
        )
    except Exception as e:
        logger.error(f"Erro ao calcular perfil de risco: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular perfil de risco: {str(e)}"
        )


@router.post("/oracle-baseline", response_model=OracleBaselineResponse)
async def generate_oracle_baseline(request: OracleBaselineRequest):
    """
    Gerar baseline para Oracle baseada em dados históricos
    
    **Uso:**
    - Configurar thresholds de payout para seguros paramétricos
    - Definir severidade mínima para triggers automáticos
    - Calcular períodos de retorno de eventos
    """
    try:
        # Calcular perfil de risco
        profile = integration_service.calculate_historical_risk_profile(
            municipio=request.municipio,
            uf=request.uf,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        
        # Gerar baseline
        baseline = integration_service.generate_oracle_baseline(
            risk_profile=profile,
            token_id=request.token_id,
            disaster_type=request.disaster_type,
        )
        
        return OracleBaselineResponse(
            event_id=baseline.event_id,
            token_id=baseline.token_id,
            municipio=baseline.municipio,
            uf=baseline.uf,
            disaster_type=baseline.disaster_type,
            severity_score=baseline.severity_score,
            severity_category=baseline.severity_category,
            severity_percentile=baseline.severity_percentile,
            annual_probability=baseline.annual_probability,
            return_period_years=baseline.return_period_years,
            payout_threshold_severity=baseline.payout_threshold_severity,
            payout_percentage=baseline.payout_percentage,
            expected_mortes=baseline.expected_mortes,
            expected_afetados=baseline.expected_afetados,
            expected_prejuizo=baseline.expected_prejuizo,
        )
    except Exception as e:
        logger.error(f"Erro ao gerar baseline do Oracle: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar baseline: {str(e)}"
        )


@router.post("/pricing-adjustment", response_model=PricingAdjustmentResponse)
async def adjust_pricing_for_historical_risk(request: PricingAdjustmentRequest):
    """
    Ajustar precificação baseada em risco histórico do Atlas
    
    **Fatores de ajuste:**
    - Frequência de eventos históricos
    - Severidade média
    - Tendência de crescimento
    - Impacto humanitário (mortes)
    
    **Retorna:**
    - Prêmio ajustado
    - Fatores de ajuste individuais
    - Loss ratio esperado
    """
    try:
        # Calcular perfil de risco
        profile = integration_service.calculate_historical_risk_profile(
            municipio=request.municipio,
            uf=request.uf,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        
        # Ajustar precificação
        result = integration_service.adjust_pricing_for_historical_risk(
            base_premium=request.base_premium,
            risk_profile=profile,
            coverage_amount=request.coverage_amount,
        )
        
        return PricingAdjustmentResponse(
            base_premium=result['base_premium'],
            adjusted_premium=result['adjusted_premium'],
            composite_factor=result['composite_factor'],
            risk_score=result['risk_score'],
            risk_category=result['risk_category'],
            expected_loss_ratio=result['expected_loss_ratio'],
            expected_losses=result['expected_losses'],
            factors=result['factors'],
        )
    except Exception as e:
        logger.error(f"Erro ao ajustar precificação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ajustar precificação: {str(e)}"
        )


@router.post("/real-time-cross-check", response_model=RealTimeEventResponse)
async def cross_check_real_time_event(request: RealTimeEventRequest):
    """
    Cross-check de evento em tempo real com baseline histórica
    
    **Uso:**
    - Validar se evento atual justifica payout
    - Comparar severidade atual com histórico
    - Decisão automática de trigger
    
    **Integração com Oracle:**
    - Usa baseline histórica como referência
    - Calcula percentil do evento atual
    - Decide payout baseado em threshold
    """
    try:
        result = integration_service.cross_check_real_time_event(
            real_time_severity=request.real_time_severity,
            latitude=request.latitude,
            longitude=request.longitude,
            disaster_type=request.disaster_type,
        )
        
        return RealTimeEventResponse(
            real_time_severity=result['real_time_severity'],
            baseline_severity=result['baseline_severity'],
            severity_difference=result['severity_difference'],
            severity_ratio=result['severity_ratio'],
            current_percentile=result['current_percentile'],
            payout_triggered=result['payout_triggered'],
            payout_percentage=result['payout_percentage'],
            payout_threshold=result['payout_threshold'],
            recommendation=result['recommendation'],
            historical_context=result['historical_context'],
        )
    except Exception as e:
        logger.error(f"Erro no cross-check: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro no cross-check: {str(e)}"
        )


@router.get("/summary/{municipio}/{uf}")
async def get_integration_summary(
    municipio: str,
    uf: str,
    ano_inicio: int = Query(default=1991, ge=1900),
    ano_fim: int = Query(default=2024, ge=1900),
):
    """
    Obter resumo completo da integração para um município
    
    **Retorna:**
    - Resumo do perfil de risco
    - Baseline do Oracle
    - Fatores de ajuste de pricing
    """
    try:
        # Coordenadas aproximadas (em produção, usar geocoding)
        lat, lon = integration_service._get_nearest_municipio_coords(municipio, uf)
        
        # Calcular perfil de risco
        profile = integration_service.calculate_historical_risk_profile(
            municipio=municipio,
            uf=uf,
            latitude=lat,
            longitude=lon,
            anos=(ano_inicio, ano_fim),
        )
        
        # Gerar baseline
        baseline = integration_service.generate_oracle_baseline(
            risk_profile=profile,
        )
        
        # Resumo
        return {
            "municipio": municipio,
            "uf": uf,
            "periodo_analise": f"{ano_inicio}-{ano_fim}",
            "risk_profile": {
                "total_eventos": profile.total_eventos,
                "risk_score": profile.risk_score,
                "risk_category": profile.risk_category,
                "tipo_mais_comum": profile.tipo_mais_comum,
            },
            "oracle_baseline": {
                "severity_score": baseline.severity_score,
                "payout_threshold": baseline.payout_threshold_severity,
                "return_period_years": baseline.return_period_years,
            },
            "pricing_guidance": {
                "recommended_factor": 1.0 + (profile.risk_score / 10.0),
                "expected_loss_ratio": baseline.expected_mortes / max(1, profile.total_eventos),
            },
        }
    except Exception as e:
        logger.error(f"Erro ao obter resumo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter resumo: {str(e)}"
        )


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Verificar saúde do serviço de integração"""
    return {
        "status": "healthy",
        "atlas_service_available": atlas_service is not None,
        "integration_service_available": integration_service is not None,
        "cache_size": len(integration_service._risk_cache),
    }

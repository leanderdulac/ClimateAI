"""
Unified Earth-Space Platform API Router
Endpoints para plataforma unificada Terra-Espaço
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Query, Body, HTTPException
from pydantic import BaseModel, Field

from services.unified_earth_space_platform import (
    unified_platform,
    UnifiedRiskAssessment,
    IntegratedInsuranceProduct,
    RiskDomain,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified-platform", tags=["unified-platform"])


class RiskAssessmentRequest(BaseModel):
    """Requisição para avaliação de risco unificada"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude_km: float = Field(default=0.0, ge=0, le=36000)
    include_space: bool = True
    include_atmosphere: bool = True
    include_surface: bool = True


class RiskAssessmentResponse(BaseModel):
    """Resposta de avaliação de risco"""
    assessment_id: str
    timestamp: str
    location: Dict[str, float]
    space_risk: Optional[Dict[str, Any]]
    atmospheric_risk: Optional[Dict[str, Any]]
    surface_risk: Optional[Dict[str, Any]]
    composite_risk_score: float
    composite_risk_level: str
    cross_domain_correlations: List[Dict[str, Any]]
    recommendations: List[str]
    data_sources: List[str]
    confidence_score: float


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def get_unified_risk_assessment(request: RiskAssessmentRequest):
    """
    Obter avaliação unificada de risco Terra-Espaço
    
    **Camadas analisadas:**
    - SPACE: Satélites, conjunções, clima espacial (CelesTrak)
    - ATMOSPHERE: Clima em tempo real (OpenMeteo)
    - SURFACE: Desastres históricos (Atlas Digital)
    
    **Altitude:**
    - 0-10 km: Superfície (foco em desastres terrestres)
    - 10-100 km: Atmosfera (foco em clima)
    - 100+ km: Órbita (foco em espaço)
    """
    try:
        assessment = unified_platform.get_unified_risk_assessment(
            latitude=request.latitude,
            longitude=request.longitude,
            altitude_km=request.altitude_km,
            include_space=request.include_space,
            include_atmosphere=request.include_atmosphere,
            include_surface=request.include_surface,
        )
        
        return RiskAssessmentResponse(
            assessment_id=assessment.assessment_id,
            timestamp=assessment.timestamp.isoformat(),
            location=assessment.location,
            space_risk=assessment.space_risk,
            atmospheric_risk=assessment.atmospheric_risk,
            surface_risk=assessment.surface_risk,
            composite_risk_score=assessment.composite_risk_score,
            composite_risk_level=assessment.composite_risk_level,
            cross_domain_correlations=assessment.cross_domain_correlations,
            recommendations=assessment.recommendations,
            data_sources=assessment.data_sources,
            confidence_score=assessment.confidence_score,
        )
    except Exception as e:
        logger.error(f"Error in risk assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insurance-products")
async def get_integrated_insurance_products():
    """
    Obter produtos de seguro integrados Terra-Espaço
    
    **Produtos disponíveis:**
    1. Earth-Space Comprehensive Coverage
    2. Satellite Operator Bundle
    3. Climate Resilience Package
    """
    products = unified_platform.get_integrated_insurance_products()
    
    return {
        'total_products': len(products),
        'products': [
            {
                'product_id': p.product_id,
                'name': p.name,
                'description': p.description,
                'covered_domains': [d.value for d in p.covered_domains],
                'trigger_count': len(p.triggers),
                'base_premium_rate': p.premium_calculation.get('base_rate', 0),
            }
            for p in products
        ],
    }


@router.get("/product/{product_id}")
async def get_insurance_product_details(product_id: str):
    """
    Obter detalhes completos de um produto de seguro
    """
    products = unified_platform.get_integrated_insurance_products()
    
    for p in products:
        if p.product_id == product_id:
            return {
                'product_id': p.product_id,
                'name': p.name,
                'description': p.description,
                'covered_domains': [d.value for d in p.covered_domains],
                'triggers': p.triggers,
                'payout_structure': p.payout_structure,
                'premium_calculation': p.premium_calculation,
                'required_data_sources': p.required_data_sources,
            }
    
    raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@router.get("/dashboard-summary")
async def get_dashboard_summary():
    """
    Resumo para dashboard unificado
    
    **Retorna:**
    - Status de todas as camadas
    - Alertas ativos
    - Produtos disponíveis
    - Estatísticas consolidadas
    """
    # Obter status de cada serviço
    atlas_status = "available"  # Mock
    celestrak_status = "available"  # Mock
    openmeteo_status = "available"  # Mock
    
    # Contar alertas ativos (mock)
    active_alerts = {
        'space': 2,
        'atmosphere': 5,
        'surface': 3,
    }
    
    return {
        'platform_status': 'operational',
        'layers': {
            'space': {
                'status': celestrak_status,
                'active_alerts': active_alerts['space'],
                'data_source': 'CelesTrak',
            },
            'atmosphere': {
                'status': openmeteo_status,
                'active_alerts': active_alerts['atmosphere'],
                'data_source': 'OpenMeteo',
            },
            'surface': {
                'status': atlas_status,
                'active_alerts': active_alerts['surface'],
                'data_source': 'Atlas Digital',
            },
        },
        'products_available': len(unified_platform.get_integrated_insurance_products()),
        'total_data_sources': 3,
        'last_update': None,  # Will be set by frontend
    }


@router.get("/health")
async def health_check():
    """Health check da plataforma unificada"""
    return {
        'status': 'healthy',
        'service': 'unified-earth-space-platform',
        'version': '1.0.0',
        'capabilities': [
            'risk_assessment',
            'insurance_products',
            'cross_domain_analysis',
            'multi_layer_oracle',
        ],
    }

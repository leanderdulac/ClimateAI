"""
Microsegmentation Router - Endpoints para análise de microsegmentação geográfica
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from services.audit_service import log_operation
from services.microsegmentation_service import (
    analyze_location_risk,
    create_microsegments,
    get_microsegmentation_summary,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create")
async def create_microsegments_endpoint(
    region_bounds: Dict[str, Any],
    n_segments: int = Query(20, description="Número de microsegmentos"),
) -> Dict[str, Any]:
    """
    Criar microsegmentos para uma região geográfica

    Args:
        region_bounds: Limites e características da região
        n_segments: Número de microsegmentos a criar

    Returns:
        Definições dos microsegmentos criados
    """
    try:
        result = create_microsegments(region_bounds, n_segments)
        return result
    except Exception as e:
        logger.error(f"Erro ao criar microsegmentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro microsegmentação: {str(e)}")


@router.get("/analyze-location")
async def analyze_location_risk_endpoint(
    latitude: float,
    longitude: float,
    region_id: str = Query("default", description="ID da região"),
) -> Dict[str, Any]:
    """
    Analisar risco de uma localização específica usando microsegmentação

    Args:
        latitude: Latitude da localização
        longitude: Longitude da localização
        region_id: ID da região para análise

    Returns:
        Análise de risco detalhada para a localização
    """
    try:
        result = analyze_location_risk(latitude, longitude, region_id)

        # Registrar operação de auditoria
        log_operation(
            operation="microsegmentation_analysis",
            resource_type="location_risk",
            action="analyze",
            status="success",
            resource_id=f"lat_{latitude}_lon_{longitude}",
            details={
                "latitude": latitude,
                "longitude": longitude,
                "region_id": region_id,
                "risk_score": result.get("risk_score", 0),
                "segment_id": result.get("segment_id"),
            },
            risk_score=result.get("risk_score", 0),
        )

        return result
    except Exception as e:
        # Registrar erro de auditoria
        log_operation(
            operation="microsegmentation_analysis",
            resource_type="location_risk",
            action="analyze",
            status="error",
            resource_id=f"lat_{latitude}_lon_{longitude}",
            details={"error": str(e), "latitude": latitude, "longitude": longitude},
            compliance_flags=["microsegmentation_error"],
        )
        logger.error(f"Erro ao analisar risco da localização: {e}")
        raise HTTPException(status_code=500, detail=f"Erro análise risco: {str(e)}")


@router.get("/summary")
async def get_microsegmentation_summary_endpoint(
    region_id: str = Query("default", description="ID da região")
) -> Dict[str, Any]:
    """
    Obter resumo estatístico da análise de microsegmentação

    Args:
        region_id: ID da região

    Returns:
        Estatísticas resumidas da microsegmentação
    """
    try:
        result = get_microsegmentation_summary(region_id)
        return result
    except Exception as e:
        logger.error(f"Erro ao obter resumo de microsegmentação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro resumo: {str(e)}")

"""
API Router for xAI Grok Integration Service
Provides natural language processing and analysis capabilities to complement
the specialized climate risk AI system already implemented
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.grok_integration_service import (
    GrokAnalysisResult,
    GrokIntegrationService,
)

router = APIRouter()

# Instância global do serviço
grok_service = GrokIntegrationService()


class ClimateAnalysisRequest(BaseModel):
    data: Dict[str, Any]
    analysis_type: Optional[str] = "general"


class LocationInsightsRequest(BaseModel):
    location: str
    time_period: str


class ParametricInsuranceRequest(BaseModel):
    location: str
    risk_type: str  # agricultural, urban, infrastructure, etc.
    coverage_value: Optional[float] = None
    time_period: Optional[str] = "12_months"


@router.post("/parametric-insurance")
async def analyze_parametric_insurance_endpoint(request: ParametricInsuranceRequest):
    """
    Analyze parametric insurance viability for specific location and risk type
    """
    if not os.getenv("GROK_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROK_API_KEY not configured in environment variables",
        )

    try:
        # Cria dados climáticos mock para análise paramétrica
        mock_climate_data = {
            "location": request.location,
            "risk_type": request.risk_type,
            "coverage_value": request.coverage_value,
            "time_period": request.time_period,
            "analysis_focus": "parametric_insurance"
        }

        result = grok_service.analyze_climate_data(
            mock_climate_data, "parametric_insurance"
        )

        return {
            "parametric_analysis": result.analysis_text,
            "confidence": result.confidence_level,
            "analysis_type": result.analysis_type,
            "location": request.location,
            "risk_type": request.risk_type,
            "timestamp": result.processing_timestamp.isoformat(),
            "sources": result.sources_considered,
            "regulatory_compliance": "SUSEP Circular 562/2015"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actuarial-calculation")
async def calculate_actuarial_risk_endpoint(request: ParametricInsuranceRequest):
    """
    Perform actuarial calculations for parametric insurance products
    """
    if not os.getenv("GROK_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROK_API_KEY not configured in environment variables",
        )

    try:
        # Dados para cálculo atuarial
        actuarial_data = {
            "location": request.location,
            "risk_type": request.risk_type,
            "coverage_value": request.coverage_value or 1000000,  # Valor padrão
            "calculation_type": "parametric_premium",
            "time_period": request.time_period,
            "technical_rate": 0.055,  # Taxa técnica de 5.5% a.a.
            "discount_rate": 0.045   # Taxa de desconto atuarial
        }

        result = grok_service.analyze_climate_data(
            actuarial_data, "parametric_insurance"
        )

        return {
            "actuarial_calculation": result.analysis_text,
            "confidence": result.confidence_level,
            "location": request.location,
            "risk_type": request.risk_type,
            "coverage_value": actuarial_data["coverage_value"],
            "technical_parameters": {
                "technical_rate": actuarial_data["technical_rate"],
                "discount_rate": actuarial_data["discount_rate"]
            },
            "timestamp": result.processing_timestamp.isoformat(),
            "methodology": "Brazilian actuarial standards with SUSEP compliance"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_climate_data_endpoint(request: ClimateAnalysisRequest):
    """
    Analyze climate data using Grok AI
    """
    if not os.getenv("GROK_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROK_API_KEY not configured in environment variables",
        )

    try:
        result = grok_service.analyze_climate_data(
            request.data, request.analysis_type
        )
        return {
            "analysis": result.analysis_text,
            "confidence": result.confidence_level,
            "analysis_type": result.analysis_type,
            "timestamp": result.processing_timestamp.isoformat(),
            "sources": result.sources_considered,
            "complementary_to": result.complementary_to,
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Grok climate analysis error: {str(e)}\nTraceback: {tb}")


@router.post("/insights")
async def generate_location_insights_endpoint(request: LocationInsightsRequest):
    """
    Generate climate insights for a specific location
    """
    if not os.getenv("GROK_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROK_API_KEY not configured in environment variables",
        )

    try:
        result = grok_service.generate_climate_insights(
            request.location, request.time_period
        )
        return {
            "insights": result.analysis_text,
            "confidence": result.confidence_level,
            "analysis_type": result.analysis_type,
            "timestamp": result.processing_timestamp.isoformat(),
            "sources": result.sources_considered,
            "complementary_to": result.complementary_to,
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Grok insights error: {str(e)}\nTraceback: {tb}")


@router.post("/parametric-insurance")
async def analyze_parametric_insurance_endpoint(request: ParametricInsuranceRequest):
    """
    Analyze parametric insurance viability for specific location and risk type
    """
    if not os.getenv("GROK_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROK_API_KEY not configured in environment variables",
        )

    try:
        # Cria dados climáticos mock para análise paramétrica
        mock_climate_data = {
            "location": request.location,
            "risk_type": request.risk_type,
            "coverage_value": request.coverage_value,
            "time_period": request.time_period,
            "analysis_focus": "parametric_insurance"
        }

        result = grok_service.analyze_climate_data(
            mock_climate_data, "parametric_insurance"
        )

        return {
            "parametric_analysis": result.analysis_text,
            "confidence": result.confidence_level,
            "analysis_type": result.analysis_type,
            "location": request.location,
            "risk_type": request.risk_type,
            "timestamp": result.processing_timestamp.isoformat(),
            "sources": result.sources_considered,
            "regulatory_compliance": "SUSEP Circular 562/2015"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actuarial-calculation")
async def calculate_actuarial_risk_endpoint(request: ParametricInsuranceRequest):
    """
    Perform actuarial calculations for parametric insurance products
    """
    if not os.getenv("GROK_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROK_API_KEY not configured in environment variables",
        )

    try:
        # Dados para cálculo atuarial
        actuarial_data = {
            "location": request.location,
            "risk_type": request.risk_type,
            "coverage_value": request.coverage_value or 1000000,  # Valor padrão
            "calculation_type": "parametric_premium",
            "time_period": request.time_period,
            "technical_rate": 0.055,  # Taxa técnica de 5.5% a.a.
            "discount_rate": 0.045   # Taxa de desconto atuarial
        }

        result = grok_service.analyze_climate_data(
            actuarial_data, "parametric_insurance"
        )

        return {
            "actuarial_calculation": result.analysis_text,
            "confidence": result.confidence_level,
            "location": request.location,
            "risk_type": request.risk_type,
            "coverage_value": actuarial_data["coverage_value"],
            "technical_parameters": {
                "technical_rate": actuarial_data["technical_rate"],
                "discount_rate": actuarial_data["discount_rate"]
            },
            "timestamp": result.processing_timestamp.isoformat(),
            "methodology": "Brazilian actuarial standards with SUSEP compliance"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_grok_status():
    """
    Get Grok integration status and model information
    """
    try:
        model_info = grok_service.get_model_info()
        return {
            "status": "active" if os.getenv("GROK_API_KEY") else "inactive",
            "model_info": model_info,
            "api_configured": bool(os.getenv("GROK_API_KEY")),
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return {
            "status": "error",
            "error": f"{str(e)}\nTraceback: {tb}",
            "api_configured": bool(os.getenv("GROK_API_KEY")),
        }


@router.get("/models")
async def get_available_models():
    """
    Get information about available Grok models
    """
    return {
        "models": [
            {
                "name": "grok-beta",
                "description": "Grok beta model specialized in parametric insurance, actuarial calculations, SUSEP regulations, and Brazilian climate history",
                "capabilities": [
                    "Climate data analysis with Brazilian historical context (1994-2024)",
                    "Parametric insurance product design and viability analysis",
                    "Actuarial calculations using Brazilian technical rates",
                    "SUSEP regulatory compliance assessment",
                    "Risk assessment for agricultural, urban, and infrastructure sectors",
                    "Natural language processing for insurance and climate insights"
                ],
                "specializations": [
                    "Brazilian insurance market (SUSEP regulations)",
                    "Parametric insurance mechanisms",
                    "Actuarial mathematics and risk modeling",
                    "30-year Brazilian climate history analysis",
                    "Regional climate risk assessment by Brazilian states"
                ]
            }
        ],
        "current_model": "grok-beta",
        "training_focus": "Parametric insurance, SUSEP compliance, actuarial calculations, Brazilian climate history"
    }
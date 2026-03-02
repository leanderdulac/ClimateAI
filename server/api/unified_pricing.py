"""
Unified Pricing API Router
Provides endpoints for the unified pricing orchestrator.
"""

from typing import Any, Dict, List, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from services.unified_pricing_orchestrator import (
    UnifiedPricingOrchestrator,
    PricingInput,
    PricingModel,
    unified_pricing_orchestrator,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class UnifiedPricingRequest(BaseModel):
    """Request model for unified pricing calculation"""
    coverage_amount: float = Field(..., description="Coverage amount in BRL")
    location_latitude: float = Field(default=-23.5507, description="Location latitude")
    location_longitude: float = Field(default=-46.6339, description="Location longitude")
    risk_factors: Dict[str, float] = Field(
        default_factory=lambda: {
            "climatic_risk": 0.3,
            "economic_risk": 0.2,
            "location_risk": 0.25,
        },
        description="Risk factors dictionary"
    )
    policy_duration_years: int = Field(default=1, description="Policy duration in years")
    confidence_level: float = Field(default=0.95, description="Confidence level for intervals")
    custom_model_weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Custom weights for models (optional)"
    )
    models_to_use: Optional[List[str]] = Field(
        default=None,
        description="List of models to use (optional, uses all by default)"
    )


class UnifiedPricingResponse(BaseModel):
    """Response model for unified pricing calculation"""
    final_premium: float
    weighted_average_premium: float
    confidence_interval: List[float]
    combined_risk_score: float
    model_agreement_score: float
    recommended_premium: float
    premium_range: List[float]
    calculation_time_ms: float
    explanation: Dict[str, Any]
    warnings: List[str]
    model_results: List[Dict[str, Any]]

    model_config = ConfigDict(protected_namespaces=())


@router.post("/calculate", response_model=UnifiedPricingResponse)
async def calculate_unified_pricing(request: UnifiedPricingRequest) -> UnifiedPricingResponse:
    """
    Calculate unified premium using all available pricing models.
    
    Combines 6 sophisticated pricing models:
    - Comprehensive Pricing (integrated formula)
    - Advanced Actuarial (fractal analysis, Monte Carlo, fuzzy logic)
    - Dynamic Insurance Analysis (ML-based)
    - Ensemble Pricing (BIC-weighted)
    - Climate Premium (climatic inflation factor)
    - Bayesian Bootstrap (uncertainty quantification)
    
    Returns a weighted ensemble of all model outputs with confidence intervals
    and model agreement analysis.
    """
    try:
        # Convert models_to_use strings to enums if provided
        models_enum = None
        if request.models_to_use:
            models_enum = [PricingModel(m) for m in request.models_to_use]
        
        # Build pricing input
        pricing_input = PricingInput(
            coverage_amount=request.coverage_amount,
            location_latitude=request.location_latitude,
            location_longitude=request.location_longitude,
            risk_factors=request.risk_factors,
            policy_duration_years=request.policy_duration_years,
            confidence_level=request.confidence_level,
            custom_model_weights={
                PricingModel(k): v for k, v in request.custom_model_weights.items()
            } if request.custom_model_weights else None,
            models_to_use=models_enum,
        )
        
        # Calculate unified premium
        result = await unified_pricing_orchestrator.calculate_unified_premium_async(pricing_input)
        
        return UnifiedPricingResponse(
            final_premium=result.final_premium,
            weighted_average_premium=result.weighted_average_premium,
            confidence_interval=list(result.confidence_interval),
            combined_risk_score=result.combined_risk_score,
            model_agreement_score=result.model_agreement_score,
            recommended_premium=result.recommended_premium,
            premium_range=list(result.premium_range),
            calculation_time_ms=result.total_calculation_time_ms,
            explanation=result.explanation,
            warnings=result.warnings,
            model_results=[
                {
                    "model_name": r.model_name,
                    "premium": r.premium,
                    "confidence_interval": list(r.confidence_interval),
                    "risk_score": r.risk_score,
                    "weight": r.weight,
                    "calculation_time_ms": r.calculation_time_ms,
                    "error": r.error,
                }
                for r in result.model_results
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unified pricing calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """
    Get information about available pricing models and their default weights.
    """
    return {
        "models": [
            {
                "id": "comprehensive",
                "name": "Comprehensive Pricing",
                "description": "Integrated formula: PTP × (1+ML) × (1+TR) × (1+CC) × Adjustment",
                "default_weight": 0.25,
            },
            {
                "id": "actuarial",
                "name": "Advanced Actuarial",
                "description": "Fractal analysis, Monte Carlo simulation, fuzzy logic",
                "default_weight": 0.20,
            },
            {
                "id": "dynamic",
                "name": "Dynamic Insurance",
                "description": "ML-based dynamic pricing with portfolio optimization",
                "default_weight": 0.20,
            },
            {
                "id": "ensemble",
                "name": "Ensemble Pricing",
                "description": "BIC-weighted ensemble with Dirichlet priors and VaR",
                "default_weight": 0.15,
            },
            {
                "id": "climate",
                "name": "Climate Premium",
                "description": "Climatic inflation factor with drift rate integration",
                "default_weight": 0.10,
            },
            {
                "id": "bayesian",
                "name": "Bayesian Bootstrap",
                "description": "Uncertainty quantification via bootstrap with VaR/CVaR",
                "default_weight": 0.10,
            },
        ],
        "total_default_weight": 1.0,
        "orchestrator_status": unified_pricing_orchestrator.get_model_performance_summary(),
    }


@router.get("/health")
async def check_pricing_health() -> Dict[str, Any]:
    """
    Check health status of the unified pricing system.
    """
    summary = unified_pricing_orchestrator.get_model_performance_summary()
    return {
        "status": "healthy" if summary["services_loaded"] else "degraded",
        "models_available": len(summary["models_available"]),
        "details": summary,
    }

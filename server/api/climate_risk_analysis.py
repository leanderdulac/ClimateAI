"""
Router for Climate Systemic Risk and Climate SCR Services
Implements:
- Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark)
- Margem = SCR_climatico · √(1 + Ψ²) where Ψ = f(prazo_projecao, qualidade_dados)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import numpy as np

from services.climate_systemic_risk_service import (
    climate_systemic_risk_service,
    calculate_extreme_climate_event_probability,
    calculate_conditional_var,
    calculate_climate_loading,
    calculate_systemic_climate_risk
)
from services.climate_scr_service import (
    climate_scr_service,
    ProjectionHorizon,
    calculate_basic_scr,
    calculate_climate_scr_margin,
    calculate_climate_scr_with_uncertainty,
    calculate_scr_with_dynamic_horizon,
    calculate_regulatory_compliant_scr
)

router = APIRouter()

# Climate Systemic Risk Endpoints
@router.post("/climate-systemic-risk/extreme-event-probability")
async def calculate_extreme_climate_event_probability_endpoint(
    climate_data: Dict[str, List[float]],
    event_type: str = Query("compound", description="Type of extreme event: compound, temperature, precipitation, wind, drought")
):
    """
    Calculate probability of extreme climate events
    """
    try:
        result = calculate_extreme_climate_event_probability(climate_data, event_type)
        return {
            "probability": result,
            "climate_data_variables": list(climate_data.keys()),
            "event_type": event_type,
            "n_observations": len(next(iter(climate_data.values()))) if climate_data else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extreme event probability calculation failed: {str(e)}")

@router.post("/climate-systemic-risk/conditional-var")
async def calculate_conditional_var_endpoint(
    portfolio_returns: List[float] = Query(..., description="Portfolio returns time series"),
    event_type: str = Query("compound", description="Type of extreme event: compound, temperature, precipitation, wind, drought"),
    confidence_level: float = Query(0.95, ge=0.5, lt=1.0, description="Confidence level for CoVaR calculation"),
    climate_data: Dict[str, List[float]] = Query(..., description="Climate variables data")
):
    """
    Calculate Conditional Value at Risk (CoVaR) of portfolio conditional on extreme climate event
    """
    try:
        result = calculate_conditional_var(portfolio_returns, climate_data, event_type, confidence_level)
        return {
            "conditional_var": result,
            "portfolio_returns_count": len(portfolio_returns),
            "climate_data_variables": list(climate_data.keys()),
            "event_type": event_type,
            "confidence_level": confidence_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conditional VaR calculation failed: {str(e)}")

@router.post("/climate-systemic-risk/climate-loading")
async def calculate_climate_loading_endpoint(
    portfolio_returns: List[float] = Query(..., description="Portfolio returns time series"),
    event_type: str = Query("compound", description="Type of extreme event: compound, temperature, precipitation, wind, drought"),
    confidence_level: float = Query(0.95, ge=0.5, lt=1.0, description="Confidence level for CoVaR calculation"),
    climate_data: Dict[str, List[float]] = Query(..., description="Climate variables data")
):
    """
    Calculate climate loading: Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark)
    where CoVaR = VaR of portfolio conditional on extreme climate event
    """
    try:
        result = calculate_climate_loading(portfolio_returns, climate_data, confidence_level, event_type)
        return {
            "covar_portfolio": result.covar_portfolio,
            "covar_benchmark": result.covar_benchmark,
            "loading_climate": result.loading_climate,
            "portfolio_vat": result.portfolio_vat,
            "benchmark_vat": result.benchmark_vat,
            "climate_scenario": result.climate_scenario,
            "confidence_level": result.confidence_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Climate loading calculation failed: {str(e)}")

@router.post("/climate-systemic-risk/systemic-risk-analysis")
async def calculate_systemic_climate_risk_endpoint(
    portfolios_data: Dict[str, List[float]],  # {portfolio_name: [returns]}
    climate_data: Dict[str, List[float]],
    confidence_levels: List[float] = Query([0.95, 0.99], description="Confidence levels to analyze"),
    event_types: List[str] = Query(["compound", "temperature", "precipitation"], description="Types of extreme events to analyze")
):
    """
    Calculate systemic climate risk across multiple portfolios
    """
    try:
        result = calculate_systemic_climate_risk(portfolios_data, climate_data, confidence_levels, event_types)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Systemic climate risk calculation failed: {str(e)}")

# Climate SCR Endpoints
@router.post("/climate-scr/basic-scr")
async def calculate_basic_scr_endpoint(
    climate_risk_factors: Dict[str, float],
    portfolio_exposure: float = Query(..., gt=0, description="Portfolio exposure value"),
    confidence_level: float = Query(0.995, ge=0.5, lt=1.0, description="Confidence level for SCR calculation")
):
    """
    Calculate basic climate Solvency Capital Requirement (SCR)
    """
    try:
        result = calculate_basic_scr(climate_risk_factors, portfolio_exposure, confidence_level)
        return {
            "basic_scr": result,
            "portfolio_exposure": portfolio_exposure,
            "climate_risk_factors": climate_risk_factors,
            "confidence_level": confidence_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Basic SCR calculation failed: {str(e)}")

@router.post("/climate-scr/uncertainty-coefficient")
async def calculate_uncertainty_coefficient_endpoint(
    projection_horizon: str = Query(..., description="Time horizon: short_term, medium_term, or long_term"),
    data_quality: str = Query("good", description="Data quality: excellent, good, fair, poor, unknown"),
    additional_uncertainty: float = Query(0.0, ge=0, description="Additional uncertainty from model/data sources")
):
    """
    Determine uncertainty coefficient Ψ = f(prazo_projecao, qualidade_dados)
    """
    try:
        if projection_horizon not in ["short_term", "medium_term", "long_term"]:
            raise HTTPException(status_code=400, detail="Invalid projection horizon. Use: short_term, medium_term, or long_term")
        
        result = calculate_uncertainty_coefficient(projection_horizon, data_quality, additional_uncertainty)
        return {
            "uncertainty_coefficient": result,
            "projection_horizon": projection_horizon,
            "data_quality": data_quality,
            "additional_uncertainty": additional_uncertainty
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uncertainty coefficient calculation failed: {str(e)}")

@router.post("/climate-scr/margin")
async def calculate_climate_scr_margin_endpoint(
    base_scr: float = Query(..., ge=0, description="Basic climate SCR value"),
    uncertainty_coefficient: float = Query(..., ge=0, description="Uncertainty coefficient Ψ")
):
    """
    Calculate climate SCR margin: Margem = SCR_climatico · √(1 + Ψ²)
    """
    try:
        result = calculate_climate_scr_margin(base_scr, uncertainty_coefficient)
        return {
            "margin": result,
            "base_scr": base_scr,
            "uncertainty_coefficient": uncertainty_coefficient,
            "formula": f"{base_scr:.2f} * sqrt(1 + {uncertainty_coefficient}²) = {result:.2f}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SCR margin calculation failed: {str(e)}")

@router.post("/climate-scr/complete-calculation")
async def calculate_climate_scr_with_uncertainty_endpoint(
    climate_risk_factors: Dict[str, float],
    portfolio_exposure: float = Query(..., gt=0, description="Portfolio exposure value"),
    projection_horizon: str = Query(..., description="Time horizon: short_term, medium_term, or long_term"),
    data_quality: str = Query("good", description="Data quality: excellent, good, fair, poor, unknown"),
    confidence_level: float = Query(0.995, ge=0.5, lt=1.0, description="Confidence level for SCR calculation"),
    additional_uncertainty: float = Query(0.0, ge=0, description="Additional uncertainty sources"),
    time_horizon_years: float = Query(5.0, gt=0, description="Time horizon in years")
):
    """
    Complete climate SCR calculation with uncertainty:
    Margem = SCR_climatico · √(1 + Ψ²)
    """
    try:
        result = calculate_climate_scr_with_uncertainty(
            climate_risk_factors, portfolio_exposure, projection_horizon, 
            data_quality, confidence_level, additional_uncertainty, time_horizon_years
        )
        return {
            "base_scr": result.base_scr,
            "uncertainty_coefficient": result.uncertainty_coefficient,
            "final_margin": result.margin,
            "projection_horizon": result.projection_horizon.value,
            "data_quality_score": result.data_quality_score,
            "time_horizon_years": result.time_horizon_years,
            "formula": f"SCR({result.base_scr:.2f}) * sqrt(1 + {result.uncertainty_coefficient:.3f}²) = {result.margin:.2f}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete SCR calculation failed: {str(e)}")

@router.post("/climate-scr/dynamic-horizon")
async def calculate_scr_with_dynamic_horizon_endpoint(
    climate_risk_factors: Dict[str, float],
    portfolio_exposure: float = Query(..., gt=0, description="Portfolio exposure value"),
    time_horizon_years: float = Query(..., gt=0, description="Time horizon in years"),
    data_quality: str = Query("good", description="Data quality: excellent, good, fair, poor, unknown"),
    confidence_level: float = Query(0.995, ge=0.5, lt=1.0, description="Confidence level for SCR calculation")
):
    """
    Climate SCR calculation with dynamic time horizon adjustment
    """
    try:
        result = calculate_scr_with_dynamic_horizon(
            climate_risk_factors, portfolio_exposure, time_horizon_years,
            data_quality, confidence_level
        )
        return {
            "base_scr": result.base_scr,
            "uncertainty_coefficient": result.uncertainty_coefficient,
            "final_margin": result.margin,
            "projection_horizon": result.projection_horizon.value,
            "data_quality_score": result.data_quality_score,
            "time_horizon_years": result.time_horizon_years,
            "formula": f"SCR({result.base_scr:.2f}) * sqrt(1 + {result.uncertainty_coefficient:.3f}²) = {result.margin:.2f}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dynamic horizon SCR calculation failed: {str(e)}")

@router.post("/climate-scr/regulatory-compliant")
async def calculate_regulatory_compliant_scr_endpoint(
    climate_risk_factors: Dict[str, float],
    portfolio_exposure: float = Query(..., gt=0, description="Portfolio exposure value"),
    time_horizon_years: float = Query(..., gt=0, description="Time horizon in years"),
    data_quality: str = Query("good", description="Data quality: excellent, good, fair, poor, unknown"),
    confidence_level: float = Query(0.995, ge=0.5, lt=1.0, description="Confidence level for SCR calculation"),
    stress_scenarios: Optional[List[Dict[str, float]]] = None
):
    """
    Regulatory-compliant climate SCR calculation following insurance regulation standards
    """
    try:
        result = calculate_regulatory_compliant_scr(
            climate_risk_factors, portfolio_exposure, time_horizon_years,
            data_quality, confidence_level, stress_scenarios
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regulatory compliant SCR calculation failed: {str(e)}")

@router.get("/climate-risk-analysis/status")
async def climate_risk_analysis_status():
    """
    Get the status of the climate risk analysis services
    """
    return {
        "services_available": True,
        "systemic_risk_service": True,
        "scr_service": True,
        "supported_horizons": ["short_term", "medium_term", "long_term"],
        "data_quality_levels": ["excellent", "good", "fair", "poor", "unknown"],
        "timestamp": datetime.now().isoformat()
    }
"""
Router for Climate Systemic Risk and Climate SCR Services
Implements:
- Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark)
- Margem = SCR_climatico · √(1 + Ψ²) where Ψ = f(prazo_projecao, qualidade_dados)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from services.climate_scr_service import (
    calculate_individual_scr,
    calculate_peril_specific_scr,
    calculate_portfolio_scr,
    calculate_simple_portfolio_scr,
    climate_scr_service,
    create_correlation_matrix,
)
from services.climate_systemic_risk_service import (
    calculate_climate_loading,
    calculate_conditional_var,
    calculate_extreme_climate_event_probability,
    calculate_systemic_climate_risk,
    climate_systemic_risk_service,
)

router = APIRouter()


# Climate Systemic Risk Endpoints
@router.post("/climate-systemic-risk/extreme-event-probability")
async def calculate_extreme_climate_event_probability_endpoint(
    climate_data: Dict[str, List[float]],
    event_type: str = Query(
        "compound",
        description="Type of extreme event: compound, temperature, precipitation, wind, drought",
    ),
):
    """
    Calculate probability of extreme climate events
    """
    try:
        result = (
            climate_systemic_risk_service.calculate_extreme_climate_event_probability(
                climate_data, event_type
            )
        )
        return {
            "probability": result,
            "climate_data_variables": list(climate_data.keys()),
            "event_type": event_type,
            "n_observations": (
                len(next(iter(climate_data.values()))) if climate_data else 0
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extreme event probability calculation failed: {str(e)}",
        )


@router.post("/climate-systemic-risk/conditional-var")
async def calculate_conditional_var_endpoint(
    portfolio_returns: List[float],
    climate_data: Dict[str, List[float]],
    event_type: str = Query(
        "compound",
        description="Type of extreme event: compound, temperature, precipitation, wind, drought",
    ),
    confidence_level: float = Query(
        0.95, ge=0.5, lt=1.0, description="Confidence level for CoVaR calculation"
    ),
):
    """
    Calculate Conditional Value at Risk (CoVaR) of portfolio conditional on extreme climate event
    """
    try:
        result = climate_systemic_risk_service.calculate_conditional_var(
            portfolio_returns, climate_data, event_type, confidence_level
        )
        return {
            "conditional_var": result,
            "portfolio_returns_count": len(portfolio_returns),
            "climate_data_variables": list(climate_data.keys()),
            "event_type": event_type,
            "confidence_level": confidence_level,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Conditional VaR calculation failed: {str(e)}"
        )


@router.post("/climate-systemic-risk/climate-loading")
async def calculate_climate_loading_endpoint(
    portfolio_returns: List[float],
    climate_data: Dict[str, List[float]],
    event_type: str = Query(
        "compound",
        description="Type of extreme event: compound, temperature, precipitation, wind, drought",
    ),
    confidence_level: float = Query(
        0.95, ge=0.5, lt=1.0, description="Confidence level for CoVaR calculation"
    ),
):
    """
    Calculate climate loading: Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark)
    where CoVaR = VaR of portfolio conditional on extreme climate event
    """
    try:
        result = climate_systemic_risk_service.calculate_climate_loading(
            portfolio_returns, climate_data, confidence_level, event_type
        )
        return {
            "covar_portfolio": result.covar_portfolio,
            "covar_benchmark": result.covar_benchmark,
            "loading_climate": result.loading_climate,
            "portfolio_vat": result.portfolio_vat,
            "benchmark_vat": result.benchmark_vat,
            "climate_scenario": result.climate_scenario,
            "confidence_level": result.confidence_level,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Climate loading calculation failed: {str(e)}"
        )


@router.post("/climate-systemic-risk/systemic-risk-analysis")
async def calculate_systemic_climate_risk_endpoint(
    portfolios_data: Dict[str, List[float]],  # {portfolio_name: [returns]}
    climate_data: Dict[str, List[float]],
    confidence_levels: List[float] = Query(
        [0.95, 0.99], description="Confidence levels to analyze"
    ),
    event_types: List[str] = Query(
        ["compound", "temperature", "precipitation"],
        description="Types of extreme events to analyze",
    ),
):
    """
    Calculate systemic climate risk across multiple portfolios
    """
    try:
        result = climate_systemic_risk_service.calculate_systemic_climate_risk(
            portfolios_data, climate_data, confidence_levels, event_types
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Systemic climate risk calculation failed: {str(e)}",
        )


# Climate SCR Endpoints
@router.post("/climate-scr/basic-scr")
async def calculate_basic_scr_endpoint(
    var_995_losses: List[float],
    expected_losses: List[float],
    correlation_matrix: Optional[List[List[float]]] = None,
):
    """
    Calculate basic climate Solvency Capital Requirement (SCR)
    """
    try:
        result = climate_scr_service.calculate_portfolio_scr(
            var_995_losses, expected_losses, correlation_matrix
        )
        return {
            "total_scr": result.total_scr,
            "individual_scrs": result.individual_scrs,
            "correlation_matrix": result.correlation_matrix,
            "expected_losses": result.expected_losses,
            "var_995_losses": result.var_995_losses,
            "calculation_timestamp": result.calculation_timestamp,
            "portfolio_size": result.portfolio_size,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Basic SCR calculation failed: {str(e)}"
        )


@router.post("/climate-scr/simple-portfolio-scr")
async def calculate_simple_portfolio_scr_endpoint(
    var_995_losses: List[float], expected_losses: List[float]
):
    """
    Calculate portfolio SCR with default 0.25 correlation between different perils
    """
    try:
        result = climate_scr_service.calculate_simple_portfolio_scr(
            var_995_losses, expected_losses
        )
        return {
            "total_scr": result.total_scr,
            "individual_scrs": result.individual_scrs,
            "correlation_matrix": result.correlation_matrix,
            "expected_losses": result.expected_losses,
            "var_995_losses": result.var_995_losses,
            "calculation_timestamp": result.calculation_timestamp,
            "portfolio_size": result.portfolio_size,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Simple portfolio SCR calculation failed: {str(e)}"
        )


@router.post("/climate-scr/peril-specific-scr")
async def calculate_peril_specific_scr_endpoint(
    peril_losses: Dict[str, Dict[str, float]],
):
    """
    Calculate SCR from peril-specific data with default correlations
    """
    try:
        result = climate_scr_service.calculate_peril_specific_scr(peril_losses)
        return {
            "total_scr": result.total_scr,
            "individual_scrs": result.individual_scrs,
            "correlation_matrix": result.correlation_matrix,
            "expected_losses": result.expected_losses,
            "var_995_losses": result.var_995_losses,
            "calculation_timestamp": result.calculation_timestamp,
            "portfolio_size": result.portfolio_size,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Peril-specific SCR calculation failed: {str(e)}"
        )


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
        "timestamp": datetime.now().isoformat(),
    }

"""
API Router for Loading Margin Calculation Service
Implements: ML = ROE_target × Capital_alocado / Volume_prêmios
Where: Capital_alocado = Exp_o × SCR × fator_ponderador_RBC
And fator_ponderador_RBC determined by SCR ranges
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.loading_margin_service import (
    LoadingMarginCalculator,
    PolicyLoadingInfo,
    PortfolioLoadingAnalysis,
    calculate_loading_margin,
    calculate_policy_loading_info,
    calculate_portfolio_loading_analysis,
    calculate_risk_based_pricing_adjustment,
    get_capital_efficiency_metrics,
)

router = APIRouter()


@router.post("/loading-margin/calculate")
async def calculate_loading_margin_endpoint(
    exposure_value: float = Query(..., ge=0, description="Exposure value (Exp_o)"),
    scr_score: float = Query(..., ge=0, description="SCR score for the risk"),
    premium_volume: float = Query(
        ..., gt=0, description="Premium volume to calculate margin against"
    ),
    roe_target: float = Query(0.18, ge=0, le=1, description="ROE target (default 18%)"),
):
    """
    Calculate Loading Margin using the formula:
    ML = ROE_target × Capital_alocado / Volume_prêmios
    Where: Capital_alocado = Exp_o × SCR × fator_ponderador_RBC
    """
    try:
        # Calculate loading margin
        result = calculate_loading_margin(exposure_value, scr_score, premium_volume)

        # Calculate RBC weight factor for the given SCR score
        rbc_weight_factor = 1.0
        if 300 <= scr_score < 600:
            rbc_weight_factor = 1.5
        elif 600 <= scr_score < 800:
            rbc_weight_factor = 2.5
        elif scr_score >= 800:
            rbc_weight_factor = 4.0

        # Calculate allocated capital using the formula
        allocated_capital = exposure_value * scr_score * rbc_weight_factor

        # Calculate loading margin manually as verification
        expected_loading_margin = roe_target * allocated_capital / premium_volume

        return {
            "loading_margin": result.loading_margin,
            "roe_target": result.roe_target,
            "allocated_capital": result.allocated_capital,
            "premium_volume": result.premium_volume,
            "scr_score": result.scr_score,
            "rbc_weight_factor": result.rbc_weight_factor,
            "exposure_value": result.exposure_value,
            "calculation_method": result.calculation_method,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "formula_verification": {
                "expected_loading_margin": expected_loading_margin,
                "calculated_loading_margin": result.loading_margin,
                "match": abs(expected_loading_margin - result.loading_margin) < 0.001,
            },
            "financial_metrics": {
                "capital_intensity": allocated_capital / premium_volume,
                "loading_percentage": result.loading_margin * 100,
                "capital_efficiency_score": (
                    1.0 / (1.0 + (allocated_capital / premium_volume))
                    if premium_volume > 0
                    else 0.0
                ),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Loading margin calculation failed: {str(e)}"
        )


@router.post("/loading-margin/policy-analysis")
async def policy_loading_analysis_endpoint(
    exposure_value: float = Query(..., ge=0, description="Policy exposure value"),
    scr_score: float = Query(..., ge=0, description="Policy SCR score"),
    premium_amount: float = Query(..., gt=0, description="Policy premium amount"),
):
    """
    Calculate loading margin for an individual policy
    """
    try:
        result = calculate_policy_loading_margin(
            exposure_value, scr_score, premium_amount
        )

        return {
            "policy_id": result.policy_id,
            "exposure_value": result.exposure_value,
            "final_scr_score": result.final_scr_score,
            "rbc_weight_factor": result.rbc_weight_factor,
            "allocated_capital": result.allocated_capital,
            "premium_amount": result.premium_amount,
            "calculated_loading_margin": result.calculated_loading_margin,
            "risk_category": result.risk_category,
            "calculation_timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Policy loading calculation failed: {str(e)}"
        )


@router.post("/loading-margin/portfolio-analysis")
async def portfolio_loading_analysis_endpoint(
    exposure_values: List[float] = Query(..., description="List of exposure values"),
    scr_scores: List[float] = Query(..., description="List of SCR scores"),
    premium_amounts: List[float] = Query(..., description="List of premium amounts"),
    portfolio_premium_volume: float = Query(
        ..., gt=0, description="Total portfolio premium volume"
    ),
):
    """
    Calculate loading margin analysis for a portfolio of policies
    """
    try:
        # Validate input lengths
        if not all(
            len(lst) == len(exposure_values) for lst in [scr_scores, premium_amounts]
        ):
            raise HTTPException(
                status_code=400, detail="All lists must have the same length"
            )

        if len(exposure_values) == 0:
            raise HTTPException(
                status_code=400, detail="At least one policy is required"
            )

        # Create policy data structures
        policies = []
        for i in range(len(exposure_values)):
            policy_data = {
                "exposure_value": exposure_values[i],
                "scr_score": scr_scores[i],
                "premium_amount": premium_amounts[i],
            }
            policies.append(policy_data)

        # Calculate portfolio loading analysis
        result = calculate_portfolio_loading_analysis(
            policies, portfolio_premium_volume
        )

        return {
            "portfolio_loading_margin": result.portfolio_loading_margin,
            "portfolio_roe_target": result.portfolio_roe_target,
            "total_allocated_capital": result.total_allocated_capital,
            "total_premium_volume": result.total_premium_volume,
            "average_scr_score": result.average_scr_score,
            "risk_distribution": result.risk_distribution,
            "portfolio_size": result.portfolio_size,
            "capital_efficiency_ratio": result.capital_efficiency_ratio,
            "loading_margin_breakdown": result.loading_margin_breakdown,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "portfolio_metrics": {
                "capital_intensity_ratio": (
                    result.total_allocated_capital / result.total_premium_volume
                    if result.total_premium_volume > 0
                    else 0
                ),
                "risk_concentration_index": (
                    sum(count**2 for count in result.risk_distribution.values())
                    / (result.portfolio_size**2)
                    if result.portfolio_size > 0
                    else 0
                ),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Portfolio loading analysis failed: {str(e)}"
        )


@router.post("/loading-margin/risk-adjusted-pricing")
async def risk_adjusted_pricing_endpoint(
    base_premium: float = Query(
        ..., gt=0, description="Base premium before risk adjustment"
    ),
    scr_score: float = Query(..., ge=0, description="SCR score for the policy/risk"),
    exposure_value: float = Query(..., ge=0, description="Exposure value of the risk"),
    roe_target: float = Query(
        0.18, ge=0, le=1, description="ROE target for capital allocation"
    ),
):
    """
    Calculate risk-based pricing adjustment based on capital requirements
    """
    try:
        adjustment = calculate_risk_based_pricing_adjustment(
            base_premium, scr_score, exposure_value
        )

        return adjustment
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Risk-adjusted pricing calculation failed: {str(e)}",
        )


@router.post("/loading-margin/capital-efficiency")
async def capital_efficiency_metrics_endpoint(
    exposure_values: List[float] = Query(..., description="List of exposure values"),
    scr_scores: List[float] = Query(..., description="List of SCR scores"),
    premium_amounts: List[float] = Query(..., description="List of premium amounts"),
    total_portfolio_premium: float = Query(
        ..., gt=0, description="Total portfolio premium"
    ),
):
    """
    Get comprehensive capital efficiency metrics for the portfolio
    """
    try:
        # Validate input lengths
        n_policies = len(exposure_values)
        if not all(len(lst) == n_policies for lst in [scr_scores, premium_amounts]):
            raise HTTPException(
                status_code=400, detail="All input lists must have the same length"
            )

        if n_policies == 0:
            raise HTTPException(
                status_code=400, detail="At least one policy is required"
            )

        # Create policies list
        policies = []
        for i in range(n_policies):
            policy_data = {
                "exposure_value": exposure_values[i],
                "scr_score": scr_scores[i],
                "premium_amount": premium_amounts[i],
            }
            policies.append(policy_data)

        # Calculate capital efficiency metrics
        metrics = get_capital_efficiency_metrics(policies, total_portfolio_premium)

        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Capital efficiency metrics calculation failed: {str(e)}",
        )


@router.get("/loading-margin/info")
async def loading_margin_info():
    """
    Get information about the loading margin calculation service
    """
    return {
        "description": "Loading Margin Calculation Service",
        "formula": "ML = ROE_target × Capital_alocado / Volume_prêmios",
        "components": {
            "capital_alocado": "Exp_o × SCR × fator_ponderador_RBC",
            "fator_ponderador_RBC": {
                "SCR < 300": "1.0",
                "300 ≤ SCR < 600": "1.5",
                "600 ≤ SCR < 800": "2.5",
                "SCR ≥ 800": "4.0",
            },
            "roe_target": "18% a.a. (conservative assumption for climate risk)",
        },
        "methodology": "Risk-Based Capital (RBC) Framework for Climate Insurance",
        "regulatory_alignment": "Consistent with Basel III and Solvency II capital adequacy frameworks",
        "features": [
            "Dynamic loading margin calculation based on risk profile",
            "Risk-based capital allocation with tiered penalties",
            "Portfolio-level aggregation of capital requirements",
            "Capital efficiency metrics and recommendations",
            "Risk-adjusted pricing with appropriate margins",
        ],
        "risk_categories": {
            "low": {"scr_range": "< 300", "rbc_factor": 1.0},
            "moderate": {"scr_range": "300-599", "rbc_factor": 1.5},
            "high": {"scr_range": "600-799", "rbc_factor": 2.5},
            "critical": {"scr_range": "≥ 800", "rbc_factor": 4.0},
        },
        "capital_efficiency_indicators": [
            "Capital intensity ratio (capital allocated / premium volume)",
            "Risk-adjusted return metrics",
            "Portfolio diversification metrics",
            "Allocation efficiency scoring",
        ],
        "practical_applications": [
            "Setting appropriate loading margins for insurance policies",
            "Capital allocation optimization",
            "Risk-based pricing adjustments",
            "Portfolio efficiency assessment",
            "Regulatory compliance with capital adequacy requirements",
        ],
        "integration": "Connects with physical, transition, concentration, and mitigation services for comprehensive risk assessment",
    }

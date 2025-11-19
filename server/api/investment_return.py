"""
API Router for Investment Return Calculation Service
Implements: TR = E[Retorno_investimento] × f_tempo_apólice
Where: E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]
With adjustment: TR_ajustado = TR × (1 - 0.3·SCR/1000)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.investment_return_service import (
    InvestmentPortfolioAnalysis,
    InvestmentReturnCalculator,
    InvestmentReturnResult,
    PolicyInvestmentProfile,
    calculate_expected_return_rate,
    calculate_investment_return,
    calculate_portfolio_investment_analysis,
    calculate_return_sensitivity,
    optimize_portfolio_allocation,
)

router = APIRouter()


@router.post("/investment-return/calculate")
async def calculate_investment_return_endpoint(
    policy_id: str = Query(..., description="Unique policy identifier"),
    scr_score: float = Query(..., ge=0, description="SCR score for the policy"),
    policy_term_months: int = Query(
        12, ge=1, le=240, description="Policy term in months (max 240 = 20 years)"
    ),
    initial_investment: float = Query(
        100000.0, gt=0, description="Initial investment amount"
    ),
    climate_resilience_score: float = Query(
        0.7, ge=0, le=1, description="Climate resilience score (0-1, default 0.7)"
    ),
):
    """
    Calculate investment return using the specified formula:
    TR = E[Retorno_investimento] × f_tempo_apólice
    Where: E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]
    With adjustment: TR_ajustado = TR × (1 - 0.3·SCR/1000) [reduces exposure to risky assets as SCR rises]
    """
    try:
        # Create PolicyInvestmentProfile object
        policy_profile = PolicyInvestmentProfile(
            policy_id=policy_id,
            premium_issued=initial_investment,  # Assuming initial_investment is premium_issued for this context
            policy_term_months=policy_term_months,
            initial_investment=initial_investment,
            scr_score=scr_score,
            climate_resilience_score=climate_resilience_score,
        )

        # Calculate investment return
        result = calculate_investment_return(policy_profile)

        return {
            "total_return": result.total_return,
            "adjusted_return": result.adjusted_return,
            "expected_return_rate": result.expected_return_rate,
            "time_factor": result.time_factor,
            "portfolio_composition": result.portfolio_composition,
            "risk_adjustment_factor": result.risk_adjustment_factor,
            "scr_score": result.scr_score,
            "climate_resilience_factor": result.climate_resilience_factor,
            "calculation_method": result.calculation_method,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "input_parameters": {
                "policy_id": policy_id,
                "scr_score": scr_score,
                "policy_term_months": policy_term_months,
                "initial_investment": initial_investment,
                "climate_resilience_score": climate_resilience_score,
            },
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Investment return calculation failed: {str(e)}"
        )


@router.post("/investment-return/portfolio-analysis")
async def portfolio_investment_analysis_endpoint(
    policy_profiles: List[PolicyInvestmentProfile],
):
    """
    Calculate investment return analysis for a portfolio of policies
    """
    try:
        result = calculate_portfolio_investment_analysis(policy_profiles)

        return {
            "total_premium_issued": result.total_premium_issued,
            "total_expected_returns": result.total_expected_returns,
            "total_adjusted_returns": result.total_adjusted_returns,
            "average_return_ratio": result.average_return_ratio,
            "portfolio_size": result.portfolio_size,
            "risk_adjusted_return_ratio": result.risk_adjusted_return_ratio,
            "portfolio_risk_metrics": result.portfolio_risk_metrics,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Portfolio investment analysis failed: {str(e)}"
        )


@router.post("/investment-return/optimize-allocation")
async def optimize_investment_allocation_endpoint(
    scr_score: float = Query(
        ..., ge=0, description="SCR score to base optimization on"
    ),
    climate_resilience_target: float = Query(
        0.7, ge=0, le=1, description="Target climate resilience (0-1)"
    ),
):
    """
    Optimize investment allocation based on risk level and climate resilience
    """
    try:
        result = optimize_portfolio_allocation(
            scr_score=scr_score, climate_resilience_target=climate_resilience_target
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Investment allocation optimization failed: {str(e)}",
        )


@router.get("/investment-return/expected-return")
async def calculate_expected_return_endpoint():
    """
    Calculate expected return for the default portfolio composition:
    E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]
    """
    try:
        expected_return = calculate_expected_return_rate()

        return {
            "expected_return_rate": expected_return,
            "formula": "E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]",
            "calculation_timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Expected return calculation failed: {str(e)}"
        )


@router.get("/investment-return/info")
async def investment_return_info():
    """
    Get information about the investment return calculation service
    """
    return {
        "description": "Investment Return Calculation Service",
        "main_formula": "TR = E[Retorno_investimento] × f_tempo_apólice",
        "expected_return_formula": "E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]",
        "risk_adjustment_formula": "TR_ajustado = TR × (1 - 0.3·SCR/1000)",
        "parameters": {
            "w_rf": {
                "value": 0.60,
                "meaning": "60% weight for risk-free assets for climate insurance security",
            },
            "w_eq": {"value": 0.25, "meaning": "25% weight for equity assets"},
            "w_infra": {
                "value": 0.15,
                "meaning": "15% weight for infrastructure assets",
            },
            "r_f": {
                "value": 0.03,
                "meaning": "3% real return for risk-free assets (Selic - inflation)",
            },
            "E[r_eq]": {"value": 0.08, "meaning": "8% real return for equity assets"},
            "E[r_infra]": {
                "value": 0.06,
                "meaning": "6% real return for infrastructure assets",
            },
            "risk_adjustment_coefficient": {
                "value": 0.3,
                "meaning": "Coefficient reducing exposure to risky assets as SCR rises",
            },
            "scr_normalization_factor": {
                "value": 1000.0,
                "meaning": "Normalization factor for SCR in adjustment calculation",
            },
        },
        "methodology": "Climate-Adjusted Investment Return Framework for Insurance Portfolios",
        "features": [
            "Risk-adjusted investment return calculations",
            "SCR-based portfolio adjustment mechanisms",
            "Climate resilience optimization",
            "Portfolio-level strategy analysis",
            "Allocation optimization for climate risk",
            "Time factor incorporation",
        ],
        "default_portfolio_allocation": "60% risk-free + 25% equity + 15% infrastructure",
        "default_expected_return": "4.8% annually [(0.60 × 3%) + (0.25 × 8%) + (0.15 × 6%)]",
        "risk_adjustment_logic": "As SCR score increases, risky asset exposure decreases to maintain portfolio stability",
        "integration": "Connects with other climate risk assessment services",
    }

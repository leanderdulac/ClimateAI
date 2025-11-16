"""
API Router for Investment Return Calculation Service
Implements: TR = E[Retorno_investimento] × f_tempo_apólice
Where: E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]
With adjustment: TR_ajustado = TR × (1 - 0.3·SCR/1000)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.investment_return_service import (
    InvestmentReturnCalculator,
    InvestmentPortfolioComposition,
    InvestmentReturnResult,
    PolicyInvestmentStrategy,
    calculate_investment_return,
    calculate_portfolio_investment_strategy,
    optimize_investment_allocation,
    calculate_expected_return
)

router = APIRouter()

@router.post("/investment-return/calculate")
async def calculate_investment_return_endpoint(
    policy_id: str = Query(..., description="Unique policy identifier"),
    scr_score: float = Query(..., ge=0, description="SCR score for the policy"),
    policy_term_months: int = Query(12, ge=1, le=240, description="Policy term in months (max 240 = 20 years)"),
    initial_investment: float = Query(100000.0, gt=0, description="Initial investment amount"),
    rf_weight: float = Query(0.60, ge=0, le=1, description="Weight of risk-free assets (w_rf, default 0.60)"),
    eq_weight: float = Query(0.25, ge=0, le=1, description="Weight of equity assets (w_eq, default 0.25)"),
    infra_weight: float = Query(0.15, ge=0, le=1, description="Weight of infrastructure assets (w_infra, default 0.15)"),
    rf_return: float = Query(0.03, ge=0, le=1, description="Risk-free return rate (r_f, default 0.03 = 3%)"),
    eq_return: float = Query(0.08, ge=0, le=1, description="Equity return rate (E[r_eq], default 0.08 = 8%)"),
    infra_return: float = Query(0.06, ge=0, le=1, description="Infrastructure return rate (E[r_infra], default 0.06 = 6%)"),
    climate_resilience_score: float = Query(0.7, ge=0, le=1, description="Climate resilience score (0-1, default 0.7)")
):
    """
    Calculate investment return using the specified formula:
    TR = E[Retorno_investimento] × f_tempo_apólice
    Where: E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]
    With adjustment: TR_ajustado = TR × (1 - 0.3·SCR/1000) [reduces exposure to risky assets as SCR rises]
    """
    try:
        # Validate that weights sum to approximately 1.0
        weight_sum = rf_weight + eq_weight + infra_weight
        if not 0.99 <= weight_sum <= 1.01:
            raise HTTPException(
                status_code=400,
                detail=f"Portfolio weights must sum to 1.0, got {weight_sum:.2f}. Please adjust your weights."
            )
        
        # Validate return rates are non-negative
        if any(rate < 0 for rate in [rf_return, eq_return, infra_return]):
            raise HTTPException(
                status_code=400,
                detail="Return rates must be non-negative"
            )
        
        # Calculate investment return with all parameters
        result = calculate_investment_return(
            policy_id=policy_id,
            scr_score=scr_score,
            policy_term_months=policy_term_months,
            initial_investment=initial_investment,
            rf_weight=rf_weight,
            eq_weight=eq_weight,
            infra_weight=infra_weight,
            rf_return=rf_return,
            eq_return=eq_return,
            infra_return=infra_return,
            climate_resilience_score=climate_resilience_score
        )
        
        # Calculate the components of the formula separately for transparency
        expected_return_formula = (
            rf_weight * rf_return + 
            eq_weight * eq_return + 
            infra_weight * infra_return
        )
        
        # Time factor (simplified)
        time_years = policy_term_months / 12.0
        time_factor = 1.0 + (time_years * 0.02)  # Additional 2% per year
        
        # Risk adjustment: (1 - 0.3·SCR/1000)
        risk_adjustment = 1.0 - (0.3 * scr_score / 1000.0)
        
        return {
            "total_return": result.total_return,
            "adjusted_return": result.adjusted_return,
            "expected_return": result.expected_return,
            "time_factor": result.time_factor,
            "portfolio_composition": result.portfolio_composition,
            "risk_adjustment_factor": result.risk_adjustment_factor,
            "scr_impact": result.scr_impact,
            "calculation_method": result.calculation_method,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "input_parameters": {
                "policy_id": policy_id,
                "scr_score": scr_score,
                "policy_term_months": policy_term_months,
                "initial_investment": initial_investment,
                "rf_weight": rf_weight,
                "eq_weight": eq_weight,
                "infra_weight": infra_weight,
                "rf_return": rf_return,
                "eq_return": eq_return,
                "infra_return": infra_return,
                "climate_resilience_score": climate_resilience_score
            },
            "formula_breakdown": {
                "expected_return_component": f"w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra] = ({rf_weight}×{rf_return}) + ({eq_weight}×{eq_return}) + ({infra_weight}×{infra_return}) = {expected_return_formula:.6f}",
                "time_factor": time_factor,
                "risk_adjustment": f"(1 - 0.3·SCR/1000) = (1 - 0.3×{scr_score}/1000) = {risk_adjustment:.6f}",
                "initial_calculation": f"TR = E[Retorno] × f_tempo_apólice = {expected_return_formula:.6f} × {initial_investment} × {time_factor:.6f}",
                "adjusted_calculation": f"TR_ajustado = TR × (1 - 0.3·SCR/1000) = (result before adjustment) × {risk_adjustment:.6f}"
            }
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investment return calculation failed: {str(e)}")

@router.post("/investment-return/portfolio-strategy")
async def portfolio_investment_strategy_endpoint(
    policy_ids: List[str] = Query(..., description="List of policy IDs"),
    scr_scores: List[float] = Query(..., description="List of SCR scores for each policy"),
    policy_terms_months: List[int] = Query(..., description="List of policy terms in months"),
    investment_amounts: List[float] = Query(..., description="List of investment amounts"),
    climate_resilience_scores: List[float] = Query(None, description="Climate resilience scores (0-1)")
):
    """
    Calculate investment strategy for a portfolio of policies
    """
    try:
        n_policies = len(policy_ids)
        if not all(len(lst) == n_policies for lst in [scr_scores, policy_terms_months, investment_amounts]):
            raise HTTPException(
                status_code=400,
                detail="All input lists must have the same length"
            )
        
        if n_policies == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one policy is required"
            )
        
        # Set default climate resilience scores if not provided
        if climate_resilience_scores is None:
            climate_resilience_scores = [0.7] * n_policies
        
        if len(climate_resilience_scores) != n_policies:
            raise HTTPException(
                status_code=400,
                detail="Climate resilience scores list must match policy count"
            )
        
        # Create portfolio data
        portfolio_policies = []
        for i in range(n_policies):
            policy_data = {
                'policy_id': policy_ids[i],
                'scr_score': scr_scores[i],
                'policy_term_months': policy_terms_months[i],
                'investment_amount': investment_amounts[i],
                'climate_resilience_score': climate_resilience_scores[i],
                'rf_weight': 0.60,  # Default weights
                'eq_weight': 0.25,
                'infra_weight': 0.15,
                'rf_return': 0.03,
                'eq_return': 0.08,
                'infra_return': 0.06
            }
            portfolio_policies.append(policy_data)
        
        # Calculate portfolio strategy
        result = calculate_portfolio_investment_strategy(portfolio_policies)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio investment strategy calculation failed: {str(e)}")

@router.post("/investment-return/optimize-allocation")
async def optimize_investment_allocation_endpoint(
    scr_score: float = Query(..., ge=0, description="SCR score to base optimization on"),
    policy_term_months: int = Query(12, ge=1, le=240, description="Policy term in months"),
    climate_resilience_target: float = Query(0.7, ge=0, le=1, description="Target climate resilience (0-1)"),
    target_return_rate: float = Query(0.05, ge=0, le=1, description="Target return rate (default 0.05 = 5%)")
):
    """
    Optimize investment allocation based on risk level and climate resilience
    """
    try:
        result = optimize_investment_allocation(
            scr_score=scr_score,
            policy_term_months=policy_term_months,
            climate_resilience_target=climate_resilience_target,
            target_return_rate=target_return_rate
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investment allocation optimization failed: {str(e)}")

@router.get("/investment-return/expected-return")
async def calculate_expected_return_endpoint(
    rf_weight: float = Query(0.60, ge=0, le=1, description="Weight of risk-free assets"),
    eq_weight: float = Query(0.25, ge=0, le=1, description="Weight of equity assets"),
    infra_weight: float = Query(0.15, ge=0, le=1, description="Weight of infrastructure assets"),
    rf_return: float = Query(0.03, ge=0, le=1, description="Risk-free return rate (3%)"),
    eq_return: float = Query(0.08, ge=0, le=1, description="Equity return rate (8%)"),
    infra_return: float = Query(0.06, ge=0, le=1, description="Infrastructure return rate (6%)")
):
    """
    Calculate expected return for any portfolio composition:
    E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]
    """
    try:
        # Validate weights sum to 1.0
        total_weight = rf_weight + eq_weight + infra_weight
        if not 0.99 <= total_weight <= 1.01:
            raise HTTPException(
                status_code=400,
                detail=f"Weights must sum to 1.0, got {total_weight:.2f}"
            )
        
        expected_return = calculate_expected_return(
            rf_weight=rf_weight,
            eq_weight=eq_weight,
            infra_weight=infra_weight,
            rf_return=rf_return,
            eq_return=eq_return,
            infra_return=infra_return
        )
        
        return {
            "expected_return_rate": expected_return,
            "formula": f"E[Retorno] = ({rf_weight} × {rf_return}) + ({eq_weight} × {eq_return}) + ({infra_weight} × {infra_return})",
            "calculation": f"({rf_weight} × {rf_return:.3f}) + ({eq_weight} × {eq_return:.3f}) + ({infra_weight} × {infra_return:.3f}) = {expected_return:.6f}",
            "portfolio_composition": {
                "risk_free_weight": rf_weight,
                "equity_weight": eq_weight,
                "infrastructure_weight": infra_weight
            },
            "portfolio_returns": {
                "risk_free_return": rf_return,
                "equity_return": eq_return,
                "infrastructure_return": infra_return
            },
            "calculation_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Expected return calculation failed: {str(e)}")

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
            "w_rf": {"value": 0.60, "meaning": "60% weight for risk-free assets for climate insurance security"},
            "w_eq": {"value": 0.25, "meaning": "25% weight for equity assets"},
            "w_infra": {"value": 0.15, "meaning": "15% weight for infrastructure assets"},
            "r_f": {"value": 0.03, "meaning": "3% real return for risk-free assets (Selic - inflation)"},
            "E[r_eq]": {"value": 0.08, "meaning": "8% real return for equity assets"},
            "E[r_infra]": {"value": 0.06, "meaning": "6% real return for infrastructure assets"},
            "risk_adjustment_coefficient": {"value": 0.3, "meaning": "Coefficient reducing exposure to risky assets as SCR rises"},
            "scr_normalization_factor": {"value": 1000.0, "meaning": "Normalization factor for SCR in adjustment calculation"}
        },
        "methodology": "Climate-Adjusted Investment Return Framework for Insurance Portfolios",
        "features": [
            "Risk-adjusted investment return calculations",
            "SCR-based portfolio adjustment mechanisms",
            "Climate resilience optimization",
            "Portfolio-level strategy analysis",
            "Allocation optimization for climate risk",
            "Time factor incorporation"
        ],
        "default_portfolio_allocation": "60% risk-free + 25% equity + 15% infrastructure",
        "default_expected_return": "4.8% annually [(0.60 × 3%) + (0.25 × 8%) + (0.15 × 6%)]",
        "risk_adjustment_logic": "As SCR score increases, risky asset exposure decreases to maintain portfolio stability",
        "integration": "Connects with other climate risk assessment services"
    }
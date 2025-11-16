"""
API Router for Capital Surplus Calculation Service
Implements: CS = z_α × √Var(Loss) / E[Loss]
Where:
- Var(Loss) = E[Loss²] - E[Loss]² + σ²_climático
- σ²_climático = (SCR/1000)² × λ_clim × (1 - λ_clim) [binomial climate variance]
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.capital_surplus_service import (
    calculate_capital_surplus_from_risks,
    calculate_portfolio_capital_surplus,
    optimize_capital_efficiency,
    get_capital_surplus_factors
)

router = APIRouter()

@router.post("/capital-surplus/calculate")
async def calculate_capital_surplus_endpoint(
    physical_risk: float = Query(..., ge=0, description="Physical risk (R_físico)"),
    transition_risk: float = Query(..., ge=0, description="Transition risk (R_transição)"),
    concentration_risk: float = Query(..., ge=0, description="Concentration risk (R_concentração)"),
    scr_score: float = Query(..., ge=0, description="SCR score for climate variance calculation"),
    mitigation_effect: float = Query(0.0, ge=0, le=1, description="Mitigation effectiveness (0-1)"),
    climate_lambda: float = Query(0.1, ge=0, le=1, description="Climate loss probability λ_clim (0-1)"),
    confidence_level: float = Query(0.95, ge=0.5, le=0.99, description="Confidence level (0.5-0.99)")
):
    """
    Calculate Capital Surplus using the formula:
    CS = z_α × √Var(Loss) / E[Loss]
    Where Var(Loss) = E[Loss²] - E[Loss]² + σ²_climático
    And σ²_climático = (SCR/1000)² × λ_clim × (1 - λ_clim)
    """
    try:
        result = calculate_capital_surplus_from_risks(
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=concentration_risk,
            scr_score=scr_score,
            mitigation_effect=mitigation_effect,
            climate_lambda=climate_lambda,
            confidence_level=confidence_level
        )
        
        return {
            "capital_surplus": result.capital_surplus,
            "quantile_factor": result.quantile_factor,
            "variance_loss": result.variance_loss,
            "expected_loss": result.expected_loss,
            "climate_variance": result.climate_variance,
            "climate_lambda": result.climate_lambda,
            "confidence_level": result.confidence_level,
            "scr_normalized": result.scr_normalized,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "input_parameters": {
                "physical_risk": physical_risk,
                "transition_risk": transition_risk,
                "concentration_risk": concentration_risk,
                "scr_score": scr_score,
                "mitigation_effect": mitigation_effect,
                "climate_lambda": climate_lambda,
                "confidence_level": confidence_level
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capital surplus calculation failed: {str(e)}")

@router.post("/capital-surplus/portfolio-analysis")
async def portfolio_capital_surplus_endpoint(
    physical_risks: List[float] = Query(..., description="List of physical risks for each policy"),
    transition_risks: List[float] = Query(..., description="List of transition risks for each policy"),
    concentration_risks: List[float] = Query(..., description="List of concentration risks for each policy"),
    scr_scores: List[float] = Query(..., description="List of SCR scores for each policy"),
    mitigation_effects: List[float] = Query(..., description="List of mitigation effects (0-1) for each policy"),
    portfolio_weights: Optional[List[float]] = Query(None, description="Weights for each policy in portfolio"),
    climate_lambda: float = Query(0.1, ge=0, le=1, description="Climate loss probability λ_clim (0-1)"),
    confidence_level: float = Query(0.95, ge=0.5, le=0.99, description="Confidence level (0.5-0.99)")
):
    """
    Calculate Capital Surplus for a portfolio of policies
    """
    try:
        # Validate input lengths
        n_policies = len(physical_risks)
        if not all(len(lst) == n_policies for lst in [transition_risks, concentration_risks, scr_scores, mitigation_effects]):
            raise HTTPException(
                status_code=400,
                detail="All risk lists must have the same length"
            )
        
        if portfolio_weights and len(portfolio_weights) != n_policies:
            raise HTTPException(
                status_code=400,
                detail="Portfolio weights must match the number of policies"
            )
        
        # Create portfolio risks list
        portfolio_risks = []
        for i in range(n_policies):
            portfolio_risks.append({
                'physical': physical_risks[i],
                'transition': transition_risks[i],
                'concentration': concentration_risks[i]
            })
        
        result = calculate_portfolio_capital_surplus(
            portfolio_risks=portfolio_risks,
            portfolio_scr_scores=scr_scores,
            portfolio_mitigation_effects=mitigation_effects,
            portfolio_weights=portfolio_weights,
            climate_lambda=climate_lambda,
            confidence_level=confidence_level
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio capital surplus calculation failed: {str(e)}")

@router.post("/capital-surplus/optimize-mitigation")
async def optimize_mitigation_endpoint(
    target_capital_surplus: float = Query(..., ge=0, description="Target capital surplus value"),
    physical_risk: float = Query(..., ge=0, description="Physical risk (R_físico)"),
    transition_risk: float = Query(..., ge=0, description="Transition risk (R_transição)"),
    concentration_risk: float = Query(..., ge=0, description="Concentration risk (R_concentração)"),
    scr_score: float = Query(..., ge=0, description="SCR score"),
    climate_lambda: float = Query(0.1, ge=0, le=1, description="Climate loss probability λ_clim (0-1)"),
    confidence_level: float = Query(0.95, ge=0.5, le=0.99, description="Confidence level (0.5-0.99)")
):
    """
    Optimize mitigation measures to achieve target capital surplus
    """
    try:
        result = optimize_capital_efficiency(
            target_capital_surplus=target_capital_surplus,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=concentration_risk,
            scr_score=scr_score,
            climate_lambda=climate_lambda,
            confidence_level=confidence_level
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mitigation optimization failed: {str(e)}")

@router.get("/capital-surplus/factors-breakdown")
async def capital_surplus_factors_endpoint(
    physical_risk: float = Query(..., ge=0, description="Physical risk value"),
    transition_risk: float = Query(..., ge=0, description="Transition risk value"),
    concentration_risk: float = Query(..., ge=0, description="Concentration risk value"),
    scr_score: float = Query(..., ge=0, description="SCR score"),
    mitigation_effect: float = Query(0.0, ge=0, le=1, description="Mitigation effectiveness (0-1)")
):
    """
    Get detailed breakdown of factors influencing capital surplus calculation
    """
    try:
        # Create risk profile for analysis
        risk_profile = {
            'physical': physical_risk,
            'transition': transition_risk,
            'concentration': concentration_risk,
            'mitigation_effect': mitigation_effect
        }
        
        factors = get_capital_surplus_factors(risk_profile)
        
        return {
            'risk_profile': risk_profile,
            'factors_breakdown': factors,
            'analysis_timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Factors analysis failed: {str(e)}")

@router.get("/capital-surplus/info")
async def capital_surplus_info():
    """
    Get information about the capital surplus calculation service
    """
    return {
        "description": "Capital Surplus Calculation Service",
        "formula": "CS = z_α × √Var(Loss) / E[Loss]",
        "components": {
            "Var(Loss)": "E[Loss²] - E[Loss]² + σ²_climático",
            "σ²_climático": "(SCR/1000)² × λ_clim × (1 - λ_clim) [binomial climate variance]",
            "z_α": "Normal quantile (e.g., 1.645 for α=95%)"
        },
        "methodology": "Climate Risk Capital Adequacy Framework",
        "features": [
            "Individual policy capital surplus calculation",
            "Portfolio-level capital surplus analysis",
            "Mitigation optimization for target surplus",
            "Factor breakdown analysis",
            "Climate risk integration with binomial variance"
        ],
        "default_parameters": {
            "climate_lambda": 0.1,  # 10% climate event probability
            "confidence_level": 0.95  # 95% confidence
        },
        "applications": [
            "Insurance capital adequacy assessment",
            "Risk-based capital allocation",
            "Mitigation investment prioritization",
            "Portfolio optimization for insurers",
            "Climate risk stress testing"
        ]
    }
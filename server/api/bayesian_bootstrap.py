"""
Router for Bayesian Bootstrap Premium Calculation Service
Implements uncertainty quantification via Bayesian bootstrap:
- Parameter sampling from posterior
- Monte Carlo simulation of 10,000 scenarios
- VaR and CVaR calculation by contract
- Premium percentiles: Prêmio = R$ 1.200 ± [R$ 900 (P10) - R$ 2.100 (P90)]
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
import pandas as pd

from services.bayesian_bootstrap_service import (
    bayesian_bootstrap_service,
    sample_posterior_parameters,
    monte_carlo_simulation,
    calculate_percentiles,
    calculate_value_at_risk,
    calculate_conditional_value_at_risk,
    bayesian_bootstrap_premium,
    calculate_contract_uncertainty_ranges
)

router = APIRouter()

@router.post("/bayesian-bootstrap/sample-posterior-parameters")
async def sample_posterior_parameters_endpoint(
    data: List[float] = Query(..., description="Historical data for the contract"),
    prior_alpha: float = Query(2.0, description="Alpha parameter for Beta prior"),
    prior_beta: float = Query(2.0, description="Beta parameter for Beta prior")
):
    """
    Sample parameters from posterior distribution using conjugate priors
    """
    try:
        result = sample_posterior_parameters(data, prior_alpha, prior_beta)
        return {
            "posterior_samples": result,
            "data_points": len(data),
            "prior_alpha": prior_alpha,
            "prior_beta": prior_beta
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Posterior parameter sampling failed: {str(e)}")

@router.post("/bayesian-bootstrap/monte-carlo-simulation")
async def monte_carlo_simulation_endpoint(
    n_scenarios: int = Query(10000, ge=100, description="Number of Monte Carlo scenarios"),
    mean_rate: float = Query(..., description="Mean rate parameter"),
    variance: float = Query(..., ge=0, description="Variance parameter"),
    shape: float = Query(..., ge=0, description="Shape parameter"),
    scale: float = Query(..., ge=0, description="Scale parameter"),
    base_premium: float = Query(..., gt=0, description="Base premium"),
    contract_exposure: float = Query(..., gt=0, description="Contract exposure amount")
):
    """
    Run Monte Carlo simulation for premium estimation
    """
    try:
        param_samples = {
            'mean_rate': mean_rate,
            'variance': variance,
            'shape': shape,
            'scale': scale
        }
        
        results = monte_carlo_simulation(n_scenarios, param_samples, base_premium, contract_exposure)
        
        return {
            "scenario_results": results[:100],  # Return first 100 results to avoid huge responses
            "n_scenarios_run": n_scenarios,
            "mean_result": np.mean(results),
            "std_result": np.std(results),
            "min_result": min(results),
            "max_result": max(results),
            "parameter_samples": param_samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monte Carlo simulation failed: {str(e)}")

@router.post("/bayesian-bootstrap/calculate-percentiles")
async def calculate_percentiles_endpoint(
    scenario_results: List[float] = Query(..., description="Monte Carlo scenario results"),
    percentiles: List[int] = Query([10, 50, 90], description="Percentiles to calculate")
):
    """
    Calculate percentiles from Monte Carlo results
    """
    try:
        results = calculate_percentiles(scenario_results, percentiles)
        
        return {
            "percentile_results": results,
            "n_scenarios": len(scenario_results),
            "requested_percentiles": percentiles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Percentile calculation failed: {str(e)}")

@router.post("/bayesian-bootstrap/value-at-risk")
async def calculate_value_at_risk_endpoint(
    scenario_results: List[float] = Query(..., description="Monte Carlo scenario results"),
    confidence_level: float = Query(0.95, ge=0.5, lt=1.0, description="Confidence level for VaR")
):
    """
    Calculate Value at Risk (VaR) for the contract
    """
    try:
        var_value = calculate_value_at_risk(scenario_results, confidence_level)
        
        return {
            "value_at_risk": var_value,
            "confidence_level": confidence_level,
            "n_scenarios": len(scenario_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Value at Risk calculation failed: {str(e)}")

@router.post("/bayesian-bootstrap/conditional-value-at-risk")
async def calculate_conditional_value_at_risk_endpoint(
    scenario_results: List[float] = Query(..., description="Monte Carlo scenario results"),
    confidence_level: float = Query(0.95, ge=0.5, lt=1.0, description="Confidence level for CVaR")
):
    """
    Calculate Conditional Value at Risk (CVaR) for the contract
    """
    try:
        cvar_value = calculate_conditional_value_at_risk(scenario_results, confidence_level)
        
        return {
            "conditional_value_at_risk": cvar_value,
            "confidence_level": confidence_level,
            "n_scenarios": len(scenario_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conditional Value at Risk calculation failed: {str(e)}")

@router.post("/bayesian-bootstrap/premium-calculation")
async def bayesian_bootstrap_premium_endpoint(
    contract_data: List[float] = Query(..., description="Historical data for the contract"),
    base_premium: float = Query(..., gt=0, description="Base premium estimate"),
    contract_exposure: float = Query(..., gt=0, description="Contract exposure amount"),
    n_scenarios: int = Query(10000, ge=100, description="Number of Monte Carlo scenarios"),
    confidence_level: float = Query(0.95, ge=0.5, lt=1.0, description="Confidence level for VaR/CVaR"),
    contract_id: str = Query("default_contract", description="Contract identifier"),
    prior_alpha: float = Query(2.0, description="Alpha parameter for Beta prior"),
    prior_beta: float = Query(2.0, description="Beta parameter for Beta prior")
):
    """
    Complete Bayesian bootstrap premium calculation:
    Prêmio = R$ 1.200 ± [R$ 900 (P10) - R$ 2.100 (P90)]
    - Parameter sampling from posterior
    - Monte Carlo simulation of N scenarios
    - VaR and CVaR calculation
    - Percentile calculation
    """
    try:
        result = bayesian_bootstrap_premium(
            contract_data, base_premium, contract_exposure, n_scenarios,
            confidence_level, contract_id
        )
        
        # Prepare the result dictionary
        result_dict = {
            "mean_premium": result.mean_premium,
            "p10": result.p10,
            "p90": result.p90,
            "lower_bound": result.lower_bound,
            "upper_bound": result.upper_bound,
            "n_scenarios_used": result.n_scenarios,
            "var": result.vaar,
            "cvar": result.cvar,
            "contract_id": result.contract_id,
            "confidence_level_used": confidence_level,
            "data_points_used": len(contract_data),
            "premium_uncertainty_range": f"{result.mean_premium:.2f} ± [{result.p10:.2f} (P10), {result.p90:.2f} (P90)]",
            "statistics": {
                "std_premium": np.std(result.scenario_results),
                "median_premium": np.median(result.scenario_results),
                "skewness": float(pd.Series(result.scenario_results).skew()) if pd else 0.0
            }
        }
        
        return result_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bayesian bootstrap premium calculation failed: {str(e)}")

@router.post("/bayesian-bootstrap/contract-uncertainty-ranges")
async def calculate_contract_uncertainty_ranges_endpoint(
    contracts_data: Dict[str, Dict[str, Any]]
):
    """
    Calculate uncertainty ranges for multiple contracts
    """
    try:
        results = calculate_contract_uncertainty_ranges(contracts_data)
        
        # Format results
        formatted_results = {}
        for contract_id, result in results.items():
            formatted_results[contract_id] = {
                "mean_premium": result.mean_premium,
                "p10": result.p10,
                "p90": result.p90,
                "lower_bound": result.lower_bound,
                "upper_bound": result.upper_bound,
                "n_scenarios_used": result.n_scenarios,
                "var": result.vaar,
                "cvar": result.cvar,
                "premium_uncertainty_range": f"{result.mean_premium:.2f} ± [{result.p10:.2f} (P10), {result.p90:.2f} (P90)]"
            }
        
        return {
            "contract_results": formatted_results,
            "n_contracts_processed": len(formatted_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract uncertainty ranges calculation failed: {str(e)}")

@router.get("/bayesian-bootstrap/status")
async def bayesian_bootstrap_status():
    """
    Get the status of the Bayesian bootstrap service
    """
    return {
        "service_available": True,
        "monte_carlo_scenarios_default": 10000,
        "supported_percentiles": [10, 50, 90],
        "confidence_level_range": [0.5, 0.99],
        "formula_implemented": "Prêmio = R$ 1.200 ± [R$ 900 (P10) - R$ 2.100 (P90)]",
        "methodology": {
            "parameter_sampling": "Posterior parameter sampling using conjugate priors",
            "simulation": "Monte Carlo simulation of 10,000 scenarios",
            "risk_measures": ["Value at Risk (VaR)", "Conditional Value at Risk (CVaR)"],
            "uncertainty_quantification": "Bayesian bootstrap with percentile calculation"
        },
        "timestamp": datetime.now().isoformat()
    }
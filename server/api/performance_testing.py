"""
Router for ClimateAI Performance Testing Service
Implements:
- Climate backtesting against historical events
- Stress testing with 200% CMIP6 + Black Swan scenarios
- Robustness analysis with 20% parameter perturbation → ΔPrêmio < 10%
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np

from services.performance_testing_service import (
    climate_performance_testing_service,
    climate_backtesting_test,
    stress_testing_analysis,
    robustness_analysis_test,
    comprehensive_performance_evaluation
)

router = APIRouter()

@router.post("/performance-testing/climate-backtesting")
async def climate_backtesting_endpoint(
    model_predictions: List[float] = Query(..., description="Model predictions for historical periods"),
    actual_losses: List[float] = Query(..., description="Actual losses from historical events"),
    event_dates: List[str] = Query(..., description="Dates of historical events (YYYY-MM-DD)"),
    event_types: List[str] = Query(..., description="Types of historical events"),
    model_name: str = Query("climate_model", description="Name of the model being tested")
):
    """
    Climate backtesting against historical events:
    - Hurricane Ian (2022)
    - RS Floods (2024) 
    - Other extreme climate events
    """
    try:
        if len(model_predictions) != len(actual_losses) or len(model_predictions) != len(event_dates) or len(model_predictions) != len(event_types):
            raise HTTPException(
                status_code=400,
                detail="Predictions, actual losses, event dates, and event types must have the same length"
            )
        
        result = climate_backtesting_test(
            model_predictions, actual_losses, event_dates, event_types, model_name
        )
        
        return {
            "test_name": result.test_name,
            "test_date": result.test_date,
            "success": result.success,
            "metrics": result.metrics,
            "parameters": result.parameters,
            "results": result.results,
            "error_message": result.error_message,
            "methodology": "Climate backtesting against historical extreme events"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Climate backtesting failed: {str(e)}")

@router.post("/performance-testing/stress-testing")
async def stress_testing_endpoint(
    base_scenario_losses: List[float] = Query(..., description="Base scenario losses"),
    stress_multiplier: float = Query(2.0, ge=1.0, description="Stress multiplier (default 2.0 for 200%)"),
    black_swan_probability: float = Query(0.1, ge=0.0, le=1.0, description="Black swan event probability"),
    black_swan_impact_factor: float = Query(3.0, ge=1.0, description="Black swan impact multiplier")
):
    """
    Stress testing: 200% of worst CMIP6 scenario + Black Swan climate event
    """
    try:
        result = stress_testing_analysis(
            base_scenario_losses, stress_multiplier, black_swan_probability, black_swan_impact_factor
        )
        
        return {
            "test_name": result.test_name,
            "test_date": result.test_date,
            "success": result.success,
            "metrics": result.metrics,
            "parameters": result.parameters,
            "results": result.results,
            "error_message": result.error_message,
            "methodology": f"{stress_multiplier*100:.0f}% of worst CMIP6 scenario + Black Swan event (P={black_swan_probability}, impact×{black_swan_impact_factor})"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress testing failed: {str(e)}")

@router.post("/performance-testing/robustness-analysis")
async def robustness_analysis_endpoint(
    base_params: Dict[str, float] = Query(..., description="Base model parameters"),
    parameter_perturbation: float = Query(0.20, ge=0.01, le=0.5, description="Parameter perturbation (default 0.20 = 20%)"),
    n_perturbations: int = Query(100, ge=10, le=1000, description="Number of perturbation trials"),
    base_output: Optional[float] = Query(None, description="Base output value for comparison"),
    base_input_data: Optional[List[float]] = Query(None, description="Input data for the model")
):
    """
    Robustness analysis: 20% parameter perturbation → ΔPrêmio < 10%
    """
    try:
        # Note: In a real implementation, we would need the actual model object
        # For now, we'll use a placeholder approach
        result = robustness_analysis_test(
            base_model=None,  # Would be actual model in production
            base_params=base_params,
            parameter_perturbation=parameter_perturbation,
            n_perturbations=n_perturbations,
            base_input_data=base_input_data,
            base_output=base_output
        )
        
        return {
            "test_name": result.test_name,
            "test_date": result.test_date,
            "success": result.success,
            "metrics": result.metrics,
            "parameters": result.parameters,
            "results": result.results,
            "error_message": result.error_message,
            "methodology": f"{parameter_perturbation*100:.0f}% parameter perturbation → ΔPrêmio < 10%",
            "perturbation_target": 0.10  # 10% premium change threshold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Robustness analysis failed: {str(e)}")

@router.post("/performance-testing/comprehensive-evaluation")
async def comprehensive_performance_evaluation_endpoint(
    model_predictions: List[float] = Query(..., description="Model predictions"),
    actual_losses: List[float] = Query(..., description="Actual losses from historical events"),
    event_dates: List[str] = Query(..., description="Dates of historical events"),
    event_types: List[str] = Query(..., description="Types of historical events"),
    base_scenario_losses: List[float] = Query(..., description="Base losses for stress testing"),
    model_parameters: Dict[str, float] = Query(..., description="Model parameters for robustness testing"),
    stress_multiplier: float = Query(2.0, description="Stress multiplier for CMIP6 scenarios"),
    parameter_perturbation: float = Query(0.20, description="Parameter perturbation for robustness"),
    black_swan_probability: float = Query(0.1, description="Black swan probability for stress test"),
    black_swan_impact_factor: float = Query(3.0, description="Black swan impact factor")
):
    """
    Comprehensive performance evaluation combining:
    - Climate backtesting against historical events
    - Stress testing with extreme scenarios
    - Robustness analysis with parameter perturbations
    """
    try:
        if len(model_predictions) != len(actual_losses) or len(model_predictions) != len(event_dates) or len(model_predictions) != len(event_types):
            raise HTTPException(
                status_code=400,
                detail="Model predictions, actual losses, event dates, and event types must have the same length"
            )
        
        result = comprehensive_performance_evaluation(
            model_predictions, actual_losses, event_dates, event_types,
            base_scenario_losses, model_parameters,
            stress_multiplier=stress_multiplier,
            robustness_perturbation=parameter_perturbation
        )
        
        return {
            "comprehensive_evaluation": result,
            "methodologies_applied": [
                "Climate backtesting against historical events",
                f"Stress testing: {stress_multiplier*100:.0f}% CMIP6 + Black Swan (P={black_swan_probability}, impact×{black_swan_impact_factor})",
                f"Robustness: {parameter_perturbation*100:.0f}% parameter perturbation → ΔPrêmio < 10%"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive performance evaluation failed: {str(e)}")

@router.get("/performance-testing/status")
async def performance_testing_status():
    """
    Get status of the performance testing service
    """
    return {
        "service_available": True,
        "implemented_tests": [
            "Climate backtesting against historical events",
            "Stress testing (200% CMIP6 + Black Swan)",
            "Robustness analysis (20% parameter perturbation)",
            "Comprehensive performance evaluation"
        ],
        "validation_events": [
            "Hurricane Ian (2022)",
            "RS Floods (2024)",
            "Additional extreme climate events"
        ],
        "stress_test_parameters": {
            "cmip6_multiplier": 2.0,
            "black_swan_probability_range": [0.01, 0.20],
            "black_swan_impact_range": [2.0, 5.0]
        },
        "robustness_parameters": {
            "parameter_perturbation": 0.20,
            "premium_change_threshold": 0.10,
            "minimum_trials": 50
        },
        "formula_implemented": [
            "Climate Backtesting: Validation against historical events",
            "Stress Test: 200% CMIP6 scenarios + Black Swan events",
            "Robustness: 20% parameter perturbation → ΔPrêmio < 10%"
        ],
        "timestamp": datetime.now().isoformat()
    }
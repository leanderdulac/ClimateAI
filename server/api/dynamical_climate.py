"""
API Router for Dynamical Systems Climate Forecasting
Implements advanced climate modeling using dynamical systems theory with pynamicalsys.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.dynamical_climate_service import (
    calculate_climate_predictability_horizon,
    detect_climate_regime_shifts,
    ensemble_climate_prediction,
    fit_climate_phase_space,
    predict_climate_dynamics,
)

router = APIRouter()


@router.post("/dynamical-prediction")
async def dynamical_climate_prediction(
    initial_conditions: List[float] = Query(
        ..., description="Initial conditions for dynamical system"
    ),
    n_steps: int = Query(30, ge=1, le=365, description="Number of prediction steps"),
    model_type: str = Query("lorenz", description="Type of dynamical model"),
    parameters: Optional[Dict[str, float]] = None,
):
    """
    Generate climate predictions using dynamical systems models.

    This endpoint uses chaotic attractors like the Lorenz system to model
    the complex, non-linear dynamics of climate systems, providing improved
    forecasts with uncertainty quantification.
    """
    try:
        result = predict_climate_dynamics(
            initial_conditions=initial_conditions,
            n_steps=n_steps,
            model_type=model_type,
            parameters=parameters,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error in dynamical prediction: {str(e)}"
        )


@router.post("/ensemble-dynamical-prediction")
async def ensemble_dynamical_climate_prediction(
    n_models: int = Query(5, ge=1, le=20, description="Number of ensemble members"),
    n_steps: int = Query(30, ge=1, le=365, description="Number of prediction steps"),
    model_type: str = Query("lorenz", description="Base model type for ensemble"),
):
    """
    Generate ensemble climate predictions using multiple dynamical systems models
    to capture uncertainty in climate predictions.
    """
    try:
        result = ensemble_climate_prediction(
            n_models=n_models, n_steps=n_steps, model_type=model_type
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error in ensemble prediction: {str(e)}"
        )


@router.post("/phase-space-reconstruction")
async def phase_space_reconstruction(
    climate_data: List[Dict[str, float]],
    target_var: str = Query(
        "temperature", description="Target variable for reconstruction"
    ),
):
    """
    Reconstruct phase space from climate time series data for dynamical analysis.

    This helps understand the underlying attractor structure of climate dynamics
    and can reveal patterns not visible in raw time series.
    """
    try:
        result = fit_climate_phase_space(
            climate_data=climate_data, target_var=target_var
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error in phase space reconstruction: {str(e)}"
        )


@router.post("/regime-shift-detection")
async def detect_climate_regime_shifts_endpoint(climate_time_series: List[float]):
    """
    Detect climate regime shifts using dynamical systems properties.

    This identifies significant changes in the statistical properties of
    climate time series that may indicate system transitions.
    """
    try:
        result = detect_climate_regime_shifts(climate_time_series=climate_time_series)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error in regime shift detection: {str(e)}"
        )


@router.post("/predictability-horizon")
async def climate_predictability_horizon(
    lyapunov_exponent: float = Query(..., description="Largest Lyapunov exponent"),
    initial_uncertainty: float = Query(
        0.01, description="Initial uncertainty in observations"
    ),
):
    """
    Calculate the predictability horizon based on the largest Lyapunov exponent.

    This gives an estimate of how far into the future climate can be predicted
    based on the chaotic properties of the climate system.
    """
    try:
        result = calculate_climate_predictability_horizon(
            lyapunov_exponent=lyapunov_exponent, initial_uncertainty=initial_uncertainty
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error calculating predictability horizon: {str(e)}",
        )


@router.get("/dynamical-forecasting-info")
async def dynamical_forecasting_info():
    """
    Get information about the dynamical systems climate forecasting capabilities.
    """
    return {
        "description": "Dynamical Systems Climate Forecasting API",
        "methods": [
            "dynamical_climate_prediction: Use chaotic attractors for climate prediction",
            "ensemble_dynamical_prediction: Ensemble forecasting with multiple models",
            "phase_space_reconstruction: Reconstruct climate attractor from data",
            "regime_shift_detection: Detect shifts in climate regimes",
            "predictability_horizon: Calculate forecast limits based on chaos theory",
        ],
        "models_supported": ["lorenz", "rossler", "duffing", "henon", "logistic"],
        "features": [
            "Chaotic attractor modeling for atmospheric dynamics",
            "Phase space reconstruction for climate data",
            "Lyapunov exponent analysis for chaos quantification",
            "Basin stability metrics for climate state persistence",
            "Ensemble forecasting with uncertainty quantification",
            "Predictability horizon estimation based on chaos theory",
        ],
    }

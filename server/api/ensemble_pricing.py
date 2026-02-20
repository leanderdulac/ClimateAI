"""
Router for Ensemble Pricing Service with Dynamic Model Weights
Implements: Prêmio_final = Σ_m w_m · Prêmio_m + z_α · VaR_ensemble
Where w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m and π_m ~ Dirichlet(α)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from services.ensemble_pricing_service import (
    calculate_bic,
    calculate_dynamic_weights,
    calculate_ensemble_pricing,
    ensemble_pricing_service,
    update_model_performance,
)

router = APIRouter()


@router.post("/ensemble-pricing/bic")
async def calculate_bic_endpoint(
    log_likelihood: float = Query(..., description="Log-likelihood of the model"),
    n_params: int = Query(..., ge=1, description="Number of model parameters"),
    n_observations: int = Query(..., ge=1, description="Number of observations"),
):
    """
    Calculate Bayesian Information Criterion (BIC)
    BIC = -2 * log_likelihood + n_params * ln(n_observations)
    """
    try:
        bic_value = calculate_bic(log_likelihood, n_params, n_observations)
        return {
            "bic": bic_value,
            "log_likelihood": log_likelihood,
            "n_params": n_params,
            "n_observations": n_observations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BIC calculation failed: {str(e)}")


@router.post("/ensemble-pricing/dynamic-weights")
async def calculate_dynamic_weights_endpoint(
    bics: List[float] = Query(..., description="BIC values for each model"),
    n_models: int = Query(..., ge=2, description="Number of models in ensemble"),
    prior_alpha: Optional[List[float]] = Query(
        None, description="Dirichlet prior parameters α"
    ),
):
    """
    Calculate dynamic model weights based on BIC and Dirichlet prior:
    w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m where π_m ~ Dirichlet(α)
    """
    try:
        if len(bics) != n_models:
            raise HTTPException(
                status_code=400, detail="BICs count must match n_models"
            )

        if prior_alpha and len(prior_alpha) != n_models:
            raise HTTPException(
                status_code=400, detail="Prior alpha length must match n_models"
            )

        weights = calculate_dynamic_weights(bics, n_models, prior_alpha)

        return {
            "weights": weights,
            "bics": bics,
            "n_models": n_models,
            "prior_alpha": prior_alpha or [1.0] * n_models,
            "bic_sensitivity": ensemble_pricing_service.bic_sensitivity,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Dynamic weights calculation failed: {str(e)}"
        )


@router.post("/ensemble-pricing/calculate")
async def calculate_ensemble_pricing_endpoint(
    model_premiums: List[float] = Query(
        ..., description="Premiums from each individual model"
    ),
    model_log_likelihoods: List[float] = Query(
        ..., description="Log-likelihood for each model"
    ),
    model_n_params: List[int] = Query(
        ..., description="Number of parameters for each model"
    ),
    model_n_observations: List[int] = Query(
        ..., description="Number of observations for each model"
    ),
    confidence_level: float = Query(
        0.95, ge=0.5, lt=1.0, description="Confidence level for VaR calculation"
    ),
    dirichlet_alpha: Optional[List[float]] = Query(
        None, description="Dirichlet prior parameters α"
    ),
    bic_sensitivity: float = Query(1.0, description="BIC sensitivity parameter η"),
    uncertainty_factor: float = Query(1.0, description="Uncertainty scaling factor"),
):
    """
    Complete ensemble pricing calculation:
    Prêmio_final = Σ_m w_m · Prêmio_m + z_α · VaR_ensemble
    Where w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m and π_m ~ Dirichlet(α)
    """
    try:
        n_models = len(model_premiums)

        if not all(
            len(lst) == n_models
            for lst in [model_log_likelihoods, model_n_params, model_n_observations]
        ):
            raise HTTPException(
                status_code=400,
                detail="All model parameter lists must have the same length",
            )

        if dirichlet_alpha and len(dirichlet_alpha) != n_models:
            raise HTTPException(
                status_code=400,
                detail="Dirichlet alpha length must match number of models",
            )

        if any(n <= 0 for n in model_n_params + model_n_observations):
            raise HTTPException(
                status_code=400,
                detail="Number of parameters and observations must be positive",
            )

        result = await calculate_ensemble_pricing(
            model_premiums,
            model_log_likelihoods,
            model_n_params,
            model_n_observations,
            n_models,
            confidence_level,
            dirichlet_alpha,
            bic_sensitivity,
            uncertainty_factor,
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ensemble pricing calculation failed: {str(e)}"
        )


@router.post("/ensemble-pricing/update-model-performance")
async def update_model_performance_endpoint(
    model_id: str,
    log_likelihood: float,
    n_params: int = Query(..., ge=1),
    n_observations: int = Query(..., ge=1),
):
    """
    Update model performance history with new BIC calculation
    """
    try:
        update_model_performance(model_id, log_likelihood, n_params, n_observations)

        return {
            "message": f"Model {model_id} performance updated successfully",
            "model_id": model_id,
            "log_likelihood": log_likelihood,
            "n_params": n_params,
            "n_observations": n_observations,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Model performance update failed: {str(e)}"
        )


@router.get("/ensemble-pricing/model-performance/{model_id}")
async def get_historical_model_performance_endpoint(model_id: str):
    """
    Get historical performance for a specific model
    """
    try:
        history = ensemble_pricing_service.get_historical_model_performance(model_id)

        return {
            "model_id": model_id,
            "performance_history": history,
            "n_recordings": len(history),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Get model performance failed: {str(e)}"
        )


@router.get("/ensemble-pricing/status")
async def ensemble_pricing_status():
    """
    Get the status of the ensemble pricing service
    """
    return {
        "service_available": True,
        "n_models_tracked": len(ensemble_pricing_service.model_performance_history),
        "bic_sensitivity": ensemble_pricing_service.bic_sensitivity,
        "uncertainty_factor": ensemble_pricing_service.uncertainty_factor,
        "timestamp": datetime.now().isoformat(),
    }

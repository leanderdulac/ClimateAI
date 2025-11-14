"""
Router for advanced climate risk modeling with regularized loss functions
Implements L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f) where Ω(f) = γT + ½λ||w||²
and includes advanced climate features like SPI, RWI, synoptic patterns, and temperature gradients
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from services.climate_risk_modeling_service import (
    climate_risk_modeling_service,
    calculate_standardized_precipitation_index,
    calculate_relative_wetness_index,
    extract_synoptic_circulation_patterns,
    calculate_vertical_temperature_gradient,
    regularized_loss_function,
    comprehensive_climate_risk_assessment
)

router = APIRouter()

@router.post("/climate-risk-modeling/standardized-precipitation-index")
async def calculate_spi_endpoint(
    precipitation_data: List[float],
    window_months: int = Query(3, ge=1, le=24, description="Time window in months (3, 6, 12)")
):
    """
    Calculate Standardized Precipitation Index (SPI) for different time windows
    """
    try:
        result = calculate_standardized_precipitation_index(precipitation_data, window_months)
        return {
            "spi_values": result,
            "window_months": window_months,
            "n_values": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SPI calculation failed: {str(e)}")

@router.post("/climate-risk-modeling/relative-wetness-index")
async def calculate_rwi_endpoint(
    precipitation: List[float],
    temperature: List[float]
):
    """
    Calculate Relative Wetness Index (RWI) based on precipitation and temperature
    """
    try:
        result = calculate_relative_wetness_index(precipitation, temperature)
        return {
            "rwi_values": result,
            "n_values": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RWI calculation failed: {str(e)}")

@router.post("/climate-risk-modeling/synoptic-circulation-patterns")
async def extract_synoptic_patterns_endpoint(
    pressure_data: List[float],
    wind_data: List[Tuple[float, float]],  # (speed, direction)
    lat_lon_data: List[Tuple[float, float]]  # (lat, lon)
):
    """
    Extract synoptic circulation patterns based on pressure and wind data
    """
    try:
        result = extract_synoptic_circulation_patterns(pressure_data, wind_data, lat_lon_data)
        return {
            "circulation_patterns": result,
            "n_patterns": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synoptic pattern extraction failed: {str(e)}")

@router.post("/climate-risk-modeling/vertical-temperature-gradient")
async def calculate_temp_gradient_endpoint(
    temperature_profile_data: List[List[float]]  # [temp_surface, temp_850hpa, temp_700hpa, ...]
):
    """
    Calculate vertical temperature gradient (instability indicator)
    """
    try:
        result = calculate_vertical_temperature_gradient(temperature_profile_data)
        return {
            "temperature_gradients": result,
            "n_gradients": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Temperature gradient calculation failed: {str(e)}")

@router.post("/climate-risk-modeling/regularized-loss")
async def calculate_regularized_loss_endpoint(
    y_true: List[float],
    y_pred: List[float],
    model_weights: List[float],
    gamma: float = Query(1.0, description="Time penalty coefficient (γ)"),
    lambda_reg: float = Query(0.01, description="Regularization coefficient (λ)"),
    loss_type: str = Query("mse", regex="^(mse|mae|huber)$", description="Type of primary loss function")
):
    """
    Calculate regularized loss function: L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f)
    where Ω(f) = γT + ½λ||w||²
    """
    try:
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        weights_arr = np.array(model_weights)
        
        if len(y_true_arr) != len(y_pred_arr):
            raise HTTPException(status_code=400, detail="y_true and y_pred must have same length")
        
        result = regularized_loss_function(
            y_true_arr, y_pred_arr, weights_arr, gamma, lambda_reg, loss_type
        )
        
        return {
            "regularized_loss": result,
            "gamma": gamma,
            "lambda": lambda_reg,
            "loss_type": loss_type,
            "n_observations": len(y_true_arr)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regularized loss calculation failed: {str(e)}")

@router.post("/climate-risk-modeling/comprehensive-risk-assessment")
async def comprehensive_climate_risk_assessment_endpoint(
    precipitation_data: List[float],
    temperature_data: List[float],
    pressure_data: List[float],
    wind_data: List[Tuple[float, float]],  # (speed, direction)
    lat_lon_data: List[Tuple[float, float]],  # (lat, lon)
    temp_profile_data: List[List[float]],  # [temp_surface, temp_850hpa, temp_700hpa, ...]
    target_values: List[float],
    gamma: float = Query(0.1, description="Time penalty coefficient (γ)"),
    lambda_reg: float = Query(0.01, description="Regularization coefficient (λ)")
):
    """
    Perform comprehensive climate risk assessment using advanced features:
    - SPI (Standardized Precipitation Index) 3/6/12 months
    - RWI (Relative Wetness Index)
    - Synoptic circulation patterns
    - Vertical temperature gradients
    - Regularized loss function: L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f) where Ω(f) = γT + ½λ||w||²
    """
    try:
        result = comprehensive_climate_risk_assessment(
            precipitation_data, temperature_data, pressure_data,
            wind_data, lat_lon_data, temp_profile_data, target_values,
            gamma, lambda_reg
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive risk assessment failed: {str(e)}")
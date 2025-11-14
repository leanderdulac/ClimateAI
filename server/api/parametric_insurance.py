"""
Router for Parametric Insurance Service
Implements Payout_t = K · I{Índice_t > Trigger} · min(Cap, Loss_t) with optimal trigger calculation
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from services.parametric_insurance_service import (
    parametric_insurance_service,
    calculate_wind_index,
    calculate_precipitation_index,
    calculate_temperature_index,
    calculate_composite_index,
    calculate_payout,
    calculate_parametric_insurance_contract
)

router = APIRouter()

@router.post("/parametric-insurance/wind-index")
async def calculate_wind_index_endpoint(
    wind_speed_3s_gusts: List[float],
    threshold: float = Query(20.0, description="Wind speed threshold (m/s)")
):
    """
    Calculate maximum sustained wind index (3-second gusts)
    """
    try:
        result = calculate_wind_index(wind_speed_3s_gusts, threshold)
        return {
            "wind_indices": result,
            "threshold_used": threshold,
            "n_values": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wind index calculation failed: {str(e)}")

@router.post("/parametric-insurance/precipitation-index")
async def calculate_precipitation_index_endpoint(
    precipitation_24h: List[float],
    threshold: float = Query(50.0, description="Precipitation threshold (mm)")
):
    """
    Calculate accumulated precipitation index (24h)
    """
    try:
        result = calculate_precipitation_index(precipitation_24h, threshold)
        return {
            "precipitation_indices": result,
            "threshold_used": threshold,
            "n_values": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Precipitation index calculation failed: {str(e)}")

@router.post("/parametric-insurance/temperature-index")
async def calculate_temperature_index_endpoint(
    temperature_data: List[float],
    threshold: float = Query(35.0, description="Temperature threshold (°C)")
):
    """
    Calculate consecutive high temperature index
    """
    try:
        result = calculate_temperature_index(temperature_data, threshold)
        return {
            "temperature_indices": result,
            "threshold_used": threshold,
            "n_values": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Temperature index calculation failed: {str(e)}")

@router.post("/parametric-insurance/composite-index")
async def calculate_composite_index_endpoint(
    wind_indices: List[float],
    precip_indices: List[float],
    temp_indices: List[float],
    weights: Tuple[float, float, float] = Query((0.4, 0.4, 0.2), 
                                               description="Weights for [wind, precip, temp]")
):
    """
    Calculate composite climate index combining all three indices
    """
    try:
        result = calculate_composite_index(wind_indices, precip_indices, temp_indices, weights)
        return {
            "composite_indices": result,
            "weights_used": weights,
            "n_values": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Composite index calculation failed: {str(e)}")

@router.post("/parametric-insurance/payout")
async def calculate_payout_endpoint(
    index_values: List[float],
    losses: List[float],
    trigger: float = Query(..., description="Trigger threshold"),
    cap: float = Query(..., gt=0, description="Payout cap"),
    factor: float = Query(1.0, description="Payout factor (K)")
):
    """
    Calculate parametric insurance payouts: 
    Payout_t = K · I{Índice_t > Trigger} · min(Cap, Loss_t)
    """
    try:
        result = calculate_payout(index_values, losses, trigger, cap, factor)
        return {
            "payouts": result,
            "trigger": trigger,
            "cap": cap,
            "factor": factor,
            "n_payouts": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payout calculation failed: {str(e)}")

@router.post("/parametric-insurance/optimize-trigger")
async def optimize_trigger_endpoint(
    index_values: List[float],
    losses: List[float],
    cap: float = Query(..., gt=0, description="Payout cap"),
    factor: float = Query(1.0, description="Payout factor (K)"),
    basis_risk_weight: float = Query(0.1, description="Basis risk weight (λ)"),
    min_trigger: float = Query(0.0, description="Minimum trigger value"),
    max_trigger: Optional[float] = Query(None, description="Maximum trigger value")
):
    """
    Optimize trigger level: argmin_T [E[(Payout - Loss)²] + λ·BasisRisk]
    """
    try:
        # If max_trigger not provided, calculate it
        if max_trigger is None:
            max_trigger = max(index_values) * 1.1
        
        # In the actual service this would be implemented, but we'll just return a mock response
        # since the real optimization is in the service
        result = parametric_insurance_service.optimize_trigger(
            index_values, losses, cap, factor, basis_risk_weight,
            trigger_bounds=(min_trigger, max_trigger)
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trigger optimization failed: {str(e)}")

@router.post("/parametric-insurance/contract")
async def calculate_parametric_insurance_contract_endpoint(
    wind_speed_3s_gusts: List[float],
    precipitation_24h: List[float],
    temperature_data: List[float],
    actual_losses: List[float],
    cap: float = Query(..., gt=0, description="Payout cap"),
    factor: float = Query(1.0, description="Payout factor (K)"),
    trigger: Optional[float] = Query(None, description="Trigger threshold (if None, will be optimized)"),
    basis_risk_weight: float = Query(0.1, description="Basis risk weight (λ)"),
    wind_threshold: float = Query(20.0, description="Wind speed threshold (m/s)"),
    precip_threshold: float = Query(50.0, description="Precipitation threshold (mm)"),
    temp_threshold: float = Query(35.0, description="Temperature threshold (°C)"),
    optimize_trigger: bool = Query(True, description="Whether to optimize the trigger")
):
    """
    Complete parametric insurance contract calculation:
    - Payout_t = K · I{Índice_t > Trigger} · min(Cap, Loss_t)
    - Índice_t = f(dados_climáticos_t) combining wind, precipitation, temperature
    - Optimal trigger via: argmin_T [E[(Payout - Loss)²] + λ·BasisRisk]
    """
    try:
        result = calculate_parametric_insurance_contract(
            wind_speed_3s_gusts, precipitation_24h, temperature_data,
            actual_losses, cap, factor, trigger, basis_risk_weight,
            wind_threshold, precip_threshold, temp_threshold,
            optimize_trigger_flag=optimize_trigger
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parametric insurance contract calculation failed: {str(e)}")

@router.get("/parametric-insurance/status")
async def parametric_insurance_status():
    """
    Get the status of the parametric insurance service
    """
    return {
        "service_available": True,
        "timestamp": datetime.now().isoformat()
    }
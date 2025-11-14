"""
Router for Climate Regime Hidden Markov Model Service
Implements P(S_t = j | S_{t-1} = i) = A_ij(ΔT_t) and P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j)
Where θ_t = vector of climate forcings (CO₂, CH₄, aerosols)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np

from services.climate_hmm_service import (
    climate_hmm_service,
    compute_regime_transition_probabilities,
    compute_emission_probabilities,
    compute_climate_regime_model
)

router = APIRouter()

@router.post("/climate-hmm/regime-transition-probabilities")
async def compute_regime_transition_probabilities_endpoint(
    current_forcing: List[float] = Query(..., description="Climate forcing vector [CO₂, CH₄, aerosols]"),
    previous_temperatures: List[float] = Query(..., description="Recent temperature history"),
    n_states: int = Query(4, ge=2, le=10, description="Number of climate regimes")
):
    """
    Compute regime transition probabilities P(S_t = j | S_{t-1} = i) = A_ij(ΔT_t)
    Where transition probabilities depend on climate forcing factors
    """
    try:
        if len(current_forcing) != 3:
            raise HTTPException(status_code=400, detail="Climate forcing must have 3 values: [CO₂, CH₄, aerosols]")
        
        result = compute_regime_transition_probabilities(
            current_forcing, previous_temperatures, n_states
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regime transition probability calculation failed: {str(e)}")

@router.post("/climate-hmm/emission-probabilities")
async def compute_emission_probabilities_endpoint(
    observations: List[float] = Query(..., description="Observed climate data [temp, precip, pressure, ...]"),
    current_forcing: List[float] = Query(..., description="Climate forcing vector [CO₂, CH₄, aerosols]"),
    n_states: int = Query(4, ge=2, le=10, description="Number of climate regimes")
):
    """
    Compute emission probabilities P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j)
    Where emission probabilities depend on climate forcing factors
    """
    try:
        if len(current_forcing) != 3:
            raise HTTPException(status_code=400, detail="Climate forcing must have 3 values: [CO₂, CH₄, aerosols]")
        
        result = compute_emission_probabilities(
            observations, current_forcing, n_states
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emission probability calculation failed: {str(e)}")

@router.post("/climate-hmm/climate-regime-model")
async def compute_climate_regime_model_endpoint(
    climate_observations: List[List[float]],  # Sequence of [temperature, precipitation, pressure, ...]
    climate_forcings: List[List[float]],      # Sequence of [CO₂, CH₄, aerosols]
    temperatures_history: List[float],
    n_states: int = Query(4, ge=2, le=10, description="Number of climate regimes")
):
    """
    Complete climate regime Hidden Markov Model:
    - P(S_t = j | S_{t-1} = i) = A_ij(ΔT_t) (transition probabilities depending on climate forcing)
    - P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j) (emission probabilities depending on climate forcings)
    - Where θ_t = [CO₂, CH₄, aerosols]
    """
    try:
        if not climate_observations or not climate_forcings:
            raise HTTPException(status_code=400, detail="Climate observations and forcings cannot be empty")
        
        if len(climate_observations) != len(climate_forcings):
            raise HTTPException(status_code=400, detail="Observations and forcings must have the same length")
        
        for forcing in climate_forcings:
            if len(forcing) != 3:
                raise HTTPException(status_code=400, detail="Each forcing vector must have 3 values: [CO₂, CH₄, aerosols]")
        
        result = compute_climate_regime_model(
            climate_observations, climate_forcings, temperatures_history, n_states
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Climate regime model calculation failed: {str(e)}")

@router.get("/climate-hmm/status")
async def climate_hmm_status():
    """
    Get the status of the climate HMM service
    """
    return {
        "service_available": True,
        "n_states_supported": 4,  # Default number of climate regimes
        "climate_forcing_variables": ["CO₂", "CH₄", "aerosols"],
        "regime_descriptions": {
            0: "Cool/Precipitous",
            1: "Warm/Dry", 
            2: "Hot/Arid",
            3: "Variable/Moderate"
        },
        "timestamp": datetime.now().isoformat()
    }
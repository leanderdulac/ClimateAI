"""
API Router for Loss Expectancy Index Calculation Service
Implements: LEI = Exp_o × t_o × f_o × SCR_normalizado
With climate-adjusted rate: t_o_clim = t_o × (1 + γ·SCR)^δ
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.lei_service import (
    PropertyExposure,
    LEIResult,
    calculate_lei_score
)

router = APIRouter()

@router.post("/lei/calculate")
async def calculate_lei_endpoint(
    property_id: str = Query(..., description="Unique property identifier"),
    exposed_value: float = Query(..., gt=0, description="Exposed value of the property (reconstruction value)"),
    property_type: str = Query("residential", description="Property type: residential, commercial, industrial, agricultural, institutional"),
    latitude: float = Query(..., ge=-90, le=90, description="Property latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Property longitude"),
    occupancy_factor: float = Query(1.0, ge=0, le=5, description="Occupancy-specific factor"),
    region_id: str = Query(..., description="Region identifier for sinistrality data"),
    scr_score: float = Query(..., ge=0, description="Current SCR score"),
    custom_occupational_factor: float = Query(None, ge=0, le=5, description="Custom occupational factor"),
    custom_gamma: float = Query(None, ge=0, le=5, description="Custom climate sensitivity coefficient γ (default 0.35)"),
    custom_delta: float = Query(None, ge=0, le=5, description="Custom climate exponentiality coefficient δ (default 1.2)")
):
    """
    Calculate Loss Expectancy Index using the formula:
    LEI = Exp_o × t_o × f_o × SCR_normalizado
    With climate-adjusted rate: t_o_clim = t_o × (1 + γ·SCR)^δ
    """
    try:
        # Validate property type
        valid_property_types = ["residential", "commercial", "industrial", "agricultural", "institutional"]
        if property_type.lower() not in valid_property_types:
            raise HTTPException(status_code=400, detail=f"Invalid property type. Valid options: {valid_property_types}")
        
        # Create property exposure object
        property_exposure = PropertyExposure(
            property_id=property_id,
            exposed_value=exposed_value,
            property_type=property_type,
            location_coordinates=(latitude, longitude),
            occupancy_factor=occupancy_factor
        )
        
        # Calculate LEI score
        result = calculate_lei_score(
            property_exposure=property_exposure,
            region_id=region_id,
            scr_score=scr_score,
            custom_occupational_factor=custom_occupational_factor,
            custom_gamma=custom_gamma,
            custom_delta=custom_delta
        )
        
        # Return result
        return {
            "lei_value": result.lei_value,
            "exposed_value": result.exposed_value,
            "base_sinistrality_rate": result.base_sinistrality_rate,
            "climate_adjusted_rate": result.climate_adjusted_rate,
            "occupational_factor": result.occupational_factor,
            "normalized_scr": result.normalized_scr,
            "climate_sensitivity_coeff": result.climate_sensitivity_coeff,
            "climate_exponentiality_coeff": result.climate_exponentiality_coeff,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "input_parameters": {
                "property_id": property_exposure.property_id,
                "exposed_value": property_exposure.exposed_value,
                "property_type": property_exposure.property_type,
                "location_coordinates": property_exposure.location_coordinates,
                "occupancy_factor": property_exposure.occupancy_factor,
                "region_id": region_id,
                "scr_score": scr_score,
                "custom_occupational_factor": custom_occupational_factor,
                "custom_gamma": custom_gamma,
                "custom_delta": custom_delta
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LEI calculation failed: {str(e)}")

@router.get("/lei/info")
async def lei_info():
    """
    Get information about the Loss Expectancy Index calculation service
    """
    return {
        "description": "Loss Expectancy Index Calculation Service",
        "formula": "LEI = Exp_o × t_o × f_o × SCR_normalizado",
        "components": {
            "Exp_o": "Valor exposto do imóvel (reconstrução)",
            "t_o": "Taxa de sinistralidade histórica da região (ajustada)",
            "f_o": "Fator de exposição ocupacional (residencial, comercial, etc.)",
            "SCR_normalizado": "SCR / 1000 [transformação probabilística]"
        },
        "climate_adjustment": {
            "formula": "t_o_clim = t_o × (1 + γ·SCR)^δ",
            "parameters": {
                "gamma": "Sensitivity coefficient (default 0.35)",
                "delta": "Risk exponentiality coefficient (default 1.2)"
            }
        },
        "methodology": "Climate-Adjusted Insurance Risk Assessment",
        "features": [
            "Regional sinistrality rate adjustment",
            "Climate sensitivity modeling",
            "Property type-specific factors",
            "Occupancy-based risk adjustment",
            "Dynamic SCR normalization"
        ],
        "default_property_factors": {
            "residential": 0.8,
            "commercial": 1.2,
            "industrial": 1.5,
            "agricultural": 1.0,
            "institutional": 1.1
        },
        "supported_regions": [
            "sao_paulo",
            "rio_de_janeiro", 
            "curitiba",
            "salvador",
            "brasilia"
        ]
    }
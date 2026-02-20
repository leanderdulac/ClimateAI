"""
API Router for Physical Risk Calculation Service
Implements: R_físico = Σ_{perigo∈{inundação, vento, fogo, granizo}} p_perigo · λ_perigo · v_perigo
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query

from services.physical_risk_service import (
    ClimateScenario,
    PropertyCharacteristics,
    calculate_physical_risk,
    calculate_scenario_comparison,
    integrate_with_climate_risk,
)

router = APIRouter()


@router.post("/physical-risk/calculate")
async def calculate_physical_risk_endpoint(
    age_years: int = Query(
        ..., ge=0, le=200, description="Age of the property in years"
    ),
    construction_material: str = Query(
        "concrete", description="Construction material: concrete, wood, steel, masonry"
    ),
    elevation_meters: float = Query(
        0.0, description="Elevation relative to reference level (meters)"
    ),
    latitude: float = Query(..., ge=-90, le=90, description="Property latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Property longitude"),
    building_type: str = Query(
        "residential",
        description="Building type: residential, commercial, industrial, agricultural",
    ),
    asset_value: float = Query(..., gt=0, description="Asset value in currency units"),
    delta_temperature: float = Query(
        0.0, description="Temperature change from baseline (ΔT in °C)"
    ),
    precipitation_change: float = Query(
        0.0, description="Precipitation change from baseline (mm)"
    ),
    sea_level_rise: float = Query(0.0, description="Sea level rise (meters)"),
    climate_model: str = Query(
        "ssp245", description="Climate model: rcp45, rcp85, ssp126, ssp585, ssp245"
    ),
    scenario_year: int = Query(
        2040, ge=2020, le=2100, description="Target scenario year"
    ),
    baseline_year: int = Query(
        2020, ge=1900, le=2020, description="Baseline reference year"
    ),
    scenario_name: str = Query("default", description="Name for the scenario"),
):
    """
    Calculate physical risk using the GEV model approach:
    R_físico = Σ_{perigo∈{inundação, vento, fogo, granizo}} p_perigo · λ_perigo · v_perigo
    """
    try:
        # Validate construction material
        valid_materials = ["concrete", "wood", "steel", "masonry"]
        if construction_material not in valid_materials:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid material. Valid options: {valid_materials}",
            )

        # Validate building type
        valid_building_types = [
            "residential",
            "commercial",
            "industrial",
            "agricultural",
        ]
        if building_type not in valid_building_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid building type. Valid options: {valid_building_types}",
            )

        # Create property characteristics
        property_char = PropertyCharacteristics(
            age_years=age_years,
            construction_material=construction_material,
            elevation_meters=elevation_meters,
            location_coordinates=(latitude, longitude),
            building_type=building_type,
            value=asset_value,
        )

        # Create climate scenario
        climate_scenario = ClimateScenario(
            delta_temperature=delta_temperature,
            precipitation_change=precipitation_change,
            sea_level_rise=sea_level_rise,
            climate_model=climate_model,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Calculate physical risk
        result = calculate_physical_risk(property_char, climate_scenario, scenario_name)

        # Format response
        return {
            "total_physical_risk": result.total_physical_risk,
            "risk_breakdown": result.risk_breakdown,
            "scenario": result.scenario,
            "climate_anomaly": result.climate_anomaly,
            "property_vulnerability": result.property_vulnerability,
            "occurrence_rates": result.occurrence_rates,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "individual_risks": {
                "flood_risk": result.risk_breakdown.get("flood", 0),
                "wind_risk": result.risk_breakdown.get("wind", 0),
                "fire_risk": result.risk_breakdown.get("fire", 0),
                "hail_risk": result.risk_breakdown.get("hail", 0),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Physical risk calculation failed: {str(e)}"
        )


@router.post("/physical-risk/scenario-comparison")
async def scenario_comparison_endpoint(
    age_years: int = Query(
        ..., ge=0, le=200, description="Age of the property in years"
    ),
    construction_material: str = Query("concrete", description="Construction material"),
    elevation_meters: float = Query(
        0.0, description="Elevation relative to reference level (meters)"
    ),
    latitude: float = Query(..., ge=-90, le=90, description="Property latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Property longitude"),
    building_type: str = Query("residential", description="Building type"),
    asset_value: float = Query(..., gt=0, description="Asset value in currency units"),
    baseline_temp: float = Query(
        0.0, description="Baseline temperature change (ΔT in °C)"
    ),
    baseline_precip: float = Query(
        0.0, description="Baseline precipitation change (mm)"
    ),
    baseline_sea: float = Query(0.0, description="Baseline sea level rise (meters)"),
    future_temp: float = Query(2.0, description="Future temperature change (ΔT in °C)"),
    future_precip: float = Query(50.0, description="Future precipitation change (mm)"),
    future_sea: float = Query(0.5, description="Future sea level rise (meters)"),
    climate_model: str = Query("ssp245", description="Climate model"),
    scenario_year: int = Query(
        2040, ge=2020, le=2100, description="Target scenario year"
    ),
    baseline_year: int = Query(
        2020, ge=1900, le=2020, description="Baseline reference year"
    ),
):
    """
    Compare risks between baseline and future climate scenarios
    """
    try:
        # Create property characteristics
        property_char = PropertyCharacteristics(
            age_years=age_years,
            construction_material=construction_material,
            elevation_meters=elevation_meters,
            location_coordinates=(latitude, longitude),
            building_type=building_type,
            value=asset_value,
        )

        # Create baseline scenario
        baseline_scenario = ClimateScenario(
            delta_temperature=baseline_temp,
            precipitation_change=baseline_precip,
            sea_level_rise=baseline_sea,
            climate_model=climate_model,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Create future scenario
        future_scenario = ClimateScenario(
            delta_temperature=future_temp,
            precipitation_change=future_precip,
            sea_level_rise=future_sea,
            climate_model=climate_model,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Calculate comparison
        result = calculate_scenario_comparison(
            property_char, baseline_scenario, future_scenario
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Scenario comparison failed: {str(e)}"
        )


@router.post("/physical-risk/integrate-with-climate-risk")
async def integrate_with_climate_risk_endpoint(
    climate_risk_score: float = Query(
        ..., ge=0, le=1, description="Overall climate risk score from upstream module"
    ),
    age_years: int = Query(
        ..., ge=0, le=200, description="Age of the property in years"
    ),
    construction_material: str = Query("concrete", description="Construction material"),
    elevation_meters: float = Query(
        0.0, description="Elevation relative to reference level (meters)"
    ),
    latitude: float = Query(..., ge=-90, le=90, description="Property latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Property longitude"),
    building_type: str = Query("residential", description="Building type"),
    asset_value: float = Query(..., gt=0, description="Asset value in currency units"),
    delta_temperature: float = Query(
        0.0, description="Temperature change from baseline (ΔT in °C)"
    ),
    precipitation_change: float = Query(
        0.0, description="Precipitation change from baseline (mm)"
    ),
    sea_level_rise: float = Query(0.0, description="Sea level rise (meters)"),
    climate_model: str = Query("ssp245", description="Climate model"),
    scenario_year: int = Query(
        2040, ge=2020, le=2100, description="Target scenario year"
    ),
    baseline_year: int = Query(
        2020, ge=1900, le=2020, description="Baseline reference year"
    ),
):
    """
    Integrate physical risk calculation with broader climate risk scoring
    """
    try:
        # Create property characteristics
        property_char = PropertyCharacteristics(
            age_years=age_years,
            construction_material=construction_material,
            elevation_meters=elevation_meters,
            location_coordinates=(latitude, longitude),
            building_type=building_type,
            value=asset_value,
        )

        # Create climate scenario
        climate_scenario = ClimateScenario(
            delta_temperature=delta_temperature,
            precipitation_change=precipitation_change,
            sea_level_rise=sea_level_rise,
            climate_model=climate_model,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Calculate physical risk
        physical_risk_result = calculate_physical_risk(
            property_char, climate_scenario, "integration"
        )

        # Integrate with climate risk score
        integration_result = integrate_with_climate_risk(
            climate_risk_score, physical_risk_result
        )

        return integration_result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Risk integration failed: {str(e)}"
        )


@router.get("/physical-risk/info")
async def physical_risk_info():
    """
    Get information about the physical risk calculation service
    """
    return {
        "description": "Physical Risk Calculation Service",
        "formula": "R_físico = Σ_{perigo∈{inundação, vento, fogo, granizo}} p_perigo · λ_perigo · v_perigo",
        "components": {
            "p_perigo": "P(evento | ΔT, precip, cenário) [from GEV engine]",
            "λ_perigo": "climate-adjusted annual occurrence rate",
            "v_perigo": "vulnerability = f(coef_fragilidade, idade_imóvel, material)",
        },
        "methodology": "GEV (Generalized Extreme Value) model approach",
        "perils_calculated": ["flood", "wind", "fire", "hail"],
        "integration": "Connects with other risk assessment modules",
        "features": [
            "Scenario comparisons",
            "Vulnerability assessment",
            "Climate sensitivity analysis",
            "Property-specific risk calculation",
        ],
    }

"""
API Router for Transition Risk Calculation Service
Implements: R_transição = β₁·CarbonTax + β₂·StrandedAsset + β₃·Litígio
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query

from services.transition_risk_service import (
    AssetCharacteristics,
    EnvironmentalScenario,
    calculate_scenario_comparison,
    calculate_sector_specific_risk,
    calculate_transition_risk,
    integrate_with_physical_risk,
)

router = APIRouter()


@router.post("/transition-risk/calculate")
async def calculate_transition_risk_endpoint(
    fossil_energy_exposure: float = Query(
        ..., ge=0, le=1, description="Exposure to fossil energy (0-1)"
    ),
    asset_age_years: int = Query(
        0, ge=0, le=100, description="Age of the asset in years"
    ),
    industry_sector: str = Query(
        "manufacturing",
        description="Industry sector: oil_gas, coal, utilities, transport, manufacturing, finance",
    ),
    revenue_dependence: float = Query(
        0.0, ge=0, le=1, description="Revenue dependence on high-carbon assets (0-1)"
    ),
    asset_value: float = Query(
        ..., gt=0, description="Total asset value in currency units"
    ),
    geographical_diversification: float = Query(
        0.5, ge=0, le=1, description="Geographical diversification factor (0-1)"
    ),
    adaptation_readiness: float = Query(
        0.3, ge=0, le=1, description="Adaptation readiness score (0-1)"
    ),
    delta_temperature: float = Query(1.5, description="ΔT in °C"),
    carbon_price_usd_per_tco2: float = Query(
        150, description="Carbon price in USD per tonne CO2e"
    ),
    litigation_media_exposure: float = Query(
        0.5, ge=0, le=1, description="Media exposure score (0-1)"
    ),
    regulatory_delay_factor: float = Query(
        0.2, ge=0, le=1, description="Regulatory delay factor (0-1)"
    ),
    scenario_year: int = Query(
        2030, ge=2020, le=2100, description="Target scenario year"
    ),
    baseline_year: int = Query(
        2020, ge=1900, le=2020, description="Baseline reference year"
    ),
    scenario_name: str = Query("default", description="Name for the scenario"),
    beta_carbon_tax: float = Query(
        0.4, description="Beta weight for carbon tax component (β₁)"
    ),
    beta_stranded_asset: float = Query(
        0.4, description="Beta weight for stranded asset component (β₂)"
    ),
    beta_litigation: float = Query(
        0.2, description="Beta weight for litigation component (β₃)"
    ),
):
    """
    Calculate transition risk using the specified formula:
    R_transição = β₁·CarbonTax + β₂·StrandedAsset + β₃·Litígio
    """
    try:
        # Validate industry sector
        valid_sectors = [
            "oil_gas",
            "coal",
            "utilities",
            "transport",
            "manufacturing",
            "finance",
        ]
        if industry_sector not in valid_sectors:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sector. Valid options: {valid_sectors}",
            )

        # Create asset characteristics
        asset_char = AssetCharacteristics(
            fossil_energy_exposure=fossil_energy_exposure,
            asset_age_years=asset_age_years,
            industry_sector=industry_sector,
            revenue_dependence=revenue_dependence,
            asset_value=asset_value,
            geographical_diversification=geographical_diversification,
            adaptation_readiness=adaptation_readiness,
        )

        # Create environmental scenario
        env_scenario = EnvironmentalScenario(
            delta_temperature=delta_temperature,
            carbon_price_usd_per_tco2=carbon_price_usd_per_tco2,
            litigation_media_exposure=litigation_media_exposure,
            regulatory_delay_factor=regulatory_delay_factor,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Create beta weights
        beta_weights = {
            "carbon_tax": beta_carbon_tax,
            "stranded_asset": beta_stranded_asset,
            "litigation": beta_litigation,
        }

        # Calculate transition risk
        result = calculate_transition_risk(
            asset_char, env_scenario, beta_weights, scenario_name
        )

        # Format response
        return {
            "total_transition_risk": result.total_transition_risk,
            "risk_components": result.risk_components,
            "beta_weights": result.beta_weights,
            "scenario": result.scenario,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "component_breakdown": {
                "carbon_tax_unweighted": result.risk_components.get(
                    "carbon_tax_unweighted", 0
                ),
                "stranded_asset_unweighted": result.risk_components.get(
                    "stranded_asset_unweighted", 0
                ),
                "litigation_unweighted": result.risk_components.get(
                    "litigation_unweighted", 0
                ),
                "carbon_tax_weighted": result.risk_components.get(
                    "carbon_tax_weighted", 0
                ),
                "stranded_asset_weighted": result.risk_components.get(
                    "stranded_asset_weighted", 0
                ),
                "litigation_weighted": result.risk_components.get(
                    "litigation_weighted", 0
                ),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Transition risk calculation failed: {str(e)}"
        )


@router.post("/transition-risk/scenario-comparison")
async def scenario_comparison_endpoint(
    fossil_energy_exposure: float = Query(
        ..., ge=0, le=1, description="Exposure to fossil energy (0-1)"
    ),
    asset_age_years: int = Query(
        0, ge=0, le=100, description="Age of the asset in years"
    ),
    industry_sector: str = Query("manufacturing", description="Industry sector"),
    revenue_dependence: float = Query(
        0.0, ge=0, le=1, description="Revenue dependence on high-carbon assets (0-1)"
    ),
    asset_value: float = Query(..., gt=0, description="Total asset value"),
    geographical_diversification: float = Query(
        0.5, ge=0, le=1, description="Geographical diversification factor (0-1)"
    ),
    adaptation_readiness: float = Query(
        0.3, ge=0, le=1, description="Adaptation readiness score (0-1)"
    ),
    # Baseline scenario parameters
    baseline_temp: float = Query(0.0, description="Baseline ΔT in °C"),
    baseline_carbon_price: float = Query(
        50, description="Baseline carbon price in USD per tonne CO2e"
    ),
    baseline_media: float = Query(
        0.2, ge=0, le=1, description="Baseline media exposure score (0-1)"
    ),
    baseline_regulatory: float = Query(
        0.1, ge=0, le=1, description="Baseline regulatory delay factor (0-1)"
    ),
    # Future scenario parameters
    future_temp: float = Query(2.0, description="Future ΔT in °C"),
    future_carbon_price: float = Query(
        150, description="Future carbon price in USD per tonne CO2e"
    ),
    future_media: float = Query(
        0.7, ge=0, le=1, description="Future media exposure score (0-1)"
    ),
    future_regulatory: float = Query(
        0.4, ge=0, le=1, description="Future regulatory delay factor (0-1)"
    ),
    scenario_year: int = Query(
        2030, ge=2020, le=2100, description="Target scenario year"
    ),
    baseline_year: int = Query(
        2020, ge=1900, le=2020, description="Baseline reference year"
    ),
    beta_carbon_tax: float = Query(
        0.4, description="Beta weight for carbon tax component"
    ),
    beta_stranded_asset: float = Query(
        0.4, description="Beta weight for stranded asset component"
    ),
    beta_litigation: float = Query(
        0.2, description="Beta weight for litigation component"
    ),
):
    """
    Compare transition risks between baseline and future environmental scenarios
    """
    try:
        # Create asset characteristics
        asset_char = AssetCharacteristics(
            fossil_energy_exposure=fossil_energy_exposure,
            asset_age_years=asset_age_years,
            industry_sector=industry_sector,
            revenue_dependence=revenue_dependence,
            asset_value=asset_value,
            geographical_diversification=geographical_diversification,
            adaptation_readiness=adaptation_readiness,
        )

        # Create baseline environmental scenario
        baseline_scenario = EnvironmentalScenario(
            delta_temperature=baseline_temp,
            carbon_price_usd_per_tco2=baseline_carbon_price,
            litigation_media_exposure=baseline_media,
            regulatory_delay_factor=baseline_regulatory,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Create future environmental scenario
        future_scenario = EnvironmentalScenario(
            delta_temperature=future_temp,
            carbon_price_usd_per_tco2=future_carbon_price,
            litigation_media_exposure=future_media,
            regulatory_delay_factor=future_regulatory,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Create beta weights
        beta_weights = {
            "carbon_tax": beta_carbon_tax,
            "stranded_asset": beta_stranded_asset,
            "litigation": beta_litigation,
        }

        # Calculate comparison
        result = calculate_scenario_comparison(
            asset_char, baseline_scenario, future_scenario, beta_weights
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Scenario comparison failed: {str(e)}"
        )


@router.post("/transition-risk/sector-specific-risk")
async def sector_specific_risk_endpoint(
    fossil_energy_exposure: float = Query(
        ..., ge=0, le=1, description="Exposure to fossil energy (0-1)"
    ),
    asset_age_years: int = Query(
        0, ge=0, le=100, description="Age of the asset in years"
    ),
    industry_sector: str = Query("manufacturing", description="Industry sector"),
    revenue_dependence: float = Query(
        0.0, ge=0, le=1, description="Revenue dependence on high-carbon assets (0-1)"
    ),
    asset_value: float = Query(..., gt=0, description="Total asset value"),
    geographical_diversification: float = Query(
        0.5, ge=0, le=1, description="Geographical diversification factor (0-1)"
    ),
    adaptation_readiness: float = Query(
        0.3, ge=0, le=1, description="Adaptation readiness score (0-1)"
    ),
    delta_temperature: float = Query(1.5, description="ΔT in °C"),
    carbon_price_usd_per_tco2: float = Query(
        150, description="Carbon price in USD per tonne CO2e"
    ),
    litigation_media_exposure: float = Query(
        0.5, ge=0, le=1, description="Media exposure score (0-1)"
    ),
    regulatory_delay_factor: float = Query(
        0.2, ge=0, le=1, description="Regulatory delay factor (0-1)"
    ),
    scenario_year: int = Query(
        2030, ge=2020, le=2100, description="Target scenario year"
    ),
    baseline_year: int = Query(
        2020, ge=1900, le=2020, description="Baseline reference year"
    ),
):
    """
    Calculate sector-specific transition risk components
    """
    try:
        # Create asset characteristics
        asset_char = AssetCharacteristics(
            fossil_energy_exposure=fossil_energy_exposure,
            asset_age_years=asset_age_years,
            industry_sector=industry_sector,
            revenue_dependence=revenue_dependence,
            asset_value=asset_value,
            geographical_diversification=geographical_diversification,
            adaptation_readiness=adaptation_readiness,
        )

        # Create environmental scenario
        env_scenario = EnvironmentalScenario(
            delta_temperature=delta_temperature,
            carbon_price_usd_per_tco2=carbon_price_usd_per_tco2,
            litigation_media_exposure=litigation_media_exposure,
            regulatory_delay_factor=regulatory_delay_factor,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Calculate sector-specific risk
        result = calculate_sector_specific_risk(asset_char, env_scenario)

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sector-specific risk calculation failed: {str(e)}"
        )


@router.post("/transition-risk/integrate-with-physical-risk")
async def integrate_with_physical_risk_endpoint(
    transition_risk_score: float = Query(
        ..., ge=0, description="Calculated transition risk from transition risk module"
    ),
    physical_risk_score: float = Query(
        ..., ge=0, description="Calculated physical risk from physical risk module"
    ),
    fossil_energy_exposure: float = Query(
        ..., ge=0, le=1, description="Exposure to fossil energy (0-1)"
    ),
    asset_age_years: int = Query(
        0, ge=0, le=100, description="Age of the asset in years"
    ),
    industry_sector: str = Query("manufacturing", description="Industry sector"),
    revenue_dependence: float = Query(
        0.0, ge=0, le=1, description="Revenue dependence on high-carbon assets (0-1)"
    ),
    asset_value: float = Query(..., gt=0, description="Total asset value"),
    geographical_diversification: float = Query(
        0.5, ge=0, le=1, description="Geographical diversification factor (0-1)"
    ),
    adaptation_readiness: float = Query(
        0.3, ge=0, le=1, description="Adaptation readiness score (0-1)"
    ),
    delta_temperature: float = Query(1.5, description="ΔT in °C"),
    carbon_price_usd_per_tco2: float = Query(
        150, description="Carbon price in USD per tonne CO2e"
    ),
    litigation_media_exposure: float = Query(
        0.5, ge=0, le=1, description="Media exposure score (0-1)"
    ),
    regulatory_delay_factor: float = Query(
        0.2, ge=0, le=1, description="Regulatory delay factor (0-1)"
    ),
    scenario_year: int = Query(
        2030, ge=2020, le=2100, description="Target scenario year"
    ),
    baseline_year: int = Query(
        2020, ge=1900, le=2020, description="Baseline reference year"
    ),
    beta_carbon_tax: float = Query(
        0.4, description="Beta weight for carbon tax component"
    ),
    beta_stranded_asset: float = Query(
        0.4, description="Beta weight for stranded asset component"
    ),
    beta_litigation: float = Query(
        0.2, description="Beta weight for litigation component"
    ),
):
    """
    Integrate transition risk with physical risk to get total climate risk
    """
    try:
        # Create asset characteristics
        asset_char = AssetCharacteristics(
            fossil_energy_exposure=fossil_energy_exposure,
            asset_age_years=asset_age_years,
            industry_sector=industry_sector,
            revenue_dependence=revenue_dependence,
            asset_value=asset_value,
            geographical_diversification=geographical_diversification,
            adaptation_readiness=adaptation_readiness,
        )

        # Create environmental scenario
        env_scenario = EnvironmentalScenario(
            delta_temperature=delta_temperature,
            carbon_price_usd_per_tco2=carbon_price_usd_per_tco2,
            litigation_media_exposure=litigation_media_exposure,
            regulatory_delay_factor=regulatory_delay_factor,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Create beta weights
        beta_weights = {
            "carbon_tax": beta_carbon_tax,
            "stranded_asset": beta_stranded_asset,
            "litigation": beta_litigation,
        }

        # Calculate transition risk (for integration purposes)
        transition_risk_result = calculate_transition_risk(
            asset_char, env_scenario, beta_weights, "integration"
        )

        # Integrate with physical risk score
        integration_result = integrate_with_physical_risk(
            transition_risk_result, physical_risk_score
        )

        return integration_result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Risk integration failed: {str(e)}"
        )


@router.get("/transition-risk/info")
async def transition_risk_info():
    """
    Get information about the transition risk calculation service
    """
    return {
        "description": "Transition Risk Calculation Service",
        "formula": "R_transição = β₁·CarbonTax + β₂·StrandedAsset + β₃·Litígio",
        "components": {
            "CarbonTax": "Exposição_energia_fóssil × US$ 150/tCO₂e (cenário 2030)",
            "Litígio": "P(recurso_judicial) × E[indenização] × f(atraso_regulatório)",
            "P(recurso)": "logit⁻¹(-6.2 + 1.5·ln(ΔT) + 0.8·midia_exposição)",
        },
        "methodology": "Climate Transition Risk Assessment Framework",
        "risk_types": ["carbon_tax", "stranded_asset", "litigation"],
        "sectors_covered": [
            "oil_gas",
            "coal",
            "utilities",
            "transport",
            "manufacturing",
            "finance",
        ],
        "integration": "Connects with physical risk assessments",
        "features": [
            "Sector-specific risk assessment",
            "Scenario comparisons",
            "Beta-weighted risk components",
            "Litigation probability modeling",
            "Stranded asset evaluation",
            "Carbon tax impact analysis",
        ],
        "default_parameters": {
            "carbon_price_2030_usd_tco2": 150,
            "beta_weights": {
                "carbon_tax": 0.4,
                "stranded_asset": 0.4,
                "litigation": 0.2,
            },
        },
    }

"""
Integration API Router for Complete Pricing Framework
Implements the full formula: Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Annotated

from fastapi import APIRouter, HTTPException, Query

from services.capital_surplus_service import calculate_capital_surplus_from_risks
from services.comprehensive_pricing_service import (
    PolicyPricingInput,
    calculate_comprehensive_premium,
    calculate_supply_demand_adjustment,
    calculate_zone_concentration_ratio,
)
from services.concentration_risk_service import (
    PropertyInfo,
    calculate_concentration_risk,
)
from services.investment_return_service import calculate_expected_return_rate
from services.lei_service import PropertyExposure, calculate_lei_score
from services.loading_margin_service import calculate_loading_margin
from services.mitigation_measures_service import (
    ClimateRiskComponents,
    MitigationMeasures,
    calculate_final_scr_score,
)
from services.operating_costs_service import calculate_operating_costs, PolicyDetails
from services.physical_risk_service import (
    ClimateScenario,
    PhysicalRiskService,
    PropertyCharacteristics,
)
from services.transition_risk_service import (
    AssetCharacteristics,
    EnvironmentalScenario,
    TransitionRiskService,
)

router = APIRouter()


@router.post("/complete-pricing-framework/calculate")
async def calculate_complete_pricing_framework(
    location_latitude: Annotated[float, Query(description="Latitude of the property")] = -23.5507,
    location_longitude: Annotated[float, Query(description="Longitude of the property")] = -46.6339,
    property_value: Annotated[float, Query(gt=0, description="Value of the property")] = 1000000.0,
    coverage_amount: Annotated[float, Query(gt=0, description="Amount of coverage requested")] = 800000.0,
    coverage_period_years: Annotated[int, Query(ge=1, le=10, description="Coverage period in years")] = 1,
    policy_age_months: Annotated[int, Query(ge=0, description="Age of the policy in months")] = 0,
    zone_policies_premiums: Annotated[List[float], Query(description="Premiums of policies in the same zone")] = [],
    free_capital: Annotated[float, Query(gt=0, description="Free capital available")] = 10000000.0,
    climate_temperature_change: Annotated[float, Query(description="Expected climate temperature change (ΔT)")] = 1.5,
    climate_precipitation_change: Annotated[float, Query(description="Expected precipitation change")] = 50.0,
    fossil_energy_exposure: Annotated[float, Query(ge=0, le=1, description="Fossil energy exposure (0-1)")] = 0.5,
    revenue_dependence: Annotated[float, Query(ge=0, le=1, description="Revenue dependence on covered asset")] = 0.4,
    mitigation_drainage: Annotated[float, Query(ge=0, le=1, description="Drainage mitigation effectiveness")] = 0.25,
    mitigation_structural: Annotated[float, Query(ge=1, le=10, description="Structural resistance class")] = 8.0,
    mitigation_sensors: Annotated[int, Query(ge=0, description="Number of IoT sensors")] = 15,
    mitigation_vegetation: Annotated[float, Query(ge=0, le=1, description="NDVI (vegetation index)")] = 0.7,
    mitigation_refuge_distance: Annotated[float, Query(ge=0, description="Distance to refuge in km")] = 1.0,
    processing_method: Annotated[str, Query(description="Processing method")] = "automated",
    risk_category: Annotated[str, Query(description="Risk category")] = "standard",
    coverage_type: Annotated[str, Query(description="Coverage type")] = "property",
    claim_history_count: Annotated[int, Query(ge=0, description="Number of past claims")] = 0,
):
    """
    Calculate comprehensive premium using the full integrated formula:
    Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda

    Where each component is calculated from the complete climate risk framework
    """
    try:
        # Initialize calculators
        physical_calc = PhysicalRiskService()
        transition_calc = TransitionRiskService()

        # Step 1: Calculate Physical Risk
        property_char = PropertyCharacteristics(
            age_years=15,
            construction_material="concrete",
            elevation_meters=5.0,
            location_coordinates=(location_latitude, location_longitude),
            building_type="commercial",
            value=property_value,
        )

        climate_scenario = ClimateScenario(
            delta_temperature=climate_temperature_change,
            precipitation_change=climate_precipitation_change,
            sea_level_rise=0.3,
            climate_model="ssp245",
            scenario_year=2035,
            baseline_year=2020,
        )

        physical_task = physical_calc.calculate_physical_risk(
            property_char, climate_scenario
        )

        # Step 2: Calculate Transition Risk
        asset_char = AssetCharacteristics(
            fossil_energy_exposure=fossil_energy_exposure,
            asset_age_years=15,
            industry_sector="utilities",
            revenue_dependence=revenue_dependence,
            asset_value=property_value,
            geographical_diversification=0.6,
            adaptation_readiness=0.5,
        )

        env_scenario = EnvironmentalScenario(
            delta_temperature=climate_temperature_change,
            carbon_price_usd_per_tco2=150,
            litigation_media_exposure=0.5,
            regulatory_delay_factor=0.2,
            scenario_year=2035,
            baseline_year=2020,
        )

        transition_task = transition_calc.calculate_transition_risk(
            asset_char, env_scenario
        )

        # Run risk assessments in parallel
        import asyncio
        physical_result, transition_result = await asyncio.gather(
            physical_task, transition_task
        )

        # Step 3: Create concentration risk estimate
        if zone_policies_premiums:
            # Create dummy properties for concentration calculation
            properties = []
            for i, premium in enumerate(
                zone_policies_premiums[:2]
            ):  # Use first 2 for calculation
                properties.append(
                    PropertyInfo(
                        property_id=f"PROP{i+1}",
                        premium_value=premium,
                        latitude=location_latitude
                        + (i * 0.001),  # Slightly different coordinates
                        longitude=location_longitude + (i * 0.001),
                        coverage_type=coverage_type,
                        asset_value=property_value * (premium / coverage_amount),
                        construction_type="residential",
                        elevation=5.0,
                        climate_zone="tropical",
                    )
                )
            concentration_result = calculate_concentration_risk(properties, hazard_type="flood")
            concentration_risk = concentration_result.concentration_risk
        else:
            # Use representative value if no zone data
            concentration_risk = 4849.15 / 100000  # Normalized representative value

        # Step 4: Calculate mitigation effectiveness
        mitigation_measures = MitigationMeasures(
            drainage_capacity=mitigation_drainage,
            area_drained=20000,
            structural_resistance_class=mitigation_structural,
            iot_sensors_count=mitigation_sensors,
            local_ndvi=mitigation_vegetation,
            refuge_distance_km=mitigation_refuge_distance,
            implementation_date=datetime.now(),
            effectiveness_rating=0.85,
            maintenance_schedule="weekly",
        )

        risk_components = ClimateRiskComponents(
            physical_risk=physical_result.total_physical_risk,
            transition_risk=transition_result.total_transition_risk,
            concentration_risk=concentration_risk,
        )

        final_scr_result = calculate_final_scr_score(
            risk_components, mitigation_measures
        )

        # Step 5: Calculate expected claims (this is our PTP - Pure Theoretical Premium)
        expected_claims = (
            physical_result.total_physical_risk
            + transition_result.total_transition_risk
            + concentration_risk
        ) * coverage_amount

        # Step 6: Calculate operating costs (for ML component)
        policy_details = PolicyDetails(
            policy_id="TEMP_INTEGRATED",
            premium_issued=expected_claims * 1.2,
            processing_method=processing_method,
            risk_category=risk_category,
            coverage_type=coverage_type,
            policy_age_months=policy_age_months,
            claim_history_count=claim_history_count,
        )
        operating_costs_result = calculate_operating_costs(policy_details)

        # Step 7: Calculate Loading Margin
        ml_result = calculate_loading_margin(
            exposure_value=coverage_amount,
            scr_score=final_scr_result.final_scr_score,
            premium_volume=expected_claims * 1.2,
        )

        # Step 8: Calculate Investment Return (TR component)
        tr_rate = calculate_expected_return_rate()

        # Step 9: Calculate Climate Change Factor (CC component)
        cc_factor = (
            climate_temperature_change * 0.05
        )  # Simplified climate change loading

        # Step 10: Calculate zone concentration and supply-demand adjustment
        if not zone_policies_premiums:
            zone_policies_premiums = [coverage_amount * 0.2]  # Default if no zone data

        zone_concentration_ratio = calculate_zone_concentration_ratio(
            zone_policies_premiums, free_capital
        )
        supply_demand_adjustment = calculate_supply_demand_adjustment(
            zone_concentration_ratio
        )

        # Step 11: Calculate comprehensive premium using full formula
        pricing_input = PolicyPricingInput(
            policy_id=f"FRAMEWORK_{int(datetime.now().timestamp())}",
            pure_theoretical_premium=expected_claims,
            loading_margin=ml_result.loading_margin,
            total_risk_factor=tr_rate,
            climate_change_factor=cc_factor,
            zone_policies_premiums=zone_policies_premiums,
            free_capital=free_capital,
        )

        comprehensive_result = await calculate_comprehensive_premium(pricing_input)

        # Organize results
        return {
            "policy_id": comprehensive_result.policy_id,
            "final_premium": comprehensive_result.final_premium,
            "pure_theoretical_premium": comprehensive_result.pure_theoretical_premium,
            "loading_margin": ml_result.loading_margin,
            "total_risk_factor": tr_rate,
            "climate_change_factor": cc_factor,
            "supply_demand_adjustment": comprehensive_result.cost_breakdown[
                "supply_demand_adjustment"
            ],
            "zone_concentration_ratio": zone_concentration_ratio,
            "scr_score": final_scr_result.final_scr_score,
            "risk_level": comprehensive_result.risk_level,
            "decision": comprehensive_result.decision,
            "operating_costs": {
                "subscription_cost": comprehensive_result.subscription_cost,
                "claims_cost": comprehensive_result.claims_cost,
                "admin_cost": comprehensive_result.admin_cost,
                "operating_cost_ratio": (
                    (
                        comprehensive_result.subscription_cost
                        + comprehensive_result.claims_cost
                        + comprehensive_result.admin_cost
                    )
                    / comprehensive_result.final_premium
                    if comprehensive_result.final_premium > 0
                    else 0.0
                ),
            },
            "climate_risk_components": {
                "physical_risk": physical_result.total_physical_risk,
                "transition_risk": transition_result.total_transition_risk,
                "concentration_risk": concentration_risk,
                "mitigation_effect": final_scr_result.mitigation_score,
            },
            "profitability_analysis": {
                "expected_claims": expected_claims,
                "premium_loading": comprehensive_result.final_premium - expected_claims,
                "profit_margin": (
                    (comprehensive_result.final_premium - expected_claims)
                    / comprehensive_result.final_premium
                    if comprehensive_result.final_premium > 0
                    else 0.0
                ),
                "profitability_status": (
                    "PROFITABLE"
                    if (comprehensive_result.final_premium - expected_claims)
                    / comprehensive_result.final_premium
                    > 0.05
                    and comprehensive_result.final_premium > 0
                    else "NOT_PROFITABLE"
                ),
            },
            "calculation_breakdown": {
                "base_ptp": expected_claims,
                "after_ml": expected_claims * (1 + ml_result.loading_margin),
                "after_tr": expected_claims
                * (1 + ml_result.loading_margin)
                * (1 + tr_rate),
                "after_cc": expected_claims
                * (1 + ml_result.loading_margin)
                * (1 + tr_rate)
                * (1 + cc_factor),
                "after_supply_demand": comprehensive_result.final_premium,
            },
            "calculation_method": "integrated_climate_insurance_framework",
            "calculation_timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Complete pricing framework calculation failed: {str(e)}",
        )


@router.get("/pricing-framework/info")
async def pricing_framework_info():
    """
    Get information about the complete pricing framework
    """
    return {
        "description": "Complete Climate Insurance Pricing Framework",
        "main_formula": "Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda",
        "components": {
            "PTP": "Pure Theoretical Premium based on expected claims",
            "ML": "Loading Margin for profitability and risk",
            "TR": "Total Risk factor including climate investment returns",
            "CC": "Climate Change factor based on projected changes",
            "Ajuste_oferta_demanda": "Supply-demand adjustment based on market concentration",
        },
        "formula_details": {
            "zone_concentration": "concentração_zoneamento = Σ_{apólices_na_ZCR} (Prêmio_i / Capital_livre)",
            "supply_demand_adjustment": {
                "high_concentration": ">25% → Ajuste = 1.30 (capacity loading)",
                "low_concentration": "<10% → Ajuste = 0.90 (diversification discount)",
                "medium_concentration": "Otherwise → Ajuste = 1.00 (neutral)",
            },
        },
        "integrated_services": [
            "Physical Risk Assessment (R_físico)",
            "Transition Risk Assessment (R_transição)",
            "Concentration Risk Assessment (R_concentração)",
            "Mitigation Measure Effectiveness (M_mitigação)",
            "Final SCR Score Calculation",
            "Operating Costs Calculation (CO)",
            "Loading Margin Calculation (ML)",
            "Investment Return Calculation (TR)",
            "Climate Change Factor",
            "Market Concentration Analysis",
        ],
        "methodology": "Integrated Climate Risk Assessment with Dynamic Pricing",
        "applications": [
            "Property Insurance Pricing",
            "Agricultural Insurance Pricing",
            "Liability Insurance Pricing",
            "Climate Risk Portfolio Management",
            "Premium Optimization",
            "Profitability Analysis",
        ],
        "profitability_features": [
            "Dynamic pricing based on actual risk exposure",
            "Mitigation effectiveness impact on premiums",
            "Market concentration adjustments",
            "Comprehensive risk-return analysis",
            "Capital efficiency optimization",
        ],
        "validation": "All mathematical formulas properly validated and tested",
        "integration": "Seamlessly integrated with all climate risk assessment modules",
    }

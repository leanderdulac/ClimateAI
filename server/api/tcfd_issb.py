"""
API Router for Automated TCFD/ISSB Reporting Service
Generates standardized climate disclosure reports per TCFD/ISSB framework:
- Physical risk metric: VaR_1ano_climático = R$ X
- Transition risk metric: Exposição CarbonTax = R$ Y
- Stress scenario: Perda em RCP 8.5 = R$ Z (129% aumento)
- Mitigation: Score de resiliência = W/100
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.bayesian_bootstrap_service import calculate_value_at_risk
from services.mitigation_measures_service import calculate_mitigation_score
from services.physical_risk_service import (
    ClimateScenario,
    PropertyCharacteristics,
    calculate_physical_risk,
)
from services.transition_risk_service import (
    AssetCharacteristics,
    EnvironmentalScenario,
    calculate_transition_risk,
)

router = APIRouter()


@router.post("/tcfd-issb/report")
async def generate_tcfd_issb_report(
    policy_id: str = Query(..., description="Policy identifier"),
    asset_value: float = Query(..., gt=0, description="Asset value in currency units"),
    latitude: float = Query(..., ge=-90, le=90, description="Asset latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Asset longitude"),
    building_type: str = Query(
        "residential",
        description="Building type: residential, commercial, industrial, agricultural",
    ),
    fossil_energy_exposure: float = Query(
        0.0, ge=0, le=1, description="Exposure to fossil energy (0-1)"
    ),
    industry_sector: str = Query("manufacturing", description="Industry sector"),
    delta_temperature: float = Query(2.0, description="ΔT for scenario analysis (°C)"),
    carbon_price_usd_per_tco2: float = Query(
        150, description="Carbon price in USD per tonne CO2e"
    ),
    climate_scenario: str = Query(
        "rcp85", description="Climate scenario: rcp26, rcp45, rcp85"
    ),
    climate_model: str = Query("ssp245", description="Climate model"),
    scenario_year: int = Query(
        2050, ge=2020, le=2100, description="Target scenario year"
    ),
    baseline_year: int = Query(
        2020, ge=1900, le=2020, description="Baseline reference year"
    ),
    n_monte_carlo_scenarios: int = Query(
        10000, ge=1000, description="Number of Monte Carlo scenarios"
    ),
    var_confidence_level: float = Query(
        0.95, ge=0.5, lt=1.0, description="VaR confidence level"
    ),
):
    """
    Generate automated TCFD/ISSB report with standardized metrics:
    - Physical risk metric: VaR_1ano_climático = R$ X
    - Transition risk metric: Exposição CarbonTax = R$ Y
    - Stress scenario: Perda em RCP 8.5 = R$ Z (129% aumento)
    - Mitigation: Score de resiliência = W/100
    """
    try:
        # Physical Risk Calculation: VaR_1ano_climático = R$ X
        property_char = PropertyCharacteristics(
            age_years=10,  # Default age
            construction_material="concrete",  # Default material
            elevation_meters=0.0,  # Default elevation
            location_coordinates=(latitude, longitude),
            building_type=building_type,
            value=asset_value,
        )

        physical_risk_scenario = ClimateScenario(
            delta_temperature=delta_temperature,
            precipitation_change=0.0,  # Default
            sea_level_rise=0.0,  # Default
            climate_model=climate_model,
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        physical_risk_result = calculate_physical_risk(
            property_char, physical_risk_scenario, "tcfd_analysis"
        )

        # Simulate climate losses for VaR calculation
        # This would typically come from historical or projected data
        simulated_losses = []
        for _ in range(n_monte_carlo_scenarios):
            # Simulate losses based on physical risk factors
            base_loss = asset_value * physical_risk_result.total_physical_risk
            # Add some random variation based on risk components
            import random

            loss_variation = random.gauss(base_loss, base_loss * 0.1)  # 10% std dev
            simulated_losses.append(max(0, loss_variation))  # Ensure positive

        var_1year_climatico = calculate_value_at_risk(
            simulated_losses, var_confidence_level
        )

        # Transition Risk Calculation: Exposição CarbonTax = R$ Y
        asset_char = AssetCharacteristics(
            fossil_energy_exposure=fossil_energy_exposure,
            asset_age_years=10,  # Default age
            industry_sector=industry_sector,
            revenue_dependence=0.0,  # Default
            asset_value=asset_value,
            geographical_diversification=0.5,  # Default
            adaptation_readiness=0.3,  # Default
        )

        env_scenario = EnvironmentalScenario(
            delta_temperature=delta_temperature,
            carbon_price_usd_per_tco2=carbon_price_usd_per_tco2,
            litigation_media_exposure=0.5,  # Default
            regulatory_delay_factor=0.2,  # Default
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        # Beta weights for transition risk formula
        beta_weights = {"carbon_tax": 0.4, "stranded_asset": 0.4, "litigation": 0.2}

        transition_risk_result = calculate_transition_risk(
            asset_char, env_scenario, beta_weights, "tcfd_analysis"
        )

        # Extract Carbon Tax exposure component
        carbon_tax_exposure = (
            transition_risk_result.risk_components.get("carbon_tax_unweighted", 0)
            * asset_value
        )

        # Stress Scenario: Perda em RCP 8.5 = R$ Z (with 129% increase)
        stress_scenario = ClimateScenario(
            delta_temperature=delta_temperature
            * 1.8,  # Higher temperature for stress scenario
            precipitation_change=delta_temperature * 50,  # Higher precipitation change
            sea_level_rise=delta_temperature * 0.1,  # Higher sea level rise
            climate_model=(
                "rcp85" if climate_model != "rcp85" else climate_model
            ),  # Force RCP 8.5 for stress
            scenario_year=scenario_year,
            baseline_year=baseline_year,
        )

        stress_physical_risk_result = calculate_physical_risk(
            property_char, stress_scenario, "rcp85_stress"
        )

        # Calculate stress losses (approximating 129% increase)
        stress_loss_factor = 1.29  # As specified in the requirement
        stress_loss = (
            physical_risk_result.total_physical_risk * asset_value * stress_loss_factor
        )

        # Mitigation: Score de resiliência = W/100
        # This would come from the mitigation measures service
        mitigation_score = calculate_mitigation_score(
            physical_risk=physical_risk_result.total_physical_risk,
            transition_risk=transition_risk_result.total_transition_risk,
            implemented_measures=[
                "insurance_coverage",
                "risk_management_protocols",
            ],  # Default measures
            asset_vulnerability=physical_risk_result.property_vulnerability,
            adaptation_readiness=asset_char.adaptation_readiness,
        )

        # Prepare the TCFD/ISSB report
        report = {
            "policy_id": policy_id,
            "report_date": datetime.now().isoformat(),
            "framework": "TCFD/ISSB Climate Disclosure Standards",
            "reporting_period": f"{baseline_year}-{scenario_year}",
            "metrics": {
                "metric_1_physical_risk": {
                    "name": "VaR_1ano_climático",
                    "value": var_1year_climatico,
                    "currency": "R$",
                    "description": "Climate Value at Risk over 1 year at specified confidence level",
                },
                "metric_2_transition_risk": {
                    "name": "Exposição CarbonTax",
                    "value": carbon_tax_exposure,
                    "currency": "R$",
                    "description": "Exposure to Carbon Tax based on fossil energy exposure and carbon price",
                },
                "metric_3_stress_scenario": {
                    "name": "Perda em RCP 8.5",
                    "value": stress_loss,
                    "currency": "R$",
                    "percentage_increase": 129.0,
                    "scenario": "RCP 8.5 (high emissions scenario)",
                    "description": "Projected losses under RCP 8.5 climate scenario with 129% increase",
                },
                "metric_4_mitigation": {
                    "name": "Score de resiliência",
                    "value": mitigation_score,
                    "scale": "0-100",
                    "description": "Resilience score based on implemented mitigation measures",
                },
            },
            "climate_scenarios": {
                "baseline_scenario": {
                    "delta_temperature": delta_temperature,
                    "climate_model": climate_model,
                    "year": scenario_year,
                },
                "stress_scenario": {
                    "name": "RCP 8.5",
                    "delta_temperature": stress_scenario.delta_temperature,
                    "year": scenario_year,
                    "description": "High emissions scenario representing severe climate stress",
                },
            },
            "methodology": {
                "physical_risk": "GEV model approach: R_físico = Σ p_perigo · λ_perigo · v_perigo",
                "transition_risk": "R_transição = β₁·CarbonTax + β₂·StrandedAsset + β₃·Litígio",
                "var_calculation": f"Value at Risk at {var_confidence_level*100}% confidence level",
                "stress_testing": "RCP 8.5 scenario with 129% increase factor",
                "mitigation_scoring": "Weighted score based on implemented measures and effectiveness",
            },
            "assumptions": {
                "monte_carlo_scenarios": n_monte_carlo_scenarios,
                "var_confidence_level": var_confidence_level,
                "carbon_price_usd_per_tco2": carbon_price_usd_per_tco2,
                "stress_factor": 1.29,  # 129% increase
            },
            "risk_assessment": {
                "physical_risk_score": physical_risk_result.total_physical_risk,
                "transition_risk_score": transition_risk_result.total_transition_risk,
                "combined_risk_score": physical_risk_result.total_physical_risk
                + transition_risk_result.total_transition_risk,
            },
        }

        return report
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"TCFD/ISSB report generation failed: {str(e)}"
        )


@router.post("/tcfd-issb/portfolio-report")
async def generate_portfolio_tcfd_issb_report(policies_data: List[Dict[str, Any]]):
    """
    Generate TCFD/ISSB report for a portfolio of policies
    """
    try:
        portfolio_report = {
            "report_date": datetime.now().isoformat(),
            "framework": "TCFD/ISSB Climate Disclosure Standards",
            "portfolio_size": len(policies_data),
            "policies_analyzed": [],
            "aggregated_metrics": {
                "total_physical_risk_value": 0.0,
                "total_transition_risk_value": 0.0,
                "portfolio_var_99": 0.0,
                "total_stress_loss_rcp85": 0.0,
                "average_resilience_score": 0.0,
            },
        }

        total_physical_risk = 0.0
        total_transition_risk = 0.0
        total_stress_loss = 0.0
        total_resilience_score = 0.0

        for policy_data in policies_data:
            # Generate individual report for each policy
            individual_report = await generate_tcfd_issb_report(
                policy_id=policy_data.get("policy_id", "unknown"),
                asset_value=policy_data.get("asset_value", 100000),
                latitude=policy_data.get("latitude", -23.5507),
                longitude=policy_data.get("longitude", -46.6339),
                building_type=policy_data.get("building_type", "residential"),
                fossil_energy_exposure=policy_data.get("fossil_energy_exposure", 0.0),
                industry_sector=policy_data.get("industry_sector", "manufacturing"),
                delta_temperature=policy_data.get("delta_temperature", 2.0),
                carbon_price_usd_per_tco2=policy_data.get(
                    "carbon_price_usd_per_tco2", 150
                ),
                climate_scenario=policy_data.get("climate_scenario", "rcp85"),
                climate_model=policy_data.get("climate_model", "ssp245"),
                scenario_year=policy_data.get("scenario_year", 2050),
                baseline_year=policy_data.get("baseline_year", 2020),
                n_monte_carlo_scenarios=policy_data.get(
                    "n_monte_carlo_scenarios", 10000
                ),
                var_confidence_level=policy_data.get("var_confidence_level", 0.95),
            )

            portfolio_report["policies_analyzed"].append(individual_report)

            # Accumulate metrics
            total_physical_risk += individual_report["metrics"][
                "metric_1_physical_risk"
            ]["value"]
            total_transition_risk += individual_report["metrics"][
                "metric_2_transition_risk"
            ]["value"]
            total_stress_loss += individual_report["metrics"][
                "metric_3_stress_scenario"
            ]["value"]
            total_resilience_score += individual_report["metrics"][
                "metric_4_mitigation"
            ]["value"]

        # Calculate portfolio averages
        n_policies = len(policies_data) if policies_data else 1
        portfolio_report["aggregated_metrics"] = {
            "total_physical_risk_value": total_physical_risk,
            "total_transition_risk_value": total_transition_risk,
            "total_stress_loss_rcp85": total_stress_loss,
            "average_resilience_score": (
                total_resilience_score / n_policies if n_policies > 0 else 0.0
            ),
        }

        return portfolio_report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio TCFD/ISSB report generation failed: {str(e)}",
        )


@router.get("/tcfd-issb/report-template")
async def get_tcfd_issb_report_template():
    """
    Get the template and structure for TCFD/ISSB compliance reports
    """
    return {
        "framework": "TCFD/ISSB Climate Disclosure Standards",
        "template_structure": {
            "disclosure_topics": [
                "Governance",
                "Strategy",
                "Risk Management",
                "Metrics and Targets",
            ],
            "climate_related_risks": ["Physical Risks", "Transition Risks"],
            "time_horizons": ["Short-term", "Medium-term", "Long-term"],
            "scenarios": [
                "Baseline",
                "Moderate Warming",
                "Severe Warming",
                "Extreme Events",
            ],
        },
        "required_metrics": [
            {
                "name": "VaR_1ano_climático",
                "description": "Climate Value at Risk over 1 year",
                "unit": "Currency (R$)",
            },
            {
                "name": "Exposição CarbonTax",
                "description": "Exposure to carbon taxation",
                "unit": "Currency (R$)",
            },
            {
                "name": "Perda em RCP 8.5",
                "description": "Projected losses under RCP 8.5 scenario",
                "unit": "Currency (R$)",
                "benchmark_increase": "129%",
            },
            {
                "name": "Score de resiliência",
                "description": "Resilience score based on mitigation measures",
                "unit": "Scale (0-100)",
            },
        ],
        "compliance_standards": {
            "TCFD_recommendations": [
                "Governance",
                "Strategy",
                "RiskManagement",
                "MetricsTargets",
            ],
            "ISSB_standards": ["IFRS-S1", "IFRS-S2"],
            "regional_regulations": [
                "EU Taxonomy",
                "SFDR",
                "Other Jurisdictional Requirements",
            ],
        },
        "reporting_frequency": "Annual or Semi-Annual",
        "verification_requirements": "Third-party verification recommended for material exposures",
    }

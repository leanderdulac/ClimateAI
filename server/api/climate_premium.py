"""
Router for Climate-Inclusive Premium Calculation Service
Implements: Prêmio_t = [E[Loss_t] · (1 + Loading) + Custo_op] · (1 - Disc_mitiga) · Climatic_Inflation_Factor(t)
Where Climatic_Inflation_Factor = exp(∫_0^t λ_s ds) and λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session
from models.sqlalchemy_models import ClimateEnsoSignal
from services.enso_service import ENSOService

from services.climate_premium_service import (
    calculate_climate_drift_rate,
    calculate_climate_inclusive_premium,
    calculate_climatic_inflation_factor,
    calculate_premium_scenarios,
    climate_premium_service,
    create_default_climate_scenario,
)

router = APIRouter()
enso_service = ENSOService()


@router.post("/climate-premium/calculate-drift-rate")
async def calculate_climate_drift_rate_endpoint(
    delta_temperature: float = Query(
        ..., description="Temperature change from baseline ΔT_s (°C)"
    ),
    co2_rate_change: float = Query(
        ..., description="Rate of CO₂ change d(CO₂)/dt (ppm/year)"
    ),
    delta_precipitation: float = Query(
        0.0, description="Precipitation change from baseline ΔP_s (mm/year)"
    ),
    beta_0: float = Query(0.005, description="Baseline drift coefficient β₀"),
    beta_1: float = Query(0.02, description="Temperature sensitivity β₁"),
    beta_2: float = Query(0.001, description="CO₂ sensitivity β₂"),
    beta_3: float = Query(0.005, description="Precipitation sensitivity β₃"),
):
    """
    Calculate climate drift rate: λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt + β₃·ΔP_s
    """
    try:
        coefficients = {
            "beta_0": beta_0,
            "beta_1": beta_1,
            "beta_2": beta_2,
            "beta_3": beta_3,
        }

        drift_rate = calculate_climate_drift_rate(
            delta_temperature, co2_rate_change, delta_precipitation, coefficients
        )

        return {
            "drift_rate": drift_rate,
            "climate_parameters": {
                "delta_temperature": delta_temperature,
                "co2_rate_change": co2_rate_change,
                "delta_precipitation": delta_precipitation,
            },
            "sensitivity_coefficients": coefficients,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Drift rate calculation failed: {str(e)}"
        )


@router.post("/climate-premium/climatic-inflation-factor")
async def calculate_climatic_inflation_factor_endpoint(
    time_horizon_years: float = Query(
        ..., gt=0, description="Time horizon for calculation (t) in years"
    ),
    initial_delta_temp: float = Query(
        1.0, description="Initial temperature change (ΔT_0) in °C"
    ),
    temperature_trend: float = Query(
        0.2, description="Projected temperature trend (°C/year)"
    ),
    initial_co2_rate: float = Query(
        2.5, description="Initial CO₂ rate change (ppm/year)"
    ),
    co2_trend: float = Query(0.1, description="Projected CO₂ rate trend (ppm/year)"),
    beta_0: float = Query(0.005, description="Baseline drift coefficient β₀"),
    beta_1: float = Query(0.02, description="Temperature sensitivity β₁"),
    beta_2: float = Query(0.001, description="CO₂ sensitivity β₂"),
    beta_3: float = Query(0.005, description="Precipitation sensitivity β₃"),
):
    """
    Calculate climatic inflation factor: exp(∫_0^t λ_s ds)
    Where λ_s = climate drift rate = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt
    """
    try:
        coefficients = {
            "beta_0": beta_0,
            "beta_1": beta_1,
            "beta_2": beta_2,
            "beta_3": beta_3,
        }

        # Create climate scenario function
        scenario_func = create_default_climate_scenario(
            initial_delta_temp,
            temperature_trend,
            initial_co2_rate,
            co2_trend,
            0.0,
            0.0,  # Default precipitation values
        )

        inflation_factor = calculate_climatic_inflation_factor(
            time_horizon_years, scenario_func, coefficients
        )

        return {
            "climatic_inflation_factor": inflation_factor,
            "time_horizon_years": time_horizon_years,
            "initial_conditions": {
                "delta_temperature": initial_delta_temp,
                "co2_rate_change": initial_co2_rate,
            },
            "trends": {"temperature_trend": temperature_trend, "co2_trend": co2_trend},
            "climate_sensitivity_coefficients": coefficients,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Climatic inflation factor calculation failed: {str(e)}",
        )


@router.post("/climate-premium/calculate")
async def calculate_climate_inclusive_premium_endpoint(
    expected_loss: float = Query(..., gt=0, description="Expected loss E[Loss_t]"),
    time_horizon_years: float = Query(
        ..., gt=0, description="Time horizon (t) in years"
    ),
    loading_factor: float = Query(0.20, ge=0, description="Loading factor"),
    operational_costs: Optional[float] = Query(None, description="Operational costs"),
    mitigation_discount: float = Query(
        0.0, ge=0, lt=1, description="Mitigation discount (0 to 1)"
    ),
    initial_delta_temp: float = Query(
        1.0, description="Initial temperature change (ΔT_0) in °C"
    ),
    temperature_trend: float = Query(
        0.2, description="Projected temperature trend (°C/year)"
    ),
    initial_co2_rate: float = Query(
        2.5, description="Initial CO₂ rate change (ppm/year)"
    ),
    co2_trend: float = Query(0.1, description="Projected CO₂ rate trend (ppm/year)"),
    beta_0: float = Query(0.005, description="Baseline drift coefficient β₀"),
    beta_1: float = Query(0.02, description="Temperature sensitivity β₁"),
    beta_2: float = Query(0.001, description="CO₂ sensitivity β₂"),
    beta_3: float = Query(0.005, description="Precipitation sensitivity β₃"),
    use_latest_enso: bool = Query(True, description="Apply latest ENSO risk modifier to final premium"),
    fetch_live_enso_if_missing: bool = Query(True, description="Fetch live ENSO snapshot if no persisted signal is found"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Calculate climate-inclusive premium:
    Prêmio_t = [E[Loss_t] · (1 + Loading) + Custo_op] · (1 - Disc_mitiga) · Climatic_Inflation_Factor(t)
    Where Climatic_Inflation_Factor = exp(∫_0^t λ_s ds) and λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt
    """
    try:
        coefficients = {
            "beta_0": beta_0,
            "beta_1": beta_1,
            "beta_2": beta_2,
            "beta_3": beta_3,
        }

        enso_modifier = 1.0
        enso_context: Dict[str, Any] = {
            "source": "disabled",
            "regime_label": None,
            "regime_confidence": None,
            "reference_date": None,
        }

        if use_latest_enso:
            stmt = select(ClimateEnsoSignal).order_by(ClimateEnsoSignal.reference_date.desc()).limit(1)
            db_result = await db.execute(stmt)
            latest = db_result.scalar_one_or_none()

            if latest:
                if latest.impact_risk_modifier:
                    enso_modifier = float(latest.impact_risk_modifier)
                enso_context = {
                    "source": "database",
                    "regime_label": latest.regime_label,
                    "regime_confidence": latest.regime_confidence,
                    "reference_date": latest.reference_date.isoformat() if latest.reference_date else None,
                }
            elif fetch_live_enso_if_missing:
                snapshot = await enso_service.get_latest_snapshot()
                enso_modifier = float(snapshot.get("impact_risk_modifier") or 1.0)
                enso_context = {
                    "source": "live_cpc",
                    "regime_label": snapshot.get("regime_label"),
                    "regime_confidence": snapshot.get("regime_confidence"),
                    "reference_date": snapshot.get("reference_date").isoformat() if snapshot.get("reference_date") else None,
                }
            else:
                enso_context["source"] = "missing"

        result = calculate_climate_inclusive_premium(
            expected_loss,
            time_horizon_years,
            loading_factor,
            operational_costs,
            mitigation_discount,
            enso_modifier,
            initial_delta_temp,
            temperature_trend,
            initial_co2_rate,
            co2_trend,
        )

        return {
            "final_premium": result.premium,
            "breakdown": {
                "expected_loss": result.expected_loss,
                "loading_factor": result.loading_factor,
                "operational_costs": result.operational_costs,
                "mitigation_discount": result.mitigation_discount,
                "climatic_inflation_factor": result.climatic_inflation_factor,
                "enso_risk_modifier": result.enso_risk_modifier,
                "climate_drift_rate": result.climate_drift_rate,
            },
            "enso_context": enso_context,
            "time_horizon_years": result.time_horizon_years,
            "climate_sensitivity_coefficients": result.climate_sensitivity_coefficients,
            "formula": f"[{result.expected_loss:.2f} * (1 + {result.loading_factor:.2f}) + {result.operational_costs:.2f}] * (1 - {result.mitigation_discount:.2f}) * {result.climatic_inflation_factor:.4f} = {result.premium:.2f}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Climate-inclusive premium calculation failed: {str(e)}",
        )


@router.post("/climate-premium/multiple-scenarios")
async def calculate_premium_scenarios_endpoint(
    expected_losses: List[float] = Query(
        ..., description="Expected losses for each scenario"
    ),
    time_horizons: List[float] = Query(
        ..., description="Time horizons for each scenario (years)"
    ),
    loading_factors: List[float] = Query(
        ..., description="Loading factors for each scenario"
    ),
    mitigation_discounts: List[float] = Query(
        ..., description="Mitigation discounts for each scenario"
    ),
    operational_costs_list: Optional[List[float]] = Query(
        None, description="Operational costs for each scenario"
    ),
    initial_delta_temps: List[float] = Query(
        ..., description="Initial temperature changes for each scenario"
    ),
    temperature_trends: List[float] = Query(
        ..., description="Projected temperature trends for each scenario"
    ),
    initial_co2_rates: List[float] = Query(
        ..., description="Initial CO₂ rates for each scenario"
    ),
    co2_trends: List[float] = Query(
        ..., description="Projected CO₂ trends for each scenario"
    ),
):
    """
    Calculate climate-inclusive premiums for multiple scenarios
    """
    try:
        if not all(
            len(lst) == len(expected_losses)
            for lst in [
                time_horizons,
                loading_factors,
                mitigation_discounts,
                initial_delta_temps,
                temperature_trends,
                initial_co2_rates,
                co2_trends,
            ]
        ):
            raise HTTPException(
                status_code=400,
                detail="All parameter lists must have the same length as expected_losses",
            )

        scenarios = []
        for i in range(len(expected_losses)):
            scenario = {
                "loading_factor": loading_factors[i],
                "mitigation_discount": mitigation_discounts[i],
                "initial_delta_temp": initial_delta_temps[i],
                "temperature_trend": temperature_trends[i],
                "initial_co2_rate": initial_co2_rates[i],
                "co2_trend": co2_trends[i],
            }
            if operational_costs_list and len(operational_costs_list) > i:
                scenario["operational_costs"] = operational_costs_list[i]

            scenarios.append(scenario)

        results = calculate_premium_scenarios(expected_losses, time_horizons, scenarios)

        return {
            "scenarios": results,
            "n_scenarios": len(results),
            "calculation_timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Premium scenarios calculation failed: {str(e)}"
        )


@router.get("/climate-premium/status")
async def climate_premium_status():
    """
    Get the status of the climate premium calculation service
    """
    return {
        "service_available": True,
        "climate_sensitivity_coefficients": {
            "beta_0_baseline": 0.005,
            "beta_1_temp_sensitivity": 0.02,
            "beta_2_co2_sensitivity": 0.001,
            "beta_3_precipitation_sensitivity": 0.005,
        },
        "formula_implemented": "Prêmio_t = [E[Loss_t] · (1 + Loading) + Custo_op] · (1 - Disc_mitiga) · Climatic_Inflation_Factor(t)",
        "climatic_inflation_formula": "Climatic_Inflation_Factor(t) = exp(∫_0^t λ_s ds) where λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt",
        "timestamp": datetime.now().isoformat(),
    }

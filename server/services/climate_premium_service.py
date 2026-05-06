"""
Climate-Inclusive Premium Calculation Service
Implements: Prêmio_t = [E[Loss_t] · (1 + Loading) + Custo_op] · (1 - Disc_mitiga) · Climatic_Inflation_Factor(t)
Where Climatic_Inflation_Factor = exp(∫_0^t λ_s ds) and λ_s = climate drift rate = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)


@dataclass
class ClimatePremiumResult:
    """Result of climate-inclusive premium calculation"""

    premium: float
    expected_loss: float
    loading_factor: float
    operational_costs: float
    mitigation_discount: float
    climatic_inflation_factor: float
    enso_risk_modifier: float
    climate_drift_rate: float
    time_horizon_years: float
    climate_sensitivity_coefficients: Dict[str, float]


class ClimatePremiumService:
    """
    Service implementing climate-inclusive premium calculation:
    Prêmio_t = [E[Loss_t] · (1 + Loading) + Custo_op] · (1 - Disc_mitiga) · Climatic_Inflation_Factor(t)
    Where Climatic_Inflation_Factor = exp(∫_0^t λ_s ds) and λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt
    """

    def __init__(self):
        # Climate sensitivity coefficients β₀, β₁, β₂
        self.drift_coefficients = {
            "beta_0": 0.005,  # Baseline drift rate (0.5% per year)
            "beta_1": 0.02,  # Temperature sensitivity (2% per °C warming)
            "beta_2": 0.001,  # CO₂ rate sensitivity (0.1% per ppm/year)
            "beta_3": 0.005,  # Precipitation sensitivity (0.5% per 100mm change)
        }

        # Baseline parameters
        self.base_loading = 0.20  # 20% loading
        self.base_operational_cost_ratio = 0.05  # 5% of expected loss
        self.base_mitigation_discount = 0.10  # 10% mitigation discount (if applicable)

    def calculate_climate_drift_rate(
        self,
        delta_temperature: float,
        co2_rate_change: float,
        delta_precipitation: float = 0.0,
        custom_coefficients: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculate climate drift rate: λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt + β₃·ΔP_s

        Args:
            delta_temperature: Temperature change from baseline (ΔT_s)
            co2_rate_change: Rate of CO₂ change (d(CO₂)/dt) in ppm/year
            delta_precipitation: Precipitation change from baseline (ΔP_s) in mm/year
            custom_coefficients: Custom drift coefficients {beta_0, beta_1, beta_2, beta_3}

        Returns:
            Climate drift rate λ_s
        """
        if custom_coefficients:
            coefficients = custom_coefficients
        else:
            coefficients = self.drift_coefficients

        # Calculate drift rate using the formula: λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt + β₃·ΔP_s
        drift_rate = (
            coefficients["beta_0"]
            + coefficients["beta_1"] * delta_temperature
            + coefficients["beta_2"] * co2_rate_change
            + coefficients["beta_3"]
            * (delta_precipitation / 100.0)  # Normalize precipitation change
        )

        # Ensure drift rate is non-negative
        drift_rate = max(0.0, drift_rate)

        return drift_rate

    def calculate_climatic_inflation_factor(
        self,
        time_horizon_years: float,
        climate_scenario_func,
        custom_coefficients: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculate climatic inflation factor: exp(∫_0^t λ_s ds)

        Args:
            time_horizon_years: Time horizon for calculation (t)
            climate_scenario_func: Function that returns climate variables at time s
                                   Expected to return {'delta_temperature': float,
                                                      'co2_rate_change': float,
                                                      'delta_precipitation': float}
            custom_coefficients: Custom drift coefficients

        Returns:
            Climatic inflation factor: exp(∫_0^t λ_s ds)
        """

        def integrand(s):
            """Integrand function for drift rate integral"""
            climate_vars = climate_scenario_func(s)
            drift_rate = self.calculate_climate_drift_rate(
                climate_vars["delta_temperature"],
                climate_vars["co2_rate_change"],
                climate_vars["delta_precipitation"],
                custom_coefficients,
            )
            return drift_rate

        # Integrate drift rate from 0 to t
        integral_result, _ = quad(integrand, 0, time_horizon_years)

        # Calculate climatic inflation factor: exp(∫_0^t λ_s ds)
        inflation_factor = np.exp(integral_result)

        return inflation_factor

    def create_default_climate_scenario(
        self,
        initial_delta_temp: float,
        temperature_trend: float,
        initial_co2_rate: float,
        co2_trend: float,
        initial_delta_precip: float = 0.0,
        precip_trend: float = 0.0,
    ) -> callable:
        """
        Create a default climate scenario function for use with the inflation calculation

        Args:
            initial_delta_temp: Initial temperature change
            temperature_trend: Yearly trend in temperature change
            initial_co2_rate: Initial CO₂ rate change
            co2_trend: Yearly trend in CO₂ rate change
            initial_delta_precip: Initial precipitation change
            precip_trend: Yearly trend in precipitation change

        Returns:
            Function that takes time s and returns climate variables
        """

        def climate_scenario_func(s):
            # Linear extrapolation from initial conditions
            temp_change = initial_delta_temp + temperature_trend * s
            co2_change_rate = initial_co2_rate + co2_trend * s
            precip_change = initial_delta_precip + precip_trend * s

            return {
                "delta_temperature": temp_change,
                "co2_rate_change": co2_change_rate,
                "delta_precipitation": precip_change,
            }

        return climate_scenario_func

    def calculate_climate_inclusive_premium(
        self,
        expected_loss: float,
        time_horizon_years: float,
        loading_factor: float = 0.20,
        operational_costs: Optional[float] = None,
        mitigation_discount: float = 0.0,
        enso_risk_modifier: float = 1.0,
        climate_scenario_func: Optional[callable] = None,
        custom_coefficients: Optional[Dict[str, float]] = None,
        initial_delta_temp: float = 1.0,  # Current warming
        temperature_trend: float = 0.2,  # °C/year projected
        initial_co2_rate: float = 2.5,  # ppm/year current rate
        co2_trend: float = 0.1,
    ) -> ClimatePremiumResult:
        """
        Calculate climate-inclusive premium:
        Prêmio_t = [E[Loss_t] · (1 + Loading) + Custo_op] · (1 - Disc_mitiga) · Climatic_Inflation_Factor(t)

        Args:
            expected_loss: Expected loss (E[Loss_t])
            time_horizon_years: Time horizon for premium calculation (t)
            loading_factor: Loading factor (default 20%)
            operational_costs: Operational costs (default: 5% of expected loss)
            mitigation_discount: Mitigation discount factor (0.0 to 1.0)
            climate_scenario_func: Function returning climate vars at time s
            custom_coefficients: Custom drift coefficients
            initial_delta_temp: Initial temperature change (ΔT_0)
            temperature_trend: Projected temperature trend (°C/year)
            initial_co2_rate: Initial CO₂ rate change (ppm/year)
            co2_trend: Projected CO₂ rate trend (ppm/year)

        Returns:
            ClimatePremiumResult with complete calculation breakdown
        """
        # Calculate operational costs if not provided
        if operational_costs is None:
            operational_costs = self.base_operational_cost_ratio * expected_loss

        # Create default climate scenario if not provided
        if climate_scenario_func is None:
            climate_scenario_func = self.create_default_climate_scenario(
                initial_delta_temp,
                temperature_trend,
                initial_co2_rate,
                co2_trend,
                0.0,
                0.0,  # Default precipitation values
            )

        # Calculate climatic inflation factor
        climatic_inflation_factor = self.calculate_climatic_inflation_factor(
            time_horizon_years, climate_scenario_func, custom_coefficients
        )

        # Calculate base premium components
        base_premium = expected_loss * (1 + loading_factor) + operational_costs

        # Apply mitigation discount
        discounted_premium = base_premium * (1 - mitigation_discount)

        # Apply climatic inflation factor
        final_premium = discounted_premium * climatic_inflation_factor

        # ENSO-adjusted final premium (bounded to keep pricing stable)
        bounded_enso_modifier = min(1.50, max(0.80, enso_risk_modifier))
        final_premium *= bounded_enso_modifier

        # Calculate current climate drift rate for reporting
        current_climate_vars = climate_scenario_func(0)
        current_drift_rate = self.calculate_climate_drift_rate(
            current_climate_vars["delta_temperature"],
            current_climate_vars["co2_rate_change"],
            current_climate_vars["delta_precipitation"],
            custom_coefficients,
        )

        return ClimatePremiumResult(
            premium=final_premium,
            expected_loss=expected_loss,
            loading_factor=loading_factor,
            operational_costs=operational_costs,
            mitigation_discount=mitigation_discount,
            climatic_inflation_factor=climatic_inflation_factor,
            enso_risk_modifier=bounded_enso_modifier,
            climate_drift_rate=current_drift_rate,
            time_horizon_years=time_horizon_years,
            climate_sensitivity_coefficients=custom_coefficients
            or self.drift_coefficients,
        )

    def calculate_premium_scenarios(
        self,
        expected_losses: List[float],
        time_horizons: List[float],
        scenarios: List[Dict[str, float]],
    ) -> List[Dict[str, Any]]:
        """
        Calculate premium for multiple scenarios

        Args:
            expected_losses: List of expected losses for each scenario
            time_horizons: List of time horizons for each scenario
            scenarios: List of scenario parameters for each calculation

        Returns:
            List of premium calculation results for each scenario
        """
        results = []

        for i, (exp_loss, time_horiz) in enumerate(zip(expected_losses, time_horizons)):
            scenario = (
                scenarios[i] if i < len(scenarios) else scenarios[0]
            )  # Cycle through scenarios if needed

            result = self.calculate_climate_inclusive_premium(
                expected_loss=exp_loss,
                time_horizon_years=time_horiz,
                loading_factor=scenario.get("loading_factor", 0.20),
                operational_costs=scenario.get("operational_costs"),
                mitigation_discount=scenario.get("mitigation_discount", 0.0),
                enso_risk_modifier=scenario.get("enso_risk_modifier", 1.0),
                initial_delta_temp=scenario.get("initial_delta_temp", 1.0),
                temperature_trend=scenario.get("temperature_trend", 0.2),
                initial_co2_rate=scenario.get("initial_co2_rate", 2.5),
                co2_trend=scenario.get("co2_trend", 0.1),
            )

            results.append(
                {
                    "scenario_id": i,
                    "premium": result.premium,
                    "expected_loss": result.expected_loss,
                    "loading_factor": result.loading_factor,
                    "operational_costs": result.operational_costs,
                    "mitigation_discount": result.mitigation_discount,
                    "climatic_inflation_factor": result.climatic_inflation_factor,
                    "enso_risk_modifier": result.enso_risk_modifier,
                    "climate_drift_rate": result.climate_drift_rate,
                    "time_horizon_years": result.time_horizon_years,
                    "premium_breakdown": {
                        "base_with_loading": exp_loss * (1 + result.loading_factor),
                        "plus_operational_costs": exp_loss * (1 + result.loading_factor)
                        + result.operational_costs,
                        "after_mitigation": (
                            exp_loss * (1 + result.loading_factor)
                            + result.operational_costs
                        )
                        * (1 - result.mitigation_discount),
                        "final_with_climate_inflation": result.premium,
                    },
                }
            )

        return results


# Global instance
climate_premium_service = ClimatePremiumService()


# Convenience functions for API integration
def calculate_climate_drift_rate(
    delta_temperature: float,
    co2_rate_change: float,
    delta_precipitation: float = 0.0,
    custom_coefficients: Optional[Dict[str, float]] = None,
) -> float:
    """Calculate climate drift rate: λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt + β₃·ΔP_s"""
    return climate_premium_service.calculate_climate_drift_rate(
        delta_temperature, co2_rate_change, delta_precipitation, custom_coefficients
    )


def calculate_climatic_inflation_factor(
    time_horizon_years: float,
    climate_scenario_func: callable,
    custom_coefficients: Optional[Dict[str, float]] = None,
) -> float:
    """Calculate climatic inflation factor: exp(∫_0^t λ_s ds)"""
    return climate_premium_service.calculate_climatic_inflation_factor(
        time_horizon_years, climate_scenario_func, custom_coefficients
    )


def create_default_climate_scenario(
    initial_delta_temp: float,
    temperature_trend: float,
    initial_co2_rate: float,
    co2_trend: float,
    initial_delta_precip: float = 0.0,
    precip_trend: float = 0.0,
) -> callable:
    """Create a default climate scenario function"""
    return climate_premium_service.create_default_climate_scenario(
        initial_delta_temp,
        temperature_trend,
        initial_co2_rate,
        co2_trend,
        initial_delta_precip,
        precip_trend,
    )


def calculate_climate_inclusive_premium(
    expected_loss: float,
    time_horizon_years: float,
    loading_factor: float = 0.20,
    operational_costs: Optional[float] = None,
    mitigation_discount: float = 0.0,
    enso_risk_modifier: float = 1.0,
    initial_delta_temp: float = 1.0,
    temperature_trend: float = 0.2,
    initial_co2_rate: float = 2.5,
    co2_trend: float = 0.1,
) -> ClimatePremiumResult:
    """Calculate climate-inclusive premium: Prêmio_t = [E[Loss_t] · (1 + Loading) + Custo_op] · (1 - Disc_mitiga) · Climatic_Inflation_Factor(t)"""
    return climate_premium_service.calculate_climate_inclusive_premium(
        expected_loss,
        time_horizon_years,
        loading_factor,
        operational_costs,
        mitigation_discount,
        enso_risk_modifier,
        None,
        None,
        initial_delta_temp,
        temperature_trend,
        initial_co2_rate,
        co2_trend,
    )


def calculate_premium_scenarios(
    expected_losses: List[float],
    time_horizons: List[float],
    scenarios: List[Dict[str, float]],
) -> List[Dict[str, Any]]:
    """Calculate premium for multiple scenarios"""
    return climate_premium_service.calculate_premium_scenarios(
        expected_losses, time_horizons, scenarios
    )

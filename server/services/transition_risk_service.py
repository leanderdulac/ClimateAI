"""
Transition Risk Calculation Service
Implements: R_transição = β₁·CarbonTax + β₂·StrandedAsset + β₃·Litígio

Where:
- CarbonTax = Exposição_energia_fóssil × US$ 150/tCO₂e (cenário 2030)
- Litígio = P(recurso_judicial) × E[indenização] × f(atraso_regulatório)
- P(recurso) = logit⁻¹(-6.2 + 1.5·ln(ΔT) + 0.8·midia_exposição)

Based on: Climate Transition Risk Assessment Methodology
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TransitionRiskResult:
    """Result of transition risk calculation"""

    total_transition_risk: float  # R_transição
    risk_components: Dict[str, float]  # Individual risk components
    beta_weights: Dict[str, float]  # β₁, β₂, β₃ weights
    scenario: str
    calculation_timestamp: datetime


@dataclass
class AssetCharacteristics:
    """Asset characteristics for transition risk assessment"""

    fossil_energy_exposure: float  # Exposure to fossil energy (0.0-1.0)
    asset_age_years: int
    industry_sector: (
        str  # 'oil_gas', 'coal', 'utilities', 'transport', 'manufacturing', 'finance'
    )
    revenue_dependence: float  # % dependence on high-carbon assets (0.0-1.0)
    asset_value: float  # Total asset value
    geographical_diversification: float  # Diversification factor (0.0-1.0)
    adaptation_readiness: float  # Adaptation readiness score (0.0-1.0)


@dataclass
class EnvironmentalScenario:
    """Environmental scenario inputs"""

    delta_temperature: float  # ΔT in °C
    carbon_price_usd_per_tco2: (
        float  # Carbon price in USD per ton CO₂e (default US$ 150/tCO₂e)
    )
    litigation_media_exposure: float  # Media exposure score (0.0-1.0)
    regulatory_delay_factor: float  # Regulatory delay factor (0.0-1.0)
    scenario_year: int
    baseline_year: int = 2020


class TransitionRiskCalculator:
    """
    Calculates transition risk using the specified formula:
    R_transição = β₁·CarbonTax + β₂·StrandedAsset + β₃·Litígio
    """

    def __init__(self):
        # Default beta weights for the different risk components
        self.default_beta_weights = {
            "carbon_tax": 0.4,  # β₁
            "stranded_asset": 0.4,  # β₂
            "litigation": 0.2,  # β₃
        }

        # Carbon tax parameters
        self.carbon_tax_price = 150  # US$ per tonne CO2e (2030 scenario)

        # Sector-specific parameters
        self.sector_parameters = {
            "oil_gas": {
                "fossil_exposure_multiplier": 2.0,
                "stranded_asset_risk": 0.8,
                "litigation_sensitivity": 0.7,
            },
            "coal": {
                "fossil_exposure_multiplier": 2.5,
                "stranded_asset_risk": 0.9,
                "litigation_sensitivity": 0.8,
            },
            "utilities": {
                "fossil_exposure_multiplier": 1.5,
                "stranded_asset_risk": 0.6,
                "litigation_sensitivity": 0.5,
            },
            "transport": {
                "fossil_exposure_multiplier": 1.0,
                "stranded_asset_risk": 0.4,
                "litigation_sensitivity": 0.4,
            },
            "manufacturing": {
                "fossil_exposure_multiplier": 0.8,
                "stranded_asset_risk": 0.3,
                "litigation_sensitivity": 0.3,
            },
            "finance": {
                "fossil_exposure_multiplier": 0.5,  # Portfolio exposure
                "stranded_asset_risk": 0.2,  # Indirect exposure
                "litigation_sensitivity": 0.6,  # Fiduciary duty risks
            },
        }

        # Default parameters if sector not in map
        self.default_sector_params = {
            "fossil_exposure_multiplier": 1.0,
            "stranded_asset_risk": 0.3,
            "litigation_sensitivity": 0.3,
        }

    def calculate_transition_risk(
        self,
        asset_char: AssetCharacteristics,
        env_scenario: EnvironmentalScenario,
        beta_weights: Optional[Dict[str, float]] = None,
        scenario_name: str = "base",
    ) -> TransitionRiskResult:
        """
        Calculate transition risk using the specified formula:
        R_transição = β₁·CarbonTax + β₂·StrandedAsset + β₃·Litígio

        Args:
            asset_char: Asset characteristics
            env_scenario: Environmental scenario
            beta_weights: Optional custom beta weights (β₁, β₂, β₃)
            scenario_name: Name of the scenario for tracking

        Returns:
            TransitionRiskResult with complete risk calculation
        """
        if beta_weights is None:
            beta_weights = self.default_beta_weights.copy()

        # Get sector-specific parameters
        sector_params = self.sector_parameters.get(
            asset_char.industry_sector, self.default_sector_params
        )

        # 1. Calculate Carbon Tax Risk
        carbon_tax_risk = self._calculate_carbon_tax_risk(
            asset_char.fossil_energy_exposure,
            env_scenario.carbon_price_usd_per_tco2,
            sector_params["fossil_exposure_multiplier"],
            asset_char.asset_value,
        )

        # 2. Calculate Stranded Asset Risk
        stranded_asset_risk = self._calculate_stranded_asset_risk(
            asset_char.revenue_dependence,
            sector_params["stranded_asset_risk"],
            asset_char.adaptation_readiness,
            asset_char.asset_age_years,
            asset_char.asset_value,
        )

        # 3. Calculate Litigation Risk
        litigation_risk = self._calculate_litigation_risk(
            env_scenario.delta_temperature,
            env_scenario.litigation_media_exposure,
            env_scenario.regulatory_delay_factor,
            sector_params["litigation_sensitivity"],
            asset_char.asset_value,
        )

        # Apply beta weights
        weighted_carbon_tax = beta_weights["carbon_tax"] * carbon_tax_risk
        weighted_stranded_asset = beta_weights["stranded_asset"] * stranded_asset_risk
        weighted_litigation = beta_weights["litigation"] * litigation_risk

        # Total transition risk is the weighted sum
        total_transition_risk = (
            weighted_carbon_tax + weighted_stranded_asset + weighted_litigation
        )

        # Store components and parameters
        risk_components = {
            "carbon_tax_unweighted": carbon_tax_risk,
            "stranded_asset_unweighted": stranded_asset_risk,
            "litigation_unweighted": litigation_risk,
            "carbon_tax_weighted": weighted_carbon_tax,
            "stranded_asset_weighted": weighted_stranded_asset,
            "litigation_weighted": weighted_litigation,
        }

        return TransitionRiskResult(
            total_transition_risk=total_transition_risk,
            risk_components=risk_components,
            beta_weights=beta_weights,
            scenario=scenario_name,
            calculation_timestamp=datetime.now(),
        )

    def _calculate_carbon_tax_risk(
        self,
        fossil_exposure: float,
        carbon_price: float,
        exposure_multiplier: float,
        asset_value: float,
    ) -> float:
        """
        Calculate carbon tax risk component:
        CarbonTax = Exposição_energia_fóssil × US$ 150/tCO₂e (cenário 2030)
        """
        # Base carbon tax calculation
        base_carbon_tax = fossil_exposure * carbon_price  # USD per unit of asset value

        # Apply sector-specific multiplier
        adjusted_carbon_tax = base_carbon_tax * exposure_multiplier

        # Scale by asset value
        carbon_tax_risk = (
            adjusted_carbon_tax / 1000000
        ) * asset_value  # Scale by asset value

        return max(0.0, carbon_tax_risk)  # Non-negative risk

    def _calculate_stranded_asset_risk(
        self,
        revenue_dependence: float,
        sector_stranded_risk: float,
        adaptation_readiness: float,
        asset_age: int,
        asset_value: float,
    ) -> float:
        """
        Calculate stranded asset risk component
        """
        # Risk due to revenue dependence on high-carbon activities
        revenue_factor = revenue_dependence

        # Sector-specific stranded asset risk
        sector_factor = sector_stranded_risk

        # Adaptation readiness reduces risk
        adaptation_factor = max(
            0.1, 1 - adaptation_readiness
        )  # At least 10% of original risk

        # Older assets may be more at risk of stranding
        age_factor = min(
            1.5, 1 + (asset_age / 50.0)
        )  # Max 50% increase for very old assets

        stranded_asset_risk = (
            revenue_factor * sector_factor * adaptation_factor * age_factor
        )

        # Scale by asset value
        return stranded_asset_risk * asset_value

    def _calculate_litigation_risk(
        self,
        delta_temp: float,
        media_exposure: float,
        regulatory_delay: float,
        sensitivity: float,
        asset_value: float,
    ) -> float:
        """
        Calculate litigation risk component:
        Litígio = P(recurso_judicial) × E[indenização] × f(atraso_regulatório)
        P(recurso) = logit⁻¹(-6.2 + 1.5·ln(ΔT) + 0.8·midia_exposição)
        """
        # Calculate probability of litigation using the specified formula
        # P(recurso) = logit⁻¹(-6.2 + 1.5·ln(ΔT) + 0.8·midia_exposição)

        # Protect against log(0) by ensuring delta_temp > 0
        ln_delta_t = (
            np.log(max(0.01, delta_temp)) if delta_temp > 0 else -4
        )  # approx ln(0.01)

        # Calculate the linear combination
        logit_input = -6.2 + 1.5 * ln_delta_t + 0.8 * media_exposure

        # Apply logistic function: logit⁻¹(x) = 1 / (1 + exp(-x))
        prob_litigation = 1 / (1 + np.exp(-logit_input))

        # Expected compensation (simplified as proportional to asset value and sensitivity)
        expected_compensation = (
            sensitivity * asset_value * 0.1
        )  # 10% of asset value as proxy

        # Factor for regulatory delay (delays may increase litigation risk)
        regulatory_factor = 1 + (regulatory_delay * 0.5)  # Up to 50% increase

        litigation_risk = prob_litigation * expected_compensation * regulatory_factor

        return max(0.0, litigation_risk)

    def calculate_scenario_comparison(
        self,
        asset_char: AssetCharacteristics,
        baseline_scenario: EnvironmentalScenario,
        future_scenario: EnvironmentalScenario,
        beta_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Compare transition risk between baseline and future environmental scenarios.

        Args:
            asset_char: Asset characteristics
            baseline_scenario: Current environmental conditions
            future_scenario: Future environmental conditions
            beta_weights: Optional custom beta weights

        Returns:
            Dictionary with risk comparison results
        """
        # Calculate risks for both scenarios
        baseline_risk = self.calculate_transition_risk(
            asset_char, baseline_scenario, beta_weights, "baseline"
        )

        future_risk = self.calculate_transition_risk(
            asset_char, future_scenario, beta_weights, "future"
        )

        # Calculate changes
        risk_increase = (
            future_risk.total_transition_risk - baseline_risk.total_transition_risk
        )
        risk_ratio = (
            future_risk.total_transition_risk / baseline_risk.total_transition_risk
            if baseline_risk.total_transition_risk > 0
            else 1.0
        )

        return {
            "baseline_risk": baseline_risk.total_transition_risk,
            "future_risk": future_risk.total_transition_risk,
            "risk_increase": risk_increase,
            "risk_ratio": risk_ratio,
            "risk_percentage_increase": (risk_ratio - 1) * 100,
            "baseline_components": baseline_risk.risk_components,
            "future_components": future_risk.risk_components,
            "beta_weights_used": baseline_risk.beta_weights,
            "comparison_date": datetime.now().isoformat(),
        }

    def calculate_sector_specific_risk(
        self, asset_char: AssetCharacteristics, env_scenario: EnvironmentalScenario
    ) -> Dict[str, float]:
        """
        Calculate sector-specific transition risk components

        Args:
            asset_char: Asset characteristics
            env_scenario: Environmental scenario

        Returns:
            Dictionary with sector-specific risk breakdown
        """
        # Get sector-specific parameters
        sector_params = self.sector_parameters.get(
            asset_char.industry_sector, self.default_sector_params
        )

        # Calculate all risk components
        carbon_tax = self._calculate_carbon_tax_risk(
            asset_char.fossil_energy_exposure,
            env_scenario.carbon_price_usd_per_tco2,
            sector_params["fossil_exposure_multiplier"],
            asset_char.asset_value,
        )

        stranded_asset = self._calculate_stranded_asset_risk(
            asset_char.revenue_dependence,
            sector_params["stranded_asset_risk"],
            asset_char.adaptation_readiness,
            asset_char.asset_age_years,
            asset_char.asset_value,
        )

        litigation = self._calculate_litigation_risk(
            env_scenario.delta_temperature,
            env_scenario.litigation_media_exposure,
            env_scenario.regulatory_delay_factor,
            sector_params["litigation_sensitivity"],
            asset_char.asset_value,
        )

        return {
            "carbon_tax_component": carbon_tax,
            "stranded_asset_component": stranded_asset,
            "litigation_component": litigation,
            "sector_total_risk": carbon_tax + stranded_asset + litigation,
            "sector": asset_char.industry_sector,
            "fossil_exposure_multiplier": sector_params["fossil_exposure_multiplier"],
            "stranded_asset_sensitivity": sector_params["stranded_asset_risk"],
            "litigation_sensitivity": sector_params["litigation_sensitivity"],
        }

    def integrate_with_physical_risk(
        self, transition_risk_result: TransitionRiskResult, physical_risk_score: float
    ) -> Dict[str, float]:
        """
        Integrate transition risk with physical risk to get total climate risk

        Args:
            transition_risk_result: Transition risk calculation result
            physical_risk_score: Physical risk score from physical_risk_service

        Returns:
            Dictionary with integrated risk metrics
        """
        # Calculate total climate risk (simple sum of transition and physical risks)
        total_climate_risk = (
            transition_risk_result.total_transition_risk + physical_risk_score
        )

        # Calculate risk proportions
        if total_climate_risk > 0:
            transition_proportion = (
                transition_risk_result.total_transition_risk / total_climate_risk
            )
            physical_proportion = physical_risk_score / total_climate_risk
        else:
            transition_proportion = 0.5
            physical_proportion = 0.5

        return {
            "total_climate_risk": total_climate_risk,
            "transition_risk_contribution": transition_risk_result.total_transition_risk,
            "physical_risk_contribution": physical_risk_score,
            "transition_risk_proportion": transition_proportion,
            "physical_risk_proportion": physical_proportion,
            "dominant_risk_type": (
                "transition"
                if transition_proportion > physical_proportion
                else "physical"
            ),
        }


# Global instance
transition_risk_service = TransitionRiskCalculator()


def calculate_transition_risk(
    asset_char: AssetCharacteristics,
    env_scenario: EnvironmentalScenario,
    beta_weights: Optional[Dict[str, float]] = None,
    scenario_name: str = "base",
) -> TransitionRiskResult:
    """Convenience function to calculate transition risk"""
    return transition_risk_service.calculate_transition_risk(
        asset_char, env_scenario, beta_weights, scenario_name
    )


def calculate_scenario_comparison(
    asset_char: AssetCharacteristics,
    baseline_scenario: EnvironmentalScenario,
    future_scenario: EnvironmentalScenario,
    beta_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Convenience function to calculate scenario comparison"""
    return transition_risk_service.calculate_scenario_comparison(
        asset_char, baseline_scenario, future_scenario, beta_weights
    )


def calculate_sector_specific_risk(
    asset_char: AssetCharacteristics, env_scenario: EnvironmentalScenario
) -> Dict[str, float]:
    """Convenience function to calculate sector-specific risk"""
    return transition_risk_service.calculate_sector_specific_risk(
        asset_char, env_scenario
    )


def integrate_with_physical_risk(
    transition_risk_result: TransitionRiskResult, physical_risk_score: float
) -> Dict[str, float]:
    """Convenience function to integrate with physical risk"""
    return transition_risk_service.integrate_with_physical_risk(
        transition_risk_result, physical_risk_score
    )

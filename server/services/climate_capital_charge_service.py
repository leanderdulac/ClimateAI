"""
Climate Capital Charge (CCC) Calculation Service with Unmodeled Events Reserve
Implements: CCC = max(0, VaR_99%(Portfólio|evento_climático) - Reservas_climáticas)
Where:
- Reservas_climáticas = 0.03 × Prêmio_total_portfólio  [exigência EIOPA para riscos não-hedgeáveis]
- Reserva_adicional = 3-6% do prêmio para eventos climáticos não-modelado

Based on: Extended Climate Risk Capital Adequacy Framework
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.stats import norm

logger = logging.getLogger(__name__)


@dataclass
class PortfolioClimateVaR:
    """Value at Risk calculation for climate risks at portfolio level"""

    var_99_portfolio: float  # VaR at 99% confidence level for the portfolio
    var_95_portfolio: float  # VaR at 95% confidence level for reference
    expected_shortfall_99: float  # Expected shortfall at 99% level
    portfolio_premium: float  # Total portfolio premium
    climate_scenario_type: str  # Type of climate scenario analyzed
    calculation_method: str  # Method used for VaR calculation
    confidence_level: float  # Confidence level used (0.99 for 99%)
    climate_correlation_factor: (
        float  # Factor accounting for climate correlation across the portfolio
    )
    tail_dependence_parameter: float  # Parameter for extreme value correlation
    calculation_timestamp: datetime


@dataclass
class ClimateCapitalChargeResult:
    """Result of Climate Capital Charge calculation"""

    climate_capital_charge: float  # CCC value
    portfolio_var_99: float  # VaR_99%(Portfólio|evento_climático)
    climate_reserves: float  # Reservas_climáticas (EIOPA requirement)
    unmodeled_events_reserve: (
        float  # Additional reserve for unmodeled climate events (3-6%)
    )
    total_climate_reserves: float  # Combined reserves (climate + unmodeled events)
    portfolio_premium: float  # Total portfolio premium
    reserve_rate: float  # Reserve rate (0.03 for EIOPA)
    unmodeled_reserve_rate: float  # Reserve rate for unmodeled events (0.03 to 0.06)
    climate_scenario_type: str  # Climate scenario used
    calculation_method: str  # Method used for calculation
    portfolio_size: int  # Number of policies in portfolio
    climate_risk_concentration: float  # Measure of climate risk concentration
    calculation_timestamp: datetime


@dataclass
class PolicyClimateRisk:
    """Climate risk component for an individual policy"""

    policy_id: str
    premium_value: float
    climate_risk_score: float
    climate_correlation: float  # Correlation with climate events
    expected_climate_loss: float
    climate_var_99: float  # VaR at 99% for this policy
    climate_scenario_impact: float  # Impact of climate scenario on this policy


class ClimateCapitalChargeCalculator:
    """
    Calculator for Climate Capital Charge (CCC) with unmodeled events reserve:
    CCC = max(0, VaR_99%(Portfólio|evento_climático) - (Reservas_climáticas + Reserva_adicional))
    Where:
    - Reservas_climáticas = 0.03 × Prêmio_total_portfólio [EIOPA requirement]
    - Reserva_adicional = 3-6% do prêmio para eventos climáticos não-modelado
    """

    def __init__(self):
        # EIOPA reserve requirement rate (3% for non-hedgeable climate risks)
        self.reserve_rate = 0.03  # 3% of total portfolio premium

        # Additional reserve rate for unmodeled climate events (3-6% as requested)
        self.unmodeled_events_reserve_rate_min = 0.03  # 3% minimum
        self.unmodeled_events_reserve_rate_max = 0.06  # 6% maximum
        self.unmodeled_events_reserve_rate = 0.045  # Default 4.5% midpoint

        # Climate scenario parameters
        self.climate_scenarios = {
            "baseline": {"severity_multiplier": 1.0, "correlation_factor": 0.5},
            "moderate_warming": {"severity_multiplier": 1.3, "correlation_factor": 0.6},
            "severe_warming": {"severity_multiplier": 1.8, "correlation_factor": 0.7},
            "extreme_events": {"severity_multiplier": 2.5, "correlation_factor": 0.8},
            "transition_shock": {"severity_multiplier": 1.5, "correlation_factor": 0.4},
        }

        # Parameters for Extreme Value Theory calculations
        self.evt_shape_parameter = (
            -0.1
        )  # Shape parameter for climate loss distribution (Fréchet type)
        self.evt_scale_parameter = 1000  # Scale parameter for EVT
        self.evt_location_parameter = 500  # Location parameter for EVT

        # Tail dependence parameter for climate extreme events
        self.tail_dependence_rho = 0.3  # Parameter for climate extreme value copula

        # Stress testing multipliers for climate scenarios
        self.stress_test_multipliers = {
            "low_stress": 1.1,
            "moderate_stress": 1.2,
            "high_stress": 1.4,
            "extreme_stress": 1.8,
        }

    def calculate_climate_var_portfolio(
        self,
        policies: List[PolicyClimateRisk],
        climate_scenario: str = "moderate_warming",
        stress_level: str = "moderate_stress",
    ) -> PortfolioClimateVaR:
        """
        Calculate portfolio Value at Risk at 99% confidence level considering climate scenarios

        Args:
            policies: List of policies with their climate risk components
            climate_scenario: Climate scenario to consider ('baseline', 'moderate_warming', etc.)
            stress_level: Stress test level to apply

        Returns:
            PortfolioClimateVaR with VaR and related metrics
        """
        if not policies:
            return PortfolioClimateVaR(
                var_99_portfolio=0.0,
                var_95_portfolio=0.0,
                expected_shortfall_99=0.0,
                portfolio_premium=0.0,
                climate_scenario_type=climate_scenario,
                calculation_method="extreme_value_theory",
                confidence_level=0.99,
                climate_correlation_factor=0.0,
                tail_dependence_parameter=0.0,
                calculation_timestamp=datetime.now(),
            )

        # Calculate total portfolio premium
        total_portfolio_premium = sum(policy.premium_value for policy in policies)

        # Get climate scenario parameters
        scenario_params = self.climate_scenarios.get(
            climate_scenario, self.climate_scenarios["baseline"]
        )

        # Get stress test multiplier
        stress_multiplier = self.stress_test_multipliers.get(stress_level, 1.0)

        # Calculate individual policy contributions to portfolio risk
        policy_risks = []
        total_climate_weighted_risk = 0.0
        climate_correlation_sum = 0.0

        for policy in policies:
            # Weight risk by premium and climate correlation
            weighted_risk = policy.expected_climate_loss * policy.climate_correlation
            policy_risks.append(weighted_risk)
            total_climate_weighted_risk += weighted_risk
            climate_correlation_sum += policy.climate_correlation

        # Calculate portfolio diversification factor based on climate correlations
        mean_climate_correlation = (
            climate_correlation_sum / len(policies) if policies else 0.0
        )

        # Calculate portfolio VaR using extreme value theory approach
        # For climate extreme events, we use a Generalized Extreme Value distribution
        if policy_risks:
            # Calculate portfolio-level quantiles using EVT
            # Use the block maxima method for VaR calculation
            n_policies = len(policies)

            # Adjust EVT parameters based on climate scenario
            adjusted_shape = (
                self.evt_shape_parameter * scenario_params["severity_multiplier"]
            )
            adjusted_scale = (
                self.evt_scale_parameter * scenario_params["severity_multiplier"]
            )

            # Calculate VaR for portfolio using EVT (quantile function)
            # For GEV distribution: VaR_α = μ + (σ/ξ) * [(−log(1−α))^(-ξ) - 1] if ξ ≠ 0
            alpha_99 = 0.99
            alpha_95 = 0.95

            if adjusted_shape != 0:
                var_99_raw = self.evt_location_parameter + (
                    adjusted_scale / adjusted_shape
                ) * ((-(np.log(1 - alpha_99))) ** (-adjusted_shape) - 1)
                var_95_raw = self.evt_location_parameter + (
                    adjusted_scale / adjusted_shape
                ) * ((-(np.log(1 - alpha_95))) ** (-adjusted_shape) - 1)
            else:
                # When ξ = 0, use Gumbel distribution
                var_99_raw = self.evt_location_parameter - adjusted_scale * np.log(
                    -np.log(alpha_99)
                )
                var_95_raw = self.evt_location_parameter - adjusted_scale * np.log(
                    -np.log(alpha_95)
                )

            # Ensure VaR values are positive (they represent risk/potential losses)
            var_99_raw = max(0, var_99_raw)
            var_95_raw = max(0, var_95_raw)

            # Scale by portfolio size and stress test
            portfolio_var_99 = (
                var_99_raw * (n_policies**0.5) * stress_multiplier
            )  # Square root of n scaling
            portfolio_var_95 = var_95_raw * (n_policies**0.5) * stress_multiplier

            # Calculate Expected Shortfall (average of losses beyond VaR_99)
            # This is a simplified calculation for demonstration
            expected_shortfall_99 = (
                portfolio_var_99 * 1.2
            )  # ES is typically higher than VaR

            # Apply climate correlation adjustment
            climate_correlation_factor = scenario_params["correlation_factor"]
            portfolio_var_99 *= (
                1 + climate_correlation_factor * mean_climate_correlation
            )
            portfolio_var_95 *= (
                1 + climate_correlation_factor * mean_climate_correlation
            )
            expected_shortfall_99 *= (
                1 + climate_correlation_factor * mean_climate_correlation
            )
        else:
            portfolio_var_99 = 0.0
            portfolio_var_95 = 0.0
            expected_shortfall_99 = 0.0
            climate_correlation_factor = 0.0

        return PortfolioClimateVaR(
            var_99_portfolio=portfolio_var_99,
            var_95_portfolio=portfolio_var_95,
            expected_shortfall_99=expected_shortfall_99,
            portfolio_premium=total_portfolio_premium,
            climate_scenario_type=climate_scenario,
            calculation_method="extreme_value_theory",
            confidence_level=0.99,
            climate_correlation_factor=mean_climate_correlation,
            tail_dependence_parameter=self.tail_dependence_rho,
            calculation_timestamp=datetime.now(),
        )

    def calculate_climate_reserves(self, total_portfolio_premium: float) -> float:
        """
        Calculate climate reserves based on EIOPA requirement:
        Reservas_climáticas = 0.03 × Prêmio_total_portfólio

        Args:
            total_portfolio_premium: Total premium of the portfolio

        Returns:
            Climate reserves amount
        """
        climate_reserves = self.reserve_rate * total_portfolio_premium
        return climate_reserves

    def calculate_unmodeled_events_reserve(
        self, total_portfolio_premium: float, reserve_rate: Optional[float] = None
    ) -> float:
        """
        Calculate additional reserve for unmodeled climate events:
        Reserva_adicional = 3-6% do prêmio para eventos climáticos não-modelado

        Args:
            total_portfolio_premium: Total premium of the portfolio
            reserve_rate: Optional custom reserve rate (between 0.03 and 0.06)

        Returns:
            Unmodeled events reserve amount
        """
        if reserve_rate is None:
            reserve_rate = self.unmodeled_events_reserve_rate
        else:
            # Ensure the rate is within the specified range
            reserve_rate = max(
                self.unmodeled_events_reserve_rate_min,
                min(self.unmodeled_events_reserve_rate_max, reserve_rate),
            )

        unmodeled_events_reserve = reserve_rate * total_portfolio_premium
        return unmodeled_events_reserve

    def calculate_climate_capital_charge(
        self,
        policies: List[PolicyClimateRisk],
        climate_scenario: str = "moderate_warming",
        stress_level: str = "moderate_stress",
        unmodeled_reserve_rate: Optional[float] = None,
    ) -> ClimateCapitalChargeResult:
        """
        Calculate Climate Capital Charge with additional unmodeled events reserve:
        CCC = max(0, VaR_99%(Portfólio|evento_climático) - (Reservas_climáticas + Reserva_adicional))
        Where:
        - Reservas_climáticas = 0.03 × Prêmio_total_portfólio
        - Reserva_adicional = 3-6% do prêmio para eventos climáticos não-modelado

        Args:
            policies: List of policy climate risks
            climate_scenario: Climate scenario to consider
            stress_level: Stress test level to apply
            unmodeled_reserve_rate: Optional custom rate for unmodeled events (0.03-0.06)

        Returns:
            ClimateCapitalChargeResult with complete CCC calculation including unmodeled events reserve
        """
        # Calculate portfolio VaR at 99% confidence level
        portfolio_var_result = self.calculate_climate_var_portfolio(
            policies, climate_scenario, stress_level
        )

        # Calculate climate reserves (EIOPA requirement)
        climate_reserves = self.calculate_climate_reserves(
            portfolio_var_result.portfolio_premium
        )

        # Calculate additional reserve for unmodeled climate events (3-6% as requested)
        unmodeled_events_reserve = self.calculate_unmodeled_events_reserve(
            portfolio_var_result.portfolio_premium, unmodeled_reserve_rate
        )

        # Total climate reserves (EIOPA + unmodeled events)
        total_climate_reserves = climate_reserves + unmodeled_events_reserve

        # Calculate climate capital charge
        climate_capital_charge = max(
            0, portfolio_var_result.var_99_portfolio - total_climate_reserves
        )

        # Calculate climate risk concentration measure
        if len(policies) > 0:
            # Measure concentration of climate risks
            risk_weights = [
                (
                    p.expected_climate_loss / portfolio_var_result.portfolio_premium
                    if portfolio_var_result.portfolio_premium > 0
                    else 0
                )
                for p in policies
            ]
            climate_risk_concentration = self._calculate_concentration_index(
                risk_weights
            )
        else:
            climate_risk_concentration = 0.0

        # Use the provided or default unmodeled reserve rate
        effective_unmodeled_rate = (
            unmodeled_reserve_rate
            if unmodeled_reserve_rate is not None
            else self.unmodeled_events_reserve_rate
        )

        return ClimateCapitalChargeResult(
            climate_capital_charge=climate_capital_charge,
            portfolio_var_99=portfolio_var_result.var_99_portfolio,
            climate_reserves=climate_reserves,
            unmodeled_events_reserve=unmodeled_events_reserve,
            total_climate_reserves=total_climate_reserves,
            portfolio_premium=portfolio_var_result.portfolio_premium,
            reserve_rate=self.reserve_rate,
            unmodeled_reserve_rate=effective_unmodeled_rate,
            climate_scenario_type=climate_scenario,
            calculation_method=portfolio_var_result.calculation_method,
            portfolio_size=len(policies),
            climate_risk_concentration=climate_risk_concentration,
            calculation_timestamp=portfolio_var_result.calculation_timestamp,
        )

    def _calculate_concentration_index(self, risk_weights: List[float]) -> float:
        """
        Calculate concentration index based on risk weights

        Args:
            risk_weights: List of risk weights for each policy

        Returns:
            Concentration index (Herfindahl-Hirschman Index normalized)
        """
        if not risk_weights:
            return 0.0

        # Calculate Herfindahl-Hirschman Index (HHI)
        hhi = sum(weight**2 for weight in risk_weights)

        # Normalize: HHI ranges from 1/n to 1
        n = len(risk_weights)
        if n <= 1:
            return 1.0 if n == 1 else 0.0

        # Min and max possible HHI values for this portfolio size
        min_hhi = 1.0 / n  # Perfectly distributed risk
        max_hhi = 1.0  # All risk concentrated in one policy

        if max_hhi == min_hhi:
            return 0.0

        # Normalize to 0-1 scale where 0 = perfectly distributed, 1 = maximally concentrated
        normalized_concentration = (hhi - min_hhi) / (max_hhi - min_hhi)

        return normalized_concentration

    def calculate_portfolio_stress_test(
        self,
        policies: List[PolicyClimateRisk],
        baseline_scenario: str = "baseline",
        stress_scenario: str = "extreme_events",
        unmodeled_reserve_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate stress test by comparing baseline and stressed scenarios with unmodeled events reserve

        Args:
            policies: Portfolio policies
            baseline_scenario: Baseline climate scenario
            stress_scenario: Stress climate scenario
            unmodeled_reserve_rate: Optional custom rate for unmodeled events

        Returns:
            Dictionary with stress test results
        """
        # Calculate baseline CCC
        baseline_result = self.calculate_climate_capital_charge(
            policies, baseline_scenario, "low_stress", unmodeled_reserve_rate
        )

        # Calculate stressed CCC
        stress_result = self.calculate_climate_capital_charge(
            policies, stress_scenario, "extreme_stress", unmodeled_reserve_rate
        )

        # Calculate stress metrics
        stress_impact = (
            stress_result.climate_capital_charge
            - baseline_result.climate_capital_charge
        )
        stress_ratio = (
            stress_result.climate_capital_charge
            / baseline_result.climate_capital_charge
            if baseline_result.climate_capital_charge > 0
            else 0.0
        )

        return {
            "baseline_scenario": baseline_scenario,
            "stress_scenario": stress_scenario,
            "baseline_ccc": baseline_result.climate_capital_charge,
            "stress_ccc": stress_result.climate_capital_charge,
            "stress_impact": stress_impact,
            "stress_ratio": stress_ratio,
            "stress_percentage_increase": (stress_ratio - 1) * 100,
            "portfolio_premium": baseline_result.portfolio_premium,
            "baseline_reserve_requirement": baseline_result.total_climate_reserves,
            "stress_reserve_requirement": stress_result.total_climate_reserves,
            "baseline_var_99": baseline_result.portfolio_var_99,
            "stress_var_99": stress_result.portfolio_var_99,
            "baseline_climate_reserves": baseline_result.climate_reserves,
            "baseline_unmodeled_events_reserve": baseline_result.unmodeled_events_reserve,
            "stress_climate_reserves": stress_result.climate_reserves,
            "stress_unmodeled_events_reserve": stress_result.unmodeled_events_reserve,
            "stress_test_completed": True,
            "stress_test_timestamp": datetime.now().isoformat(),
        }

    def optimize_climate_reserves(
        self,
        policies: List[PolicyClimateRisk],
        climate_scenario: str = "moderate_warming",
        target_ccc: float = 0.0,
        unmodeled_reserve_rate: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Optimize climate reserves to achieve target capital charge with unmodeled events component

        Args:
            policies: Portfolio policies
            climate_scenario: Climate scenario to consider
            target_ccc: Target climate capital charge
            unmodeled_reserve_rate: Optional custom rate for unmodeled events

        Returns:
            Dictionary with optimized reserve recommendations
        """
        # Calculate current VaR
        portfolio_var_result = self.calculate_climate_var_portfolio(
            policies, climate_scenario, "moderate_stress"
        )

        # Calculate current reserves and CCC
        current_result = self.calculate_climate_capital_charge(
            policies, climate_scenario, "moderate_stress", unmodeled_reserve_rate
        )

        # Calculate required reserves to achieve target CCC
        if target_ccc >= 0:
            required_total_reserves = max(
                0, portfolio_var_result.var_99_portfolio - target_ccc
            )
        else:
            required_total_reserves = (
                portfolio_var_result.var_99_portfolio
            )  # If negative CCC allowed

        # Calculate gap between current and required reserves
        reserve_gap = required_total_reserves - current_result.total_climate_reserves

        # Calculate required reserve rate
        required_reserve_rate = (
            required_total_reserves / portfolio_var_result.portfolio_premium
            if portfolio_var_result.portfolio_premium > 0
            else 0.0
        )

        return {
            "current_ccc": current_result.climate_capital_charge,
            "target_ccc": target_ccc,
            "current_total_reserves": current_result.total_climate_reserves,
            "required_total_reserves": required_total_reserves,
            "current_climate_reserves": current_result.climate_reserves,
            "current_unmodeled_events_reserve": current_result.unmodeled_events_reserve,
            "current_unmodeled_rate": current_result.unmodeled_reserve_rate,
            "reserve_gap": reserve_gap,
            "required_reserve_rate": required_reserve_rate,
            "portfolio_premium": portfolio_var_result.portfolio_premium,
            "portfolio_var_99": portfolio_var_result.var_99_portfolio,
            "optimization_suggestion": (
                "increase"
                if reserve_gap > 0
                else "decrease" if reserve_gap < 0 else "maintain"
            ),
        }

    def get_unmodeled_events_reserve_range(self) -> Dict[str, float]:
        """
        Get the valid range for unmodeled events reserve rates.

        Returns:
            Dictionary with min, max, and default rates
        """
        return {
            "min_rate": self.unmodeled_events_reserve_rate_min,
            "max_rate": self.unmodeled_events_reserve_rate_max,
            "default_rate": self.unmodeled_events_reserve_rate,
            "range_percentage": f"{self.unmodeled_events_reserve_rate_min*100:.1f}% - {self.unmodeled_events_reserve_rate_max*100:.1f}%",
            "description": "Additional reserve for unmodeled climate events (3-6% of premium)",
        }


# Global instance
ccc_calculator = ClimateCapitalChargeCalculator()


def calculate_climate_capital_charge(
    policies: List[PolicyClimateRisk],
    climate_scenario: str = "moderate_warming",
    stress_level: str = "moderate_stress",
    unmodeled_reserve_rate: Optional[float] = None,
) -> ClimateCapitalChargeResult:
    """Convenience function to calculate climate capital charge with unmodeled events reserve"""
    return ccc_calculator.calculate_climate_capital_charge(
        policies, climate_scenario, stress_level, unmodeled_reserve_rate
    )


def calculate_portfolio_climate_var(
    policies: List[PolicyClimateRisk],
    climate_scenario: str = "moderate_warming",
    stress_level: str = "moderate_stress",
) -> PortfolioClimateVaR:
    """Convenience function to calculate portfolio climate VaR"""
    return ccc_calculator.calculate_climate_var_portfolio(
        policies, climate_scenario, stress_level
    )


def calculate_climate_reserves(total_portfolio_premium: float) -> float:
    """Convenience function to calculate EIOPA climate reserves"""
    return ccc_calculator.calculate_climate_reserves(total_portfolio_premium)


def calculate_unmodeled_events_reserve(
    total_portfolio_premium: float, reserve_rate: Optional[float] = None
) -> float:
    """Convenience function to calculate unmodeled events reserve (3-6% of premium)"""
    return ccc_calculator.calculate_unmodeled_events_reserve(
        total_portfolio_premium, reserve_rate
    )


def perform_portfolio_stress_test(
    policies: List[PolicyClimateRisk],
    baseline_scenario: str = "baseline",
    stress_scenario: str = "extreme_events",
    unmodeled_reserve_rate: Optional[float] = None,
) -> Dict[str, Any]:
    """Convenience function to perform portfolio stress test with unmodeled events reserve"""
    return ccc_calculator.calculate_portfolio_stress_test(
        policies, baseline_scenario, stress_scenario, unmodeled_reserve_rate
    )


def optimize_climate_reserves(
    policies: List[PolicyClimateRisk],
    climate_scenario: str = "moderate_warming",
    target_ccc: float = 0.0,
    unmodeled_reserve_rate: Optional[float] = None,
) -> Dict[str, float]:
    """Convenience function to optimize climate reserves including unmodeled events"""
    return ccc_calculator.optimize_climate_reserves(
        policies, climate_scenario, target_ccc, unmodeled_reserve_rate
    )


def get_unmodeled_events_reserve_range() -> Dict[str, float]:
    """Convenience function to get the valid range for unmodeled events reserves"""
    return ccc_calculator.get_unmodeled_events_reserve_range()

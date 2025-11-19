"""
Capital Surplus (CS) Calculation Service
Implements: CS = z_α × √Var(Loss) / E[Loss]
Where:
- z_α = normal quantile (e.g., 1.645 for α=95%)
- Var(Loss) = E[Loss²] - E[Loss]² + σ²_climático
- σ²_climático = (SCR/1000)² × λ_clim × (1 - λ_clim)  [binomial climate variance]

Based on: Climate Risk Capital Adequacy Framework
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class CapitalSurplusResult:
    """Result of Capital Surplus calculation"""

    capital_surplus: float  # CS value
    quantile_factor: float  # z_α component
    variance_loss: float  # Var(Loss) component
    expected_loss: float  # E[Loss] component
    climate_variance: float  # σ²_climático component
    climate_lambda: float  # λ_clim parameter
    confidence_level: float  # α parameter
    scr_normalized: float  # SCR/1000 component
    calculation_timestamp: datetime


@dataclass
class LossDistributionParameters:
    """Parameters describing the loss distribution"""

    expected_loss: float  # E[Loss]
    expected_loss_squared: float  # E[Loss²]
    variance_base: float  # Base variance (without climate component)
    standard_deviation: float  # σ of the base loss distribution


@dataclass
class ClimateRiskParameters:
    """Climate risk parameters for variance calculation"""

    scr_score: float  # Raw SCR score
    climate_loss_probability: float  # λ_clim (0-1, probability of climate loss event)
    climate_sensitivity_factor: float = 0.001  # Factor for climate sensitivity


class CapitalSurplusCalculator:
    """
    Calculates Capital Surplus using the specified formula:
    CS = z_α × √Var(Loss) / E[Loss]
    Where Var(Loss) = E[Loss²] - E[Loss]² + σ²_climático
    And σ²_climático = (SCR/1000)² × λ_clim × (1 - λ_clim)
    """

    def __init__(self):
        # Default climate parameters
        self.default_climate_lambda = 0.1  # Default 10% probability of climate event
        self.default_confidence_level = 0.95  # 95% confidence level
        self.default_z_alpha = stats.norm.ppf(
            0.95
        )  # Calculate 1.645 for 95% confidence
        # Climate sensitivity factor
        self.climate_sensitivity_factor = (
            0.001  # Adjusts impact of SCR on climate variance
        )

        # Risk correlation factors between different risk types
        self.risk_correlation_matrix = {
            "physical_transition": 0.3,  # Correlation between physical and transition risks
            "physical_concentration": 0.2,  # Correlation between physical and concentration risks
            "transition_concentration": 0.15,  # Correlation between transition and concentration risks
        }

    def calculate_climate_variance(
        self, scr_score: float, climate_lambda: Optional[float] = None
    ) -> float:
        """
        Calculate climate variance component:
        σ²_climático = (SCR/1000)² × λ_clim × (1 - λ_clim)  [binomial climate variance]

        Args:
            scr_score: Raw SCR score
            climate_lambda: Climate loss probability λ_clim (0-1)

        Returns:
            Climate variance component σ²_climático
        """
        if climate_lambda is None:
            climate_lambda = self.default_climate_lambda

        # Validate lambda is between 0 and 1
        climate_lambda = max(0.0, min(1.0, climate_lambda))

        # Calculate normalized SCR
        scr_normalized = scr_score / 1000.0

        # Calculate climate variance: (SCR/1000)² × λ_clim × (1 - λ_clim)
        climate_variance = (scr_normalized**2) * climate_lambda * (1 - climate_lambda)

        return climate_variance

    def calculate_total_loss_variance(
        self, loss_params: LossDistributionParameters, climate_variance: float
    ) -> float:
        """
        Calculate total loss variance:
        Var(Loss) = E[Loss²] - E[Loss]² + σ²_climático

        Args:
            loss_params: Parameters describing the base loss distribution
            climate_variance: Climate variance component σ²_climático

        Returns:
            Total loss variance Var(Loss)
        """
        # Calculate base variance from E[Loss²] - E[Loss]²
        base_variance = loss_params.expected_loss_squared - (
            loss_params.expected_loss**2
        )

        # Add climate variance component
        total_variance = base_variance + climate_variance

        return max(0.0, total_variance)  # Ensure non-negative variance

    def calculate_capital_surplus(
        self,
        loss_params: LossDistributionParameters,
        climate_params: ClimateRiskParameters,
        confidence_level: Optional[float] = None,
    ) -> CapitalSurplusResult:
        """
        Calculate Capital Surplus using the specified formula:
        CS = z_α × √Var(Loss) / E[Loss]

        Args:
            loss_params: Parameters describing the loss distribution
            climate_params: Climate risk parameters for variance calculation
            confidence_level: Confidence level α (default 0.95)

        Returns:
            CapitalSurplusResult with complete calculation
        """
        if confidence_level is None:
            confidence_level = self.default_confidence_level

        # Calculate z_α (normal quantile)
        z_alpha = stats.norm.ppf(confidence_level)

        # Calculate climate variance component
        climate_variance = self.calculate_climate_variance(
            climate_params.scr_score, climate_params.climate_loss_probability
        )

        # Calculate total loss variance
        total_variance = self.calculate_total_loss_variance(
            loss_params, climate_variance
        )

        # Calculate standard deviation of loss
        loss_std_dev = np.sqrt(total_variance)

        # Calculate capital surplus: CS = z_α × √Var(Loss) / E[Loss]
        if loss_params.expected_loss > 0:
            capital_surplus = (z_alpha * loss_std_dev) / loss_params.expected_loss
        else:
            capital_surplus = 0.0  # Avoid division by zero

        return CapitalSurplusResult(
            capital_surplus=capital_surplus,
            quantile_factor=z_alpha,
            variance_loss=total_variance,
            expected_loss=loss_params.expected_loss,
            climate_variance=climate_variance,
            climate_lambda=climate_params.climate_loss_probability,
            confidence_level=confidence_level,
            scr_normalized=climate_params.scr_score / 1000.0,
            calculation_timestamp=datetime.now(),
        )

    def estimate_loss_distribution_parameters(
        self,
        physical_risk: float,
        transition_risk: float,
        concentration_risk: float,
        mitigation_effect: float = 0.0,
        correlation_adjustment: bool = True,
    ) -> LossDistributionParameters:
        """
        Estimate loss distribution parameters from risk components

        Args:
            physical_risk: Physical risk component R_físico
            transition_risk: Transition risk component R_transição
            concentration_risk: Concentration risk component R_concentração
            mitigation_effect: Effect of mitigation measures (0-1)
            correlation_adjustment: Whether to account for risk correlations

        Returns:
            LossDistributionParameters with estimated E[Loss] and E[Loss²]
        """
        # Calculate total risk before mitigation
        total_risk = physical_risk + transition_risk + concentration_risk

        # Apply mitigation effect
        mitigated_risk = total_risk * (1 - mitigation_effect)

        # Apply correlation adjustment if enabled
        if correlation_adjustment:
            # Adjust based on correlations between risk types
            correlation_factor = (
                1
                + self.risk_correlation_matrix["physical_transition"] * 0.1
                + self.risk_correlation_matrix["physical_concentration"] * 0.05
                + self.risk_correlation_matrix["transition_concentration"] * 0.05
            )
            mitigated_risk *= correlation_factor

        # Estimate E[Loss] as the mitigated risk
        expected_loss = max(0.0, mitigated_risk)

        # Estimate E[Loss²] based on distribution assumptions
        # For a variety of risk distributions, we might assume a relationship with variance
        # Using a common assumption for insurance risk: E[Loss²] = E[Loss]² + Var[Loss]
        # Where Var[Loss] might be proportional to E[Loss]² for heavy-tailed distributions
        base_variance = expected_loss * 0.5  # Base variance assumption
        expected_loss_squared = (expected_loss**2) + base_variance

        # Calculate standard deviation
        standard_deviation = np.sqrt(base_variance)

        return LossDistributionParameters(
            expected_loss=expected_loss,
            expected_loss_squared=expected_loss_squared,
            variance_base=base_variance,
            standard_deviation=standard_deviation,
        )

    def calculate_capital_surplus_from_risks(
        self,
        physical_risk: float,
        transition_risk: float,
        concentration_risk: float,
        scr_score: float,
        mitigation_effect: float = 0.0,
        climate_lambda: Optional[float] = None,
        confidence_level: Optional[float] = 0.95,
    ) -> CapitalSurplusResult:
        """
        Calculate Capital Surplus directly from risk components:
        CS = z_α × √Var(Loss) / E[Loss]
        Where Var(Loss) = E[Loss²] - E[Loss]² + σ²_climático
        And σ²_climático = (SCR/1000)² × λ_clim × (1 - λ_clim)

        Args:
            physical_risk: Physical risk component (R_físico)
            transition_risk: Transition risk component (R_transição)
            concentration_risk: Concentration risk component (R_concentração)
            scr_score: SCR score for climate variance calculation
            mitigation_effect: Effect of mitigation measures (0-1)
            climate_lambda: Climate loss probability λ_clim (0-1)
            confidence_level: Confidence level α (default 0.95)

        Returns:
            CapitalSurplusResult with complete CS calculation
        """
        # Estimate loss distribution parameters from risk components
        loss_params = self.estimate_loss_distribution_parameters(
            physical_risk, transition_risk, concentration_risk, mitigation_effect
        )

        # Create climate risk parameters
        climate_params = ClimateRiskParameters(
            scr_score=scr_score,
            climate_loss_probability=(
                climate_lambda
                if climate_lambda is not None
                else self.default_climate_lambda
            ),
        )

        # Calculate capital surplus
        cs_result = self.calculate_capital_surplus(
            loss_params, climate_params, confidence_level
        )

        return cs_result

    def calculate_portfolio_capital_surplus(
        self,
        portfolio_risks: List[Dict[str, float]],
        portfolio_scr_scores: List[float],
        portfolio_mitigation_effects: List[float],
        portfolio_weights: Optional[List[float]] = None,
        climate_lambda: Optional[float] = None,
        confidence_level: Optional[float] = 0.95,
    ) -> Dict[str, Any]:
        """
        Calculate capital surplus for an insurance portfolio

        Args:
            portfolio_risks: List of dicts with 'physical', 'transition', 'concentration' risk values
            portfolio_scr_scores: List of SCR scores for each policy
            portfolio_mitigation_effects: List of mitigation effects (0-1) for each policy
            portfolio_weights: Optional weights for each policy (defaults to equal weights)
            climate_lambda: Climate loss probability λ_clim (0-1)
            confidence_level: Confidence level α (default 0.95)

        Returns:
            Dictionary with portfolio-level CS calculation and metrics
        """
        n_policies = len(portfolio_risks)
        if n_policies == 0:
            return {
                "portfolio_capital_surplus": 0.0,
                "number_of_policies": 0,
                "weighted_expected_loss": 0.0,
                "portfolio_variance": 0.0,
                "calculation_timestamp": datetime.now().isoformat(),
            }

        if (
            len(portfolio_scr_scores) != n_policies
            or len(portfolio_mitigation_effects) != n_policies
        ):
            raise ValueError(
                "All risk, SCR, and mitigation lists must have the same length"
            )

        # Set default weights if not provided
        if portfolio_weights is None:
            portfolio_weights = [1.0 / n_policies] * n_policies
        elif len(portfolio_weights) != n_policies:
            raise ValueError("Portfolio weights must match number of policies")

        # Calculate individual policy parameters
        individual_results = []
        total_weighted_expected_loss = 0.0
        total_weighted_variance = 0.0

        for i, risk_dict in enumerate(portfolio_risks):
            physical = risk_dict.get("physical", 0.0)
            transition = risk_dict.get("transition", 0.0)
            concentration = risk_dict.get("concentration", 0.0)

            # Calculate individual policy CS
            policy_cs_result = self.calculate_capital_surplus_from_risks(
                physical_risk=physical,
                transition_risk=transition,
                concentration_risk=concentration,
                scr_score=portfolio_scr_scores[i],
                mitigation_effect=portfolio_mitigation_effects[i],
                climate_lambda=climate_lambda,
                confidence_level=confidence_level,
            )

            individual_results.append(policy_cs_result)

            # Weighted contributions
            weight = portfolio_weights[i]
            total_weighted_expected_loss += weight * policy_cs_result.expected_loss
            total_weighted_variance += weight * policy_cs_result.variance_loss

        # Calculate portfolio-level metrics
        portfolio_cs = 0.0
        if total_weighted_expected_loss > 0:
            # Portfolio CS using weighted average of variances and expected losses
            portfolio_std_dev = np.sqrt(total_weighted_variance)
            z_alpha = stats.norm.ppf(confidence_level)
            portfolio_cs = (z_alpha * portfolio_std_dev) / total_weighted_expected_loss

        return {
            "portfolio_capital_surplus": portfolio_cs,
            "number_of_policies": n_policies,
            "weighted_expected_loss": total_weighted_expected_loss,
            "portfolio_variance": total_weighted_variance,
            "portfolio_std_dev": np.sqrt(total_weighted_variance),
            "average_confidence_level": confidence_level,
            "climate_lambda": (
                climate_lambda
                if climate_lambda is not None
                else self.default_climate_lambda
            ),
            "calculation_timestamp": datetime.now().isoformat(),
            "individual_policy_results": [
                {
                    "policy_index": i,
                    "physical_risk": portfolio_risks[i].get("physical", 0.0),
                    "transition_risk": portfolio_risks[i].get("transition", 0.0),
                    "concentration_risk": portfolio_risks[i].get("concentration", 0.0),
                    "scr_score": portfolio_scr_scores[i],
                    "mitigation_effect": portfolio_mitigation_effects[i],
                    "weight": portfolio_weights[i],
                    "expected_loss": individual_results[i].expected_loss,
                    "variance_loss": individual_results[i].variance_loss,
                    "capital_surplus": individual_results[i].capital_surplus,
                }
                for i in range(n_policies)
            ],
        }

    def optimize_capital_efficiency(
        self,
        target_capital_surplus: float,
        physical_risk: float,
        transition_risk: float,
        concentration_risk: float,
        scr_score: float,
        climate_lambda: Optional[float] = None,
        confidence_level: Optional[float] = 0.95,
    ) -> Dict[str, float]:
        """
        Optimize mitigation investment to achieve target capital surplus

        Args:
            target_capital_surplus: Desired capital surplus level
            physical_risk: Physical risk component
            transition_risk: Transition risk component
            concentration_risk: Concentration risk component
            scr_score: SCR score
            climate_lambda: Climate loss probability λ_clim
            confidence_level: Confidence level α

        Returns:
            Dictionary with optimization results and required mitigation levels
        """
        # Binary search to find the required mitigation effect
        min_mitigation = 0.0
        max_mitigation = 0.95  # Maximum 95% mitigation
        tolerance = 0.001
        max_iterations = 50

        for _ in range(max_iterations):
            mid_mitigation = (min_mitigation + max_mitigation) / 2.0

            # Calculate CS with this mitigation level
            result = self.calculate_capital_surplus_from_risks(
                physical_risk,
                transition_risk,
                concentration_risk,
                scr_score,
                mid_mitigation,
                climate_lambda,
                confidence_level,
            )

            current_cs = result.capital_surplus

            if abs(current_cs - target_capital_surplus) < tolerance:
                break
            elif current_cs > target_capital_surplus:
                min_mitigation = mid_mitigation
            else:
                max_mitigation = mid_mitigation

        required_mitigation = (min_mitigation + max_mitigation) / 2.0

        # Calculate the resulting CS with required mitigation
        optimized_result = calculate_capital_surplus_from_risks(
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=concentration_risk,
            scr_score=scr_score,
            mitigation_effect=required_mitigation,
            climate_lambda=climate_lambda,
            confidence_level=confidence_level,
        )

        return {
            "required_mitigation_level": required_mitigation,
            "achieved_capital_surplus": optimized_result.capital_surplus,
            "target_capital_surplus": target_capital_surplus,
            "difference": abs(
                optimized_result.capital_surplus - target_capital_surplus
            ),
            "confidence_level_used": confidence_level,
            "climate_lambda_used": (
                climate_lambda
                if climate_lambda is not None
                else self.default_climate_lambda
            ),
            "expected_loss_with_optimization": optimized_result.expected_loss,
            "variance_with_optimization": optimized_result.variance_loss,
            "optimization_success": abs(
                optimized_result.capital_surplus - target_capital_surplus
            )
            < tolerance,
        }


# Global instance
cs_calculator = CapitalSurplusCalculator()


def calculate_capital_surplus_from_risks(
    physical_risk: float,
    transition_risk: float,
    concentration_risk: float,
    scr_score: float,
    mitigation_effect: float = 0.0,
    climate_lambda: Optional[float] = None,
    confidence_level: float = 0.95,
) -> CapitalSurplusResult:
    """Convenience function to calculate capital surplus from risk components"""
    return cs_calculator.calculate_capital_surplus_from_risks(
        physical_risk,
        transition_risk,
        concentration_risk,
        scr_score,
        mitigation_effect,
        climate_lambda,
        confidence_level,
    )


def calculate_portfolio_capital_surplus(
    portfolio_risks: List[Dict[str, float]],
    portfolio_scr_scores: List[float],
    portfolio_mitigation_effects: List[float],
    portfolio_weights: Optional[List[float]] = None,
    climate_lambda: Optional[float] = None,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """Convenience function to calculate portfolio capital surplus"""
    return cs_calculator.calculate_portfolio_capital_surplus(
        portfolio_risks,
        portfolio_scr_scores,
        portfolio_mitigation_effects,
        portfolio_weights,
        climate_lambda,
        confidence_level,
    )


def optimize_capital_efficiency(
    target_capital_surplus: float,
    physical_risk: float,
    transition_risk: float,
    concentration_risk: float,
    scr_score: float,
    climate_lambda: Optional[float] = None,
    confidence_level: float = 0.95,
) -> Dict[str, float]:
    """Convenience function to optimize capital efficiency"""
    return cs_calculator.optimize_capital_efficiency(
        target_capital_surplus,
        physical_risk,
        transition_risk,
        concentration_risk,
        scr_score,
        climate_lambda,
        confidence_level,
    )

"""
Investment Return Calculation Service
Implements: TR = E[Retorno_investimento] × f_tempo_apólice

Where:
- E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]
- w_rf = 60% (seguro climático exige segurança)
- r_f = Selic - inflação = 3% a.a. (real)
- w_eq = 25% → E[r_eq] = 8% a.a. (real)
- w_infra = 15% → E[r_infra] = 6% a.a. (infraestrutura resiliente)
- TR_ajustado = TR × (1 - 0.3·SCR/1000) [reduz exposição a ativos de risco conforme SCR sobe]

Based on: Climate-Adjusted Investment Return Framework for Insurance Portfolios
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PolicyInvestmentProfile:
    """Information about investment profile for an insurance policy"""

    policy_id: str
    premium_issued: float  # Prêmio_emitido
    processing_method: str = "automated"  # "automated" or "manual"
    risk_category: str = "standard"  # "low", "standard", "high", "special"
    coverage_type: str = "property"  # "property", "liability", "vehicle", etc.
    policy_term_months: int = 12  # Policy term in months
    initial_investment: float = 100000.0  # Initial investment amount
    scr_score: float = 0.0  # Current SCR score
    climate_resilience_score: float = 0.5  # Climate resilience score (0-1)


@dataclass
class InvestmentReturnResult:
    """Result of investment return calculation"""

    total_return: float  # TR value (before adjustment)
    adjusted_return: float  # TR_ajustado (after adjustment for risk)
    expected_return_rate: float  # E[Retorno_investimento] rate
    time_factor: float  # f_tempo_apólice
    portfolio_composition: Dict[str, float]  # Portfolio weights and returns
    risk_adjustment_factor: float  # Factor (1 - 0.3·SCR/1000)
    scr_score: float  # Input SCR score
    climate_resilience_factor: float  # Climate resilience adjustment
    calculation_method: str
    calculation_timestamp: datetime


@dataclass
class InvestmentPortfolioAnalysis:
    """Result of portfolio-level investment return analysis"""

    total_premium_issued: float
    total_expected_returns: float
    total_adjusted_returns: float
    average_return_ratio: float
    portfolio_size: int
    risk_adjusted_return_ratio: float
    portfolio_risk_metrics: Dict[str, float]  # Portfolio-level risk metrics
    calculation_timestamp: datetime


class InvestmentReturnService:
    """
    Calculator for investment returns using the specified formula:
    TR = E[Retorno_investimento] × f_tempo_apólice
    Where E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]
    With adjustment: TR_ajustado = TR × (1 - 0.3·SCR/1000)
    """

    def __init__(self):
        # Fixed portfolio weights according to specification
        self.rf_weight = 0.60  # 60% risk-free assets (seguro climático exige segurança)
        self.eq_weight = 0.25  # 25% equity assets (E[r_eq] = 8%)
        self.infra_weight = 0.15  # 15% infrastructure assets (E[r_infra] = 6%)

        # Fixed return rates according to specification
        self.rf_return = 0.03  # 3% real return for risk-free (Selic - inflation)
        self.eq_return = 0.08  # 8% real return for equity
        self.infra_return = 0.06  # 6% real return for infrastructure assets

        # Risk adjustment parameters
        self.risk_adjustment_coefficient = 0.3  # Coefficient in the adjustment formula

        # Time factor parameters
        self.base_time_factor = 1.0  # Base factor for time calculation

        # Climate resilience impact
        self.climate_resilience_impact = (
            0.1  # How climate resilience affects investment returns
        )

        # Validate weights sum to 1.0
        total_weight = self.rf_weight + self.eq_weight + self.infra_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Portfolio weights must sum to 1.0, got {total_weight}")

    def calculate_expected_return_rate(self) -> float:
        """
        Calculate expected return rate:
        E[Retorno] = w_rf·r_f + w_eq·E[r_eq] + w_infra·E[r_infra]

        Returns:
            Expected return rate (E[Retorno_investimento])
        """
        expected_return_rate = (
            self.rf_weight * self.rf_return
            + self.eq_weight * self.eq_return
            + self.infra_weight * self.infra_return
        )

        return expected_return_rate

    def calculate_time_factor(self, policy_term_months: int) -> float:
        """
        Calculate time factor f_tempo_apólice based on policy term

        Args:
            policy_term_months: Policy term in months

        Returns:
            Time factor f_tempo_apólice
        """
        # For insurance investment returns, this is based on compounding over the investment period
        # Using simple proportional factor with mild compound adjustment
        years = policy_term_months / 12.0

        # Compound growth factor: (1 + r)^t where r is the annual return rate and t is time in years
        # However, for our specific formula, f_tempo_apólice is a factor that scales the returns
        # Using a simple linear scaling factor based on time
        time_factor = self.base_time_factor * (
            1 + 0.02 * years
        )  # 2% per year time factor

        return time_factor

    def calculate_risk_adjustment_factor(self, scr_score: float) -> float:
        """
        Calculate risk adjustment factor: (1 - 0.3·SCR/1000)

        Args:
            scr_score: Current SCR score

        Returns:
            Risk adjustment factor between 0 and 1
        """
        # Apply the specified formula: (1 - 0.3·SCR/1000)
        risk_adjustment = (self.risk_adjustment_coefficient * scr_score) / 1000.0
        adjustment_factor = 1.0 - risk_adjustment

        # Ensure the adjustment factor is between 0 and 1 (no negative returns)
        return max(0.0, min(1.0, adjustment_factor))

    def calculate_investment_return(
        self, policy_profile: PolicyInvestmentProfile
    ) -> InvestmentReturnResult:
        """
        Calculate investment return with risk adjustment using the specified formulas

        Args:
            policy_profile: Investment profile for the policy

        Returns:
            InvestmentReturnResult with complete calculation
        """
        # Calculate expected return rate
        expected_return_rate = self.calculate_expected_return_rate()

        # Calculate time factor
        time_factor = self.calculate_time_factor(policy_profile.policy_term_months)

        # Calculate base total return before adjustment
        # TR = E[Retorno_investimento] × f_tempo_apólice
        total_return = (
            policy_profile.initial_investment * expected_return_rate * time_factor
        )

        # Calculate risk adjustment factor
        risk_adjustment_factor = self.calculate_risk_adjustment_factor(
            policy_profile.scr_score
        )

        # Apply climate resilience adjustment
        # Higher climate resilience means less risk adjustment, so less reduction in returns
        climate_resilience_factor = 1.0 - (
            self.climate_resilience_impact
            * (1.0 - policy_profile.climate_resilience_score)
        )

        # Calculate adjusted return with both risk and climate resilience factors
        adjusted_return = (
            total_return * risk_adjustment_factor * climate_resilience_factor
        )

        # Portfolio composition breakdown
        portfolio_composition = {
            "risk_free_weight": self.rf_weight,
            "equity_weight": self.eq_weight,
            "infrastructure_weight": self.infra_weight,
            "risk_free_return": self.rf_return,
            "equity_return": self.eq_return,
            "infrastructure_return": self.infra_return,
            "expected_return_rate": expected_return_rate,
            "time_factor_applied": time_factor,
        }

        return InvestmentReturnResult(
            total_return=total_return,
            adjusted_return=adjusted_return,
            expected_return_rate=expected_return_rate,
            time_factor=time_factor,
            portfolio_composition=portfolio_composition,
            risk_adjustment_factor=risk_adjustment_factor,
            scr_score=policy_profile.scr_score,
            climate_resilience_factor=climate_resilience_factor,
            calculation_method="climate_adapted_portfolio_return",
            calculation_timestamp=datetime.now(),
        )

    def calculate_portfolio_investment_analysis(
        self, policies: List[PolicyInvestmentProfile]
    ) -> InvestmentPortfolioAnalysis:
        """
        Calculate investment return analysis for a portfolio of policies

        Args:
            policies: List of policy investment profiles

        Returns:
            InvestmentPortfolioAnalysis with portfolio-level metrics
        """
        if not policies:
            return InvestmentPortfolioAnalysis(
                total_premium_issued=0.0,
                total_expected_returns=0.0,
                total_adjusted_returns=0.0,
                average_return_ratio=0.0,
                portfolio_size=0,
                risk_adjusted_return_ratio=0.0,
                portfolio_risk_metrics={},
                calculation_timestamp=datetime.now(),
            )

        total_premium = 0.0
        total_expected_returns = 0.0
        total_adjusted_returns = 0.0
        total_scr = 0.0

        for policy in policies:
            result = self.calculate_investment_return(policy)
            total_premium += policy.premium_issued
            total_expected_returns += result.total_return
            total_adjusted_returns += result.adjusted_return
            total_scr += policy.scr_score

        # Calculate portfolio-level metrics
        average_return_ratio = (
            (total_expected_returns / total_premium) if total_premium > 0 else 0.0
        )
        risk_adjusted_return_ratio = (
            (total_adjusted_returns / total_premium) if total_premium > 0 else 0.0
        )
        average_scr = total_scr / len(policies) if policies else 0.0

        # Calculate portfolio risk metrics
        portfolio_risk_metrics = {
            "total_premium_issued": total_premium,
            "total_expected_returns": total_expected_returns,
            "total_adjusted_returns": total_adjusted_returns,
            "average_scr": average_scr,
            "portfolio_return_efficiency": (
                total_adjusted_returns / (average_scr + 1) if average_scr >= 0 else 0
            ),  # Avoid division issues
            "investment_concentration": len(policies) if total_premium > 0 else 0,
        }

        return InvestmentPortfolioAnalysis(
            total_premium_issued=total_premium,
            total_expected_returns=total_expected_returns,
            total_adjusted_returns=total_adjusted_returns,
            average_return_ratio=average_return_ratio,
            portfolio_size=len(policies),
            risk_adjusted_return_ratio=risk_adjusted_return_ratio,
            portfolio_risk_metrics=portfolio_risk_metrics,
            calculation_timestamp=datetime.now(),
        )

    def calculate_return_sensitivity(
        self, policy_profile: PolicyInvestmentProfile, scr_scenarios: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate return sensitivity to different SCR scenarios

        Args:
            policy_profile: Investment profile for the policy
            scr_scenarios: List of SCR scenarios to evaluate

        Returns:
            Dictionary with sensitivity analysis results
        """
        sensitivity_results = {}

        base_result = self.calculate_investment_return(policy_profile)

        for scr in scr_scenarios:
            # Create a temporary profile with modified SCR
            temp_profile = PolicyInvestmentProfile(
                policy_id=policy_profile.policy_id,
                premium_issued=policy_profile.premium_issued,
                processing_method=policy_profile.processing_method,
                risk_category=policy_profile.risk_category,
                coverage_type=policy_profile.coverage_type,
                policy_term_months=policy_profile.policy_term_months,
                initial_investment=policy_profile.initial_investment,
                scr_score=scr,
                climate_resilience_score=policy_profile.climate_resilience_score,
            )

            result = self.calculate_investment_return(temp_profile)
            sensitivity_results[scr] = {
                "adjusted_return": result.adjusted_return,
                "total_return": result.total_return,
                "risk_adjustment_factor": result.risk_adjustment_factor,
                "change_from_baseline": result.adjusted_return
                - base_result.adjusted_return,
                "change_percentage": (
                    (
                        (result.adjusted_return - base_result.adjusted_return)
                        / base_result.adjusted_return
                        * 100
                    )
                    if base_result.adjusted_return != 0
                    else 0
                ),
            }

        return {
            "baseline_scr": policy_profile.scr_score,
            "baseline_return": base_result.adjusted_return,
            "sensitivity_analysis": sensitivity_results,
            "profile": {
                "policy_id": policy_profile.policy_id,
                "initial_investment": policy_profile.initial_investment,
                "policy_term_months": policy_profile.policy_term_months,
                "climate_resilience_score": policy_profile.climate_resilience_score,
            },
            "calculation_timestamp": datetime.now().isoformat(),
        }

    def optimize_portfolio_allocation(
        self,
        scr_score: float,
        climate_resilience_target: float = 0.7,
        target_return: float = 0.055,
    ) -> Dict[str, Any]:
        """
        Optimize portfolio allocation based on SCR and climate resilience requirements

        Args:
            scr_score: Current SCR score
            climate_resilience_target: Target climate resilience (0-1)
            target_return: Target return rate

        Returns:
            Optimized portfolio allocation weights
        """
        # Start with base weights
        base_rf_weight = self.rf_weight
        base_eq_weight = self.eq_weight
        base_infra_weight = self.infra_weight

        # Adjust infrastructure allocation based on climate resilience target
        # Higher climate resilience target increases infrastructure allocation
        infra_adjustment = (
            climate_resilience_target - 0.5
        ) * 0.3  # Up to ±15% adjustment
        adjusted_infra = min(0.3, max(0.05, base_infra_weight + infra_adjustment))

        # If SCR is high, increase risk-free allocation to reduce portfolio risk
        # SCR adjustment: for every 200 points of SCR above 400, increase risk-free by 5%
        scr_adjustment = max(0, (scr_score - 400) / 200) * 0.05
        adjusted_rf = min(0.8, base_rf_weight + scr_adjustment)  # Cap at 80% risk-free

        # Remaining goes to equity
        adjusted_eq = 1.0 - adjusted_rf - adjusted_infra

        # Normalize to ensure they sum to 1.0 if needed
        total = adjusted_rf + adjusted_eq + adjusted_infra
        if not abs(total - 1.0) < 0.001:
            adjusted_rf /= total
            adjusted_eq /= total
            adjusted_infra /= total

        # Calculate return with new allocation
        expected_return = (
            adjusted_rf * self.rf_return
            + adjusted_eq * self.eq_return
            + adjusted_infra * self.infra_return
        )

        # Calculate risk-adjusted return
        risk_factor = self.calculate_risk_adjustment_factor(scr_score)
        risk_adjusted_return = expected_return * risk_factor

        return {
            "recommended_allocation": {
                "risk_free_weight": adjusted_rf,
                "equity_weight": adjusted_eq,
                "infrastructure_weight": adjusted_infra,
            },
            "expected_return_rate": expected_return,
            "risk_adjustment_factor": risk_factor,
            "risk_adjusted_return_rate": risk_adjusted_return,
            "input_parameters": {
                "scr_score": scr_score,
                "climate_resilience_target": climate_resilience_target,
                "target_return": target_return,
            },
            "recommendations": [
                (
                    f"Risk-free allocation: {adjusted_rf:.1%}"
                    if adjusted_rf > base_rf_weight
                    else f"Maintain current risk-free allocation: {adjusted_rf:.1%}"
                ),
                (
                    f"Increase infrastructure allocation to {adjusted_infra:.1%} for better climate resilience"
                    if adjusted_infra > base_infra_weight
                    else f"Maintain current infrastructure allocation: {adjusted_infra:.1%}"
                ),
                (
                    f"Equity allocation adjusted to {adjusted_eq:.1%}"
                    if abs(adjusted_eq - base_eq_weight) > 0.01
                    else f"Maintain current equity allocation: {adjusted_eq:.1%}"
                ),
            ],
        }


# Global instance
investment_return_service = InvestmentReturnService()


def calculate_investment_return(
    policy_profile: PolicyInvestmentProfile,
) -> InvestmentReturnResult:
    """Convenience function to calculate investment return"""
    return investment_return_service.calculate_investment_return(policy_profile)


def calculate_expected_return_rate() -> float:
    """Convenience function to calculate expected return rate"""
    return investment_return_service.calculate_expected_return_rate()


def calculate_portfolio_investment_analysis(
    policies: List[PolicyInvestmentProfile],
) -> InvestmentPortfolioAnalysis:
    """Convenience function to calculate portfolio investment analysis"""
    return investment_return_service.calculate_portfolio_investment_analysis(policies)


def calculate_return_sensitivity(
    policy_profile: PolicyInvestmentProfile, scr_scenarios: List[float]
) -> Dict[str, Any]:
    """Convenience function to calculate return sensitivity analysis"""
    return investment_return_service.calculate_return_sensitivity(
        policy_profile, scr_scenarios
    )


def optimize_portfolio_allocation(
    scr_score: float,
    climate_resilience_target: float = 0.7,
    target_return: float = 0.055,
) -> Dict[str, Any]:
    """Convenience function to optimize portfolio allocation"""
    return investment_return_service.optimize_portfolio_allocation(
        scr_score, climate_resilience_target, target_return
    )

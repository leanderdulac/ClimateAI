"""
Loading Margin (ML) Calculation Service
Implements: ML = ROE_target × Capital_alocado / Volume_prêmios

Where:
- ROE_target = 18% a.a. (conservative assumption for climate risk)
- Capital_alocado = Exp_o × SCR × fator_ponderador_RBC
- fator_ponderador_RBC = 1.0 if SCR < 300, 1.5 if 300 ≤ SCR < 600, 2.5 if 600 ≤ SCR < 800, 4.0 if SCR ≥ 800

Based on: Risk-Based Capital (RBC) Framework for Climate Insurance
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LoadingMarginResult:
    """Result of Loading Margin calculation"""

    loading_margin: float
    roe_target: float
    allocated_capital: float
    premium_volume: float
    scr_score: float
    rbc_weight_factor: float
    exposure_value: float
    calculation_method: str
    calculation_timestamp: datetime


@dataclass
class PolicyLoadingInfo:
    """Information about individual policy loading calculation"""

    policy_id: str
    exposure_value: float
    final_scr_score: float
    rbc_weight_factor: float
    allocated_capital: float
    premium_amount: float
    calculated_loading_margin: float
    risk_category: str  # Based on SCR score


@dataclass
class PortfolioLoadingAnalysis:
    """Analysis of loading margins at portfolio level"""

    portfolio_loading_margin: float
    portfolio_roe_target: float
    total_allocated_capital: float
    total_premium_volume: float
    average_scr_score: float
    risk_distribution: Dict[str, int]  # Count of policies in each risk category
    portfolio_size: int
    capital_efficiency_ratio: float
    loading_margin_breakdown: Dict[str, float]
    calculation_timestamp: datetime


@dataclass
class RiskBasedCapitalFactors:
    """
    Risk-based capital factors for different SCR ranges
    Based on regulatory frameworks that penalize higher risk portfolios
    """

    low_risk_threshold: float = 300.0
    medium_risk_threshold: float = 600.0
    high_risk_threshold: float = 800.0
    critical_risk_threshold: float = float("inf")

    # Capital factor multipliers
    low_risk_factor: float = 1.0  # No penalty for low risk
    medium_risk_factor: float = 1.5  # Moderate penalty for medium risk
    high_risk_factor: float = 2.5  # Significant penalty for high risk
    critical_risk_factor: float = 4.0  # Heavy penalty for critical risk


class LoadingMarginCalculator:
    """
    Calculates Loading Margin using the specified formula:
    ML = ROE_target × Capital_alocado / Volume_prêmios
    Where Capital_alocado = Exp_o × SCR × fator_ponderador_RBC
    And fator_ponderador_RBC is determined by SCR score ranges
    """

    def __init__(self):
        # Conservative ROE target for climate risk
        self.roe_target = 0.18  # 18% annually

        # Risk-based capital factors
        self.rbc_factors = RiskBasedCapitalFactors()

        # SCR risk categories (using the same thresholds across the system)
        self.scr_risk_categories = {
            "low": (0, 300),
            "moderate": (300, 600),
            "high": (600, 800),
            "critical": (800, float("inf")),
        }

    def determine_rbc_weight_factor(self, scr_score: float) -> float:
        """
        Determine RBC weight factor based on SCR score:
        - 1.0 if SCR < 300
        - 1.5 if 300 ≤ SCR < 600
        - 2.5 if 600 ≤ SCR < 800
        - 4.0 if SCR ≥ 800

        Args:
            scr_score: Current SCR score

        Returns:
            RBC weight factor for the given SCR score
        """
        if scr_score < self.rbc_factors.low_risk_threshold:
            return self.rbc_factors.low_risk_factor
        elif scr_score < self.rbc_factors.medium_risk_threshold:
            return self.rbc_factors.medium_risk_factor
        elif scr_score < self.rbc_factors.high_risk_threshold:
            return self.rbc_factors.high_risk_factor
        else:
            return self.rbc_factors.critical_risk_factor

    def determine_risk_category(self, scr_score: float) -> str:
        """
        Determine risk category based on SCR score

        Args:
            scr_score: Current SCR score

        Returns:
            Risk category as string ('low', 'moderate', 'high', or 'critical')
        """
        if scr_score < self.rbc_factors.low_risk_threshold:
            return "low"
        elif scr_score < self.rbc_factors.medium_risk_threshold:
            return "moderate"
        elif scr_score < self.rbc_factors.high_risk_threshold:
            return "high"
        else:
            return "critical"

    def calculate_allocated_capital(
        self, exposure_value: float, scr_score: float
    ) -> Dict[str, float]:
        """
        Calculate allocated capital based on exposure, SCR score and RBC factor

        Args:
            exposure_value: Exposure value (Exp_o)
            scr_score: Current SCR score

        Returns:
            Dictionary with allocated capital and components
        """
        # Determine RBC weight factor based on SCR score
        rbc_weight_factor = self.determine_rbc_weight_factor(scr_score)

        # Calculate allocated capital
        allocated_capital = exposure_value * scr_score * rbc_weight_factor

        return {
            "allocated_capital": allocated_capital,
            "exposure_value": exposure_value,
            "scr_score": scr_score,
            "rbc_weight_factor": rbc_weight_factor,
            "capital_multiplier": scr_score * rbc_weight_factor,
            "risk_category": self.determine_risk_category(scr_score),
        }

    def calculate_loading_margin(
        self, exposure_value: float, scr_score: float, premium_volume: float
    ) -> LoadingMarginResult:
        """
        Calculate loading margin using the specified formula:
        ML = ROE_target × Capital_alocado / Volume_prêmios

        Args:
            exposure_value: Exposure value (Exp_o)
            scr_score: Current SCR score
            premium_volume: Total premium volume (Volume_prêmios)

        Returns:
            LoadingMarginResult with complete calculation
        """
        if premium_volume <= 0:
            raise ValueError("Premium volume must be positive")

        # Calculate allocated capital
        capital_details = self.calculate_allocated_capital(exposure_value, scr_score)

        # Calculate loading margin using the formula
        loading_margin = (
            self.roe_target * capital_details["allocated_capital"] / premium_volume
        )

        return LoadingMarginResult(
            loading_margin=loading_margin,
            roe_target=self.roe_target,
            allocated_capital=capital_details["allocated_capital"],
            premium_volume=premium_volume,
            scr_score=scr_score,
            rbc_weight_factor=capital_details["rbc_weight_factor"],
            exposure_value=exposure_value,
            calculation_method="risk_based_capital_framework",
            calculation_timestamp=datetime.now(),
        )

    def calculate_policy_loading_info(
        self, policy_exposure: float, policy_scr: float, policy_premium: float
    ) -> PolicyLoadingInfo:
        """
        Calculate loading margin for an individual policy

        Args:
            policy_exposure: Policy exposure value
            policy_scr: Policy's SCR score
            policy_premium: Policy premium amount

        Returns:
            PolicyLoadingInfo with policy-specific loading calculation
        """
        # Calculate RBC weight factor
        rbc_weight_factor = self.determine_rbc_weight_factor(policy_scr)

        # Calculate allocated capital for this policy
        allocated_capital = policy_exposure * policy_scr * rbc_weight_factor

        # Calculate loading margin for this policy
        # Note: For individual policy, we use portfolio premium volume for calculation
        # This is a simplified approach - could be enhanced with more sophisticated allocation methods
        if policy_premium > 0:
            # Assume this policy contributes proportionally to the portfolio
            # In practice, this would need to consider the policy's contribution to the portfolio's total capital requirement
            calculated_loading_margin = (
                self.roe_target * allocated_capital / policy_premium
            )
        else:
            calculated_loading_margin = 0.0

        return PolicyLoadingInfo(
            policy_id=f"POLICY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # Generate temporary ID
            exposure_value=policy_exposure,
            final_scr_score=policy_scr,
            rbc_weight_factor=rbc_weight_factor,
            allocated_capital=allocated_capital,
            premium_amount=policy_premium,
            calculated_loading_margin=calculated_loading_margin,
            risk_category=self.determine_risk_category(policy_scr),
        )

    def calculate_portfolio_loading_analysis(
        self, policies: List[Dict[str, float]], portfolio_premium: float
    ) -> PortfolioLoadingAnalysis:
        """
        Calculate loading margin analysis for a portfolio of policies

        Args:
            policies: List of policy dictionaries with 'exposure_value', 'scr_score', 'premium_amount'
            portfolio_premium: Total portfolio premium volume

        Returns:
            PortfolioLoadingAnalysis with comprehensive portfolio metrics
        """
        if not policies:
            return PortfolioLoadingAnalysis(
                portfolio_loading_margin=0.0,
                portfolio_roe_target=0.0,
                total_allocated_capital=0.0,
                total_premium_volume=portfolio_premium,
                average_scr_score=0.0,
                risk_distribution={},
                portfolio_size=0,
                capital_efficiency_ratio=0.0,
                loading_margin_breakdown={},
                calculation_timestamp=datetime.now(),
            )

        total_allocated_capital = 0.0
        total_exposure = 0.0
        total_scr_weight = 0.0
        risk_distribution = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
        policy_loadings = []

        for policy in policies:
            exposure_value = policy.get("exposure_value", 0.0)
            scr_score = policy.get("scr_score", 0.0)
            premium_amount = policy.get("premium_amount", 0.0)

            # Calculate capital allocation for this policy
            capital_details = self.calculate_allocated_capital(
                exposure_value, scr_score
            )
            total_allocated_capital += capital_details["allocated_capital"]
            total_exposure += exposure_value
            total_scr_weight += scr_score * exposure_value  # Weighted average

            # Track risk distribution
            risk_category = capital_details["risk_category"]
            risk_distribution[risk_category] += 1

            # Calculate individual policy loading
            if portfolio_premium > 0:
                policy_loading = (
                    self.roe_target
                    * capital_details["allocated_capital"]
                    / portfolio_premium
                )
            else:
                policy_loading = 0.0

            policy_loadings.append(policy_loading)

        # Calculate average SCR weighted by exposure
        if total_exposure > 0:
            average_scr_score = total_scr_weight / total_exposure
        else:
            average_scr_score = 0.0

        # Calculate portfolio loading margin
        if portfolio_premium > 0:
            portfolio_loading_margin = (
                self.roe_target * total_allocated_capital
            ) / portfolio_premium
        else:
            portfolio_loading_margin = 0.0

        # Calculate capital efficiency ratio (how much capital is needed relative to premium)
        capital_efficiency_ratio = (
            total_allocated_capital / portfolio_premium
            if portfolio_premium > 0
            else 0.0
        )

        # Calculate loading breakdown by risk category
        loading_breakdown = {}
        for category, count in risk_distribution.items():
            if count > 0:
                category_policies = [
                    p
                    for p in policies
                    if self.determine_risk_category(p.get("scr_score", 0)) == category
                ]
                category_capital = sum(
                    self.calculate_allocated_capital(
                        p.get("exposure_value", 0), p.get("scr_score", 0)
                    )["allocated_capital"]
                    for p in category_policies
                )
                category_loading = (
                    (self.roe_target * category_capital) / portfolio_premium
                    if portfolio_premium > 0
                    else 0
                )
                loading_breakdown[category] = category_loading

        return PortfolioLoadingAnalysis(
            portfolio_loading_margin=portfolio_loading_margin,
            portfolio_roe_target=self.roe_target,
            total_allocated_capital=total_allocated_capital,
            total_premium_volume=portfolio_premium,
            average_scr_score=average_scr_score,
            risk_distribution=risk_distribution,
            portfolio_size=len(policies),
            capital_efficiency_ratio=capital_efficiency_ratio,
            loading_margin_breakdown=loading_breakdown,
            calculation_timestamp=datetime.now(),
        )

    def calculate_risk_based_pricing_adjustment(
        self, base_premium: float, scr_score: float, exposure_value: float
    ) -> Dict[str, float]:
        """
        Calculate risk-based pricing adjustment based on capital requirements

        Args:
            base_premium: Base premium before risk adjustment
            scr_score: SCR score for the policy/risk
            exposure_value: Exposure value of the risk

        Returns:
            Dictionary with pricing adjustment information
        """
        # Calculate the allocated capital
        allocated_capital = self.calculate_allocated_capital(exposure_value, scr_score)

        # Calculate the required loading to meet ROE target
        required_loading = self.roe_target * allocated_capital["allocated_capital"]

        # Determine if this represents an adjustment to the base premium
        if base_premium > 0:
            loading_percentage = required_loading / base_premium
            adjusted_premium = base_premium + required_loading
        else:
            loading_percentage = 0.0
            adjusted_premium = required_loading

        return {
            "base_premium": base_premium,
            "required_loading": required_loading,
            "loading_percentage": loading_percentage,
            "adjusted_premium": adjusted_premium,
            "allocated_capital": allocated_capital["allocated_capital"],
            "rbc_weight_factor": allocated_capital["rbc_weight_factor"],
            "risk_category": allocated_capital["risk_category"],
            "scr_score": scr_score,
            "exposure_value": exposure_value,
        }

    def get_capital_efficiency_metrics(
        self, portfolio_policies: List[Dict[str, float]], total_portfolio_premium: float
    ) -> Dict[str, Any]:
        """
        Get comprehensive capital efficiency metrics for the portfolio

        Args:
            portfolio_policies: List of policies with risk data
            total_portfolio_premium: Total premium volume of the portfolio

        Returns:
            Dictionary with capital efficiency metrics
        """
        analysis = self.calculate_portfolio_loading_analysis(
            portfolio_policies, total_portfolio_premium
        )

        # Calculate additional efficiency metrics
        if analysis.total_premium_volume > 0:
            capital_intensity_ratio = (
                analysis.total_allocated_capital / analysis.total_premium_volume
            )
            risk_premium_ratio = (
                analysis.average_scr_score
                * analysis.portfolio_size
                / analysis.total_premium_volume
                if analysis.portfolio_size > 0
                else 0
            )
        else:
            capital_intensity_ratio = 0.0
            risk_premium_ratio = 0.0

        # Assess capital efficiency
        if capital_intensity_ratio < 0.1:
            efficiency_rating = "high"
        elif capital_intensity_ratio < 0.3:
            efficiency_rating = "medium"
        else:
            efficiency_rating = "low"

        # Calculate risk-adjusted return metrics
        potential_roe = (
            analysis.portfolio_loading_margin
        )  # Simplified as loading margin per premium unit

        return {
            "capital_intensity_ratio": capital_intensity_ratio,
            "risk_premium_ratio": risk_premium_ratio,
            "capital_efficiency_rating": efficiency_rating,
            "potential_roe": potential_roe,
            "total_allocated_capital": analysis.total_allocated_capital,
            "portfolio_loading_margin": analysis.portfolio_loading_margin,
            "average_scr_score": analysis.average_scr_score,
            "risk_distribution": analysis.risk_distribution,
            "portfolio_size": analysis.portfolio_size,
            "loading_margin_breakdown_by_risk": analysis.loading_margin_breakdown,
            "allocation_efficiency_score": 1.0
            / (1.0 + capital_intensity_ratio),  # Higher efficiency = lower ratio
            "recommendations": self._generate_efficiency_recommendations(
                analysis, capital_intensity_ratio
            ),
        }

    def _generate_efficiency_recommendations(
        self, analysis: PortfolioLoadingAnalysis, capital_intensity_ratio: float
    ) -> List[str]:
        """Generate recommendations for improving capital efficiency"""
        recommendations = []

        if analysis.average_scr_score > 600:
            recommendations.append(
                "Portfolio has high average risk scores - consider risk mitigation programs"
            )

        if (
            analysis.risk_distribution.get("critical", 0) / analysis.portfolio_size
            > 0.1
        ):
            recommendations.append(
                "High concentration of critical risk policies - diversify risk exposure"
            )

        if analysis.risk_distribution.get("low", 0) / analysis.portfolio_size < 0.2:
            recommendations.append(
                "Low risk policy share is insufficient - consider expanding in lower risk segments"
            )

        if capital_intensity_ratio > 0.3:
            recommendations.append(
                "Capital intensity is high - review allocation methodology and consider reinsurance"
            )
        elif capital_intensity_ratio < 0.05:
            recommendations.append(
                "Capital intensity is very low - ensure adequate coverage for high-risk scenarios"
            )

        # Check if loading margins are appropriately distributed across risk categories
        if (
            analysis.loading_margin_breakdown.get("critical", 0) == 0
            and analysis.risk_distribution.get("critical", 0) > 0
        ):
            recommendations.append(
                "Critical risk policies may not have adequate loading margins applied"
            )

        if not recommendations:
            recommendations.append("Portfolio capital efficiency appears well-balanced")

        return recommendations


# Global instance
loading_margin_service = LoadingMarginCalculator()


def calculate_loading_margin(
    exposure_value: float, scr_score: float, premium_volume: float
) -> LoadingMarginResult:
    """Convenience function to calculate loading margin"""
    return loading_margin_service.calculate_loading_margin(
        exposure_value, scr_score, premium_volume
    )


def calculate_policy_loading_info(
    policy_exposure: float, policy_scr: float, policy_premium: float
) -> PolicyLoadingInfo:
    """Convenience function to calculate policy loading information"""
    return loading_margin_service.calculate_policy_loading_info(
        policy_exposure, policy_scr, policy_premium
    )


def calculate_portfolio_loading_analysis(
    policies: List[Dict[str, float]], portfolio_premium: float
) -> PortfolioLoadingAnalysis:
    """Convenience function to calculate portfolio loading analysis"""
    return loading_margin_service.calculate_portfolio_loading_analysis(
        policies, portfolio_premium
    )


def calculate_risk_based_pricing_adjustment(
    base_premium: float, scr_score: float, exposure_value: float
) -> Dict[str, float]:
    """Convenience function to calculate risk-based pricing adjustment"""
    return loading_margin_service.calculate_risk_based_pricing_adjustment(
        base_premium, scr_score, exposure_value
    )


def get_capital_efficiency_metrics(
    portfolio_policies: List[Dict[str, float]], total_portfolio_premium: float
) -> Dict[str, Any]:
    """Convenience function to get capital efficiency metrics"""
    return loading_margin_service.get_capital_efficiency_metrics(
        portfolio_policies, total_portfolio_premium
    )

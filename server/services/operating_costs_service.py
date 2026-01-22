"""
Operating Costs (CO) Calculation Service
Implements: CO = (Custo_subscrição + Custo_sinistros + Custo_admin) / Prêmio_emitido

Where:
- Custo_subscrição = R$ 150 per policy (automated) or R$ 450 (manual)
- Custo_sinistros = 0.08 × Prêmio (for fraud detection, processing)
- Custo_admin = 0.12 × Prêmio (for technology, compliance)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PolicyDetails:
    """Information about an insurance policy"""

    policy_id: str
    premium_issued: float  # Prêmio_emitido
    processing_method: str = "automated"  # "automated" or "manual"
    risk_category: str = "standard"  # "low", "standard", "high", "special"
    coverage_type: str = "property"  # "property", "liability", "vehicle", etc.
    policy_age_months: int = 0  # Months since issuance
    claim_history_count: int = 0  # Number of past claims
    automated_processing_enabled: bool = True


@dataclass
class OperatingCostResult:
    """Result of Operating Costs calculation"""

    operating_cost_ratio: float  # CO value (cost ratio to premium)
    subscription_cost: float  # Custo_subscrição component
    claims_cost: float  # Custo_sinistros component
    admin_cost: float  # Custo_admin component
    premium_issued: float  # Prêmio_emitido
    processing_method: str  # Processing method used
    risk_category: str  # Risk category
    cost_breakdown: Dict[str, float]  # Detailed cost breakdown
    calculation_timestamp: datetime


@dataclass
class PortfolioOperatingCosts:
    """Result of portfolio-level operating costs"""

    total_premium_issued: float
    total_subscription_costs: float
    total_claims_processing_costs: float
    total_administration_costs: float
    average_operating_cost_ratio: float
    policy_count: int
    portfolio_cost_breakdown: Dict[str, float]
    calculation_timestamp: datetime


class OperatingCostsService:
    """
    Calculator for Operating Costs (CO) using the specified formula:
    CO = (Custo_subscrição + Custo_sinistros + Custo_admin) / Prêmio_emitido
    """

    def __init__(self):
        # Cost parameters
        self.subscription_cost_automated = 150.0  # R$ 150 per policy (automated)
        self.subscription_cost_manual = 450.0  # R$ 450 per policy (manual)

        # Percentage-based costs
        self.claims_processing_rate = 0.08  # 8% of premium for claims processing
        self.administrative_rate = 0.12  # 12% of premium for administration

        # Risk category multipliers (adjust costs based on risk level)
        self.risk_category_multipliers = {
            "low": 0.8,  # Lower costs for low-risk policies
            "standard": 1.0,  # Standard costs
            "high": 1.2,  # Higher costs for high-risk policies
            "special": 1.5,  # Highest costs for special risk policies
        }

        # Coverage type multipliers
        self.coverage_type_multipliers = {
            "property": 1.0,  # Standard for property insurance
            "liability": 1.1,  # Slightly higher for liability due to legal complexities
            "vehicle": 0.95,  # Slightly lower for vehicle due to automation
            "agricultural": 1.05,  # Slightly higher for agricultural due to climate dependency
            "marine": 1.2,  # Higher for marine due to complexity
            "aviation": 1.3,  # Highest for aviation due to specialist requirements
        }

        # Age-based cost adjustments (older policies may have different processing costs)
        self.age_cost_adjustments = {
            "new": (0, 6),  # 0-6 months: higher costs due to setup
            "mature": (6, 24),  # 6-24 months: standard costs
            "senior": (24, 120),  # 2+ years: potentially different costs
        }

        # Adjustment factors for efficiency improvements
        self.efficiency_improvement_factor = 0.95  # 5% efficiency gain over time

    def calculate_operating_costs(
        self, policy_details: PolicyDetails
    ) -> OperatingCostResult:
        """
        Calculate operating costs for a single policy using the formula:
        CO = (Custo_subscrição + Custo_sinistros + Custo_admin) / Prêmio_emitido

        Args:
            policy_details: Details about the policy to calculate costs for

        Returns:
            OperatingCostResult with complete cost calculation breakdown
        """
        premium_issued = policy_details.premium_issued

        # Calculate subscription cost (Custo_subscrição)
        if policy_details.processing_method.lower() == "manual":
            subscription_cost = self.subscription_cost_manual
        else:
            subscription_cost = self.subscription_cost_automated

        # Apply risk category multiplier
        risk_multiplier = self.risk_category_multipliers.get(
            policy_details.risk_category.lower(),
            self.risk_category_multipliers.get("standard", 1.0),
        )
        subscription_cost *= risk_multiplier

        # Apply coverage type multiplier
        coverage_multiplier = self.coverage_type_multipliers.get(
            policy_details.coverage_type.lower(),
            self.coverage_type_multipliers.get("property", 1.0),
        )
        subscription_cost *= coverage_multiplier

        # Apply age-based adjustment
        if policy_details.policy_age_months <= 6:  # New policy
            subscription_cost *= 1.1  # 10% higher for newer policies
        elif policy_details.policy_age_months > 24:  # Senior policy
            subscription_cost *= 0.95  # 5% lower for mature policies

        # Calculate claims processing cost (Custo_sinistros)
        claims_cost = self.claims_processing_rate * premium_issued

        # Add additional claims cost if there are past claims
        if policy_details.claim_history_count > 0:
            # Higher claim processing costs for policies with history of claims
            additional_claim_cost = (
                policy_details.claim_history_count * 50
            )  # R$ 50 per previous claim
            claims_cost += additional_claim_cost

        # Calculate administrative cost (Custo_admin)
        admin_cost = self.administrative_rate * premium_issued

        # Apply administrative cost adjustments based on risk category
        admin_cost *= risk_multiplier

        # Apply efficiency improvements
        subscription_cost *= self.efficiency_improvement_factor
        claims_cost *= self.efficiency_improvement_factor
        admin_cost *= self.efficiency_improvement_factor

        # Calculate total operating costs
        total_operating_costs = subscription_cost + claims_cost + admin_cost

        # Calculate operating cost ratio (CO)
        if premium_issued > 0:
            operating_cost_ratio = total_operating_costs / premium_issued
        else:
            operating_cost_ratio = 0.0  # Avoid division by zero

        # Prepare cost breakdown
        cost_breakdown = {
            "subscription_cost_base": (
                self.subscription_cost_automated
                if policy_details.processing_method.lower() == "automated"
                else self.subscription_cost_manual
            ),
            "risk_category_multiplier": risk_multiplier,
            "coverage_type_multiplier": coverage_multiplier,
            "age_adjustment": policy_details.policy_age_months,
            "claim_history_factor": policy_details.claim_history_count,
            "efficiency_adjustment": self.efficiency_improvement_factor,
        }

        return OperatingCostResult(
            operating_cost_ratio=operating_cost_ratio,
            subscription_cost=subscription_cost,
            claims_cost=claims_cost,
            admin_cost=admin_cost,
            premium_issued=premium_issued,
            processing_method=policy_details.processing_method,
            risk_category=policy_details.risk_category,
            cost_breakdown=cost_breakdown,
            calculation_timestamp=datetime.now(),
        )

    def calculate_portfolio_operating_costs(
        self, policies: List[PolicyDetails]
    ) -> PortfolioOperatingCosts:
        """
        Calculate operating costs for a portfolio of policies

        Args:
            policies: List of policy details for the portfolio

        Returns:
            PortfolioOperatingCosts with aggregated cost information
        """
        if not policies:
            return PortfolioOperatingCosts(
                total_premium_issued=0.0,
                total_subscription_costs=0.0,
                total_claims_processing_costs=0.0,
                total_administration_costs=0.0,
                average_operating_cost_ratio=0.0,
                policy_count=0,
                portfolio_cost_breakdown={},
                calculation_timestamp=datetime.now(),
            )

        total_premium = 0.0
        total_subscription_costs = 0.0
        total_claims_costs = 0.0
        total_admin_costs = 0.0

        for policy in policies:
            result = self.calculate_operating_costs(policy)
            total_premium += result.premium_issued
            total_subscription_costs += result.subscription_cost
            total_claims_costs += result.claims_cost
            total_admin_costs += result.admin_cost

        # Calculate average operating cost ratio
        if total_premium > 0:
            average_operating_cost_ratio = (
                total_subscription_costs + total_claims_costs + total_admin_costs
            ) / total_premium
        else:
            average_operating_cost_ratio = 0.0

        # Portfolio-level cost breakdown
        portfolio_cost_breakdown = {
            "total_subscription_percentage": (
                (total_subscription_costs / total_premium * 100)
                if total_premium > 0
                else 0
            ),
            "total_claims_percentage": (
                (total_claims_costs / total_premium * 100) if total_premium > 0 else 0
            ),
            "total_admin_percentage": (
                (total_admin_costs / total_premium * 100) if total_premium > 0 else 0
            ),
            "cost_ratio_by_risk_category": self._calculate_cost_ratios_by_risk_category(
                policies
            ),
            "cost_ratio_by_coverage_type": self._calculate_cost_ratios_by_coverage_type(
                policies
            ),
        }

        return PortfolioOperatingCosts(
            total_premium_issued=total_premium,
            total_subscription_costs=total_subscription_costs,
            total_claims_processing_costs=total_claims_costs,
            total_administration_costs=total_admin_costs,
            average_operating_cost_ratio=average_operating_cost_ratio,
            policy_count=len(policies),
            portfolio_cost_breakdown=portfolio_cost_breakdown,
            calculation_timestamp=datetime.now(),
        )

    def _calculate_cost_ratios_by_risk_category(
        self, policies: List[PolicyDetails]
    ) -> Dict[str, float]:
        """Calculate average cost ratios grouped by risk category"""
        category_totals = {}

        for policy in policies:
            category = policy.risk_category
            if category not in category_totals:
                category_totals[category] = {"premium": 0.0, "costs": 0.0}

            result = self.calculate_operating_costs(policy)
            category_totals[category]["premium"] += result.premium_issued
            category_totals[category]["costs"] += (
                result.subscription_cost + result.claims_cost + result.admin_cost
            )

        return {
            category: (data["costs"] / data["premium"]) if data["premium"] > 0 else 0.0
            for category, data in category_totals.items()
        }

    def _calculate_cost_ratios_by_coverage_type(
        self, policies: List[PolicyDetails]
    ) -> Dict[str, float]:
        """Calculate average cost ratios grouped by coverage type"""
        type_totals = {}

        for policy in policies:
            coverage_type = policy.coverage_type
            if coverage_type not in type_totals:
                type_totals[coverage_type] = {"premium": 0.0, "costs": 0.0}

            result = self.calculate_operating_costs(policy)
            type_totals[coverage_type]["premium"] += result.premium_issued
            type_totals[coverage_type]["costs"] += (
                result.subscription_cost + result.claims_cost + result.admin_cost
            )

        return {
            coverage_type: (
                (data["costs"] / data["premium"]) if data["premium"] > 0 else 0.0
            )
            for coverage_type, data in type_totals.items()
        }

    def calculate_cost_efficiency_improvement(
        self,
        current_operating_cost: float,
        target_operating_cost: float,
        improvement_timeline_months: int = 12,
    ) -> Dict[str, Any]:
        """
        Calculate required improvements to achieve target operating cost ratio

        Args:
            current_operating_cost: Current operating cost ratio
            target_operating_cost: Target operating cost ratio
            improvement_timeline_months: Timeline in months to achieve target

        Returns:
            Dictionary with improvement recommendations and timeline
        """
        if current_operating_cost <= target_operating_cost:
            return {
                "status": "already_achieving_target",
                "current_operating_cost": current_operating_cost,
                "target_operating_cost": target_operating_cost,
                "improvement_needed": 0.0,
                "recommendations": ["Operating costs already meet target"],
                "timeline_months": improvement_timeline_months,
            }

        improvement_needed = current_operating_cost - target_operating_cost
        monthly_improvement_rate = improvement_needed / improvement_timeline_months

        recommendations = []

        # Suggest specific cost reduction measures
        if improvement_needed > 0.05:
            recommendations.append(
                "Automate underwriting processes to reduce subscription costs"
            )
            recommendations.append(
                "Implement AI-powered fraud detection for claims processing"
            )
            recommendations.append("Optimize administrative workflows and systems")
        elif improvement_needed > 0.02:
            recommendations.append(
                "Review manual processing protocols to increase automation"
            )
            recommendations.append(
                "Audit claims processing procedures for efficiency gains"
            )
            recommendations.append(
                "Evaluate administrative cost centers for optimization"
            )
        else:
            recommendations.append("Minor optimizations available in all cost centers")

        return {
            "status": "improvement_needed",
            "current_operating_cost": current_operating_cost,
            "target_operating_cost": target_operating_cost,
            "improvement_needed": improvement_needed,
            "monthly_improvement_rate": monthly_improvement_rate,
            "recommendations": recommendations,
            "timeline_months": improvement_timeline_months,
            "projected_operating_cost_after_improvement": current_operating_cost
            - improvement_needed,
        }

    def calculate_breakeven_premium(
        self, risk_assessment: Dict[str, float], target_operating_margin: float = 0.10
    ) -> float:
        """
        Calculate breakeven premium adjusting for operating costs

        Args:
            risk_assessment: Risk assessment with expected claims
            target_operating_margin: Target profit margin after operating costs

        Returns:
            Breakeven premium that covers claims, operating costs, and target margin
        """
        expected_claims = risk_assessment.get("expected_claims", 0.0)

        # Calculate minimum premium needed to cover claims and operating costs
        # If operating cost ratio is CO, then: Premium = Expected_Claims / (1 - CO - target_margin)
        # We'll use an estimated operating cost ratio based on typical values
        estimated_operating_cost_ratio = 0.25  # Typical 25% operating cost ratio

        total_required_ratio = estimated_operating_cost_ratio + target_operating_margin
        if total_required_ratio >= 1.0:
            # If operating costs + margin >= 100%, adjust to reasonable values
            estimated_operating_cost_ratio = 0.20  # Reduce to 20%
            total_required_ratio = (
                estimated_operating_cost_ratio + target_operating_margin
            )

        if (1 - total_required_ratio) > 0:
            breakeven_premium = expected_claims / (1 - total_required_ratio)
        else:
            # Fallback calculation if ratio is too high
            breakeven_premium = expected_claims * 1.5  # Simple 50% markup

        return breakeven_premium


# Global instance
operating_costs_service = OperatingCostsService()


def calculate_operating_costs(policy_details: PolicyDetails) -> OperatingCostResult:
    """Convenience function to calculate operating costs for a single policy"""
    return operating_costs_service.calculate_operating_costs(policy_details)


def calculate_portfolio_operating_costs(
    policies: List[PolicyDetails],
) -> PortfolioOperatingCosts:
    """Convenience function to calculate operating costs for a portfolio"""
    return operating_costs_service.calculate_portfolio_operating_costs(policies)


def calculate_cost_efficiency_improvement(
    current_operating_cost: float,
    target_operating_cost: float,
    improvement_timeline_months: int = 12,
) -> Dict[str, Any]:
    """Convenience function to calculate cost efficiency improvement plan"""
    return operating_costs_service.calculate_cost_efficiency_improvement(
        current_operating_cost, target_operating_cost, improvement_timeline_months
    )


def calculate_breakeven_premium(
    risk_assessment: Dict[str, float], target_operating_margin: float = 0.10
) -> float:
    """Convenience function to calculate breakeven premium with operating costs"""
    return operating_costs_service.calculate_breakeven_premium(
        risk_assessment, target_operating_margin
    )

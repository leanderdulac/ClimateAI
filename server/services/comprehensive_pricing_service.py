"""
Comprehensive Pricing Integration Service
Implements: Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda

Where:
- Ajuste_oferta_demanda = f(concentração_zoneamento, capacidade_retida)
- concentração_zoneamento = Σ_{apólices_na_ZCR} (Prêmio_i / Capital_livre)

If concentração > 25% → Ajuste = 1.30 (capacity loading)
If concentração < 10% → Ajuste = 0.90 (diversification discount)

Based on: Integrated Climate Insurance Pricing Framework
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PolicyPricingInput:
    """Input parameters for comprehensive pricing calculation"""

    policy_id: str
    pure_theoretical_premium: float  # PTP (Prêmio Teórico Puro)
    loading_margin: float  # ML (Loading Margin)
    total_risk_factor: float  # TR (Total Risk factor)
    climate_change_factor: float  # CC (Climate Change adjustment)
    zone_policies_premiums: List[float]  # Premiums of policies in zone
    free_capital: float  # Capital_livre (available capacity)
    zone_concentration_thresholds: Optional[Dict[str, float]] = (
        None  # Thresholds for concentration adjustment
    )


@dataclass
class PolicyAnalysisReport:
    """Complete climate risk analysis report for a policy"""

    policy_id: str
    risk_level: str
    scr_score: float
    climate_risk_breakdown: Dict[str, Any]
    decision: str
    decision_reason: str
    final_premium: float
    pure_theoretical_premium: float
    subscription_cost: float  # Custo_subscrição component
    claims_cost: float  # Custo_sinistros component
    admin_cost: float  # Custo_admin component
    premium_issued: float  # Prêmio_emitido
    processing_method: str  # Processing method used
    risk_category: str  # Risk category
    cost_breakdown: Dict[str, float]  # Detailed cost breakdown
    calculation_method: str
    calculation_timestamp: datetime


@dataclass
class ClimateRiskComponents:
    """Risk components for analysis"""

    physical_risk: float
    transition_risk: float
    concentration_risk: float
    mitigation_effect: float
    expected_claims: float


@dataclass
class PremiumBreakdown:
    """Breakdown of premium components"""

    expected_loss: float
    subscription_cost: float
    claims_processing_cost: float
    administrative_cost: float


class ComprehensivePricingService:
    """
    Calculator for comprehensive pricing using the specified formula:
    Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda
    """

    def __init__(self):
        # Risk level thresholds
        self.risk_thresholds = {
            "very_low": (0, 200),
            "low": (200, 400),
            "medium": (400, 600),
            "high": (600, 800),
            "critical": (800, float("inf")),
        }

        # Cost parameters
        self.subscription_cost_automated = 150.0  # R$ 150 per policy (automated)
        self.subscription_cost_manual = 450.0  # R$ 450 per policy (manual)

        # Percentage-based costs
        self.claims_processing_rate = 0.08  # 8% of premium for claims processing
        self.administrative_rate = 0.12  # 12% of premium for administration

        # Supply-demand adjustment thresholds
        self.concentration_thresholds = {
            "low": 0.10,  # <10% concentration
            "medium": 0.25,  # 10-25% concentration
            "high": 0.30,  # >25% concentration
        }

        # Adjustment factors for supply-demand
        self.supply_demand_adjustments = {
            "low_concentration": 0.90,  # 10% discount for low concentration (diversification)
            "medium_concentration": 1.00,  # Neutral adjustment for medium concentration
            "high_concentration": 1.30,  # 30% loading for high concentration (capacity constraint)
        }

    def calculate_zone_concentration_ratio(
        self, zone_policies_premiums: List[float], free_capital: float
    ) -> float:
        """
        Calculate zone concentration ratio:
        concentração_zoneamento = Σ_{apólices_na_ZCR} (Prêmio_i / Capital_livre)

        Args:
            zone_policies_premiums: List of premiums for policies in the zone
            free_capital: Available capital (Capital_livre)

        Returns:
            Concentration ratio (0 to infinity)
        """
        if not zone_policies_premiums:
            return 0.0

        if free_capital <= 0:
            raise ValueError("Free capital must be positive")

        total_zone_premiums = sum(zone_policies_premiums)
        concentration_ratio = total_zone_premiums / free_capital

        return concentration_ratio

    def determine_concentration_level(self, concentration_ratio: float) -> str:
        """
        Determine concentration level based on thresholds

        Args:
            concentration_ratio: Calculated concentration ratio

        Returns:
            Concentration level as string ('low', 'medium', 'high')
        """
        if concentration_ratio < self.concentration_thresholds["low"]:
            return "low"
        elif concentration_ratio < self.concentration_thresholds["high"]:
            return "medium"
        else:
            return "high"

    def calculate_supply_demand_adjustment(self, concentration_ratio: float) -> float:
        """
        Calculate supply-demand adjustment factor:

        If concentração > 25% → Ajuste = 1.30 (capacity loading)
        If concentração < 10% → Ajuste = 0.90 (diversification discount)

        Args:
            concentration_ratio: Concentration ratio in the zone

        Returns:
            Supply-demand adjustment factor
        """
        concentration_level = self.determine_concentration_level(concentration_ratio)

        return self.supply_demand_adjustments.get(
            f"{concentration_level}_concentration",
            self.supply_demand_adjustments["medium_concentration"],
        )

    def calculate_comprehensive_pricing(
        self, pricing_input: PolicyPricingInput
    ) -> PolicyAnalysisReport:
        """
        Calculate comprehensive premium using the integrated formula:
        Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda

        Args:
            pricing_input: Input parameters for pricing calculation

        Returns:
            PolicyAnalysisReport with complete calculation
        """
        # Calculate zone concentration ratio
        zone_concentration_ratio = self.calculate_zone_concentration_ratio(
            pricing_input.zone_policies_premiums, pricing_input.free_capital
        )

        # Calculate supply-demand adjustment
        supply_demand_adjustment = self.calculate_supply_demand_adjustment(
            zone_concentration_ratio
        )

        # Calculate final premium using the specified formula
        final_premium = (
            pricing_input.pure_theoretical_premium
            * (1 + pricing_input.loading_margin)
            * (1 + pricing_input.total_risk_factor)
            * (1 + pricing_input.climate_change_factor)
            * supply_demand_adjustment
        )

        # Calculate operating costs components based on final premium
        subscription_cost = (
            self.subscription_cost_automated
            if len(pricing_input.zone_policies_premiums)
            > 10  # If zone has many policies, use automated
            else self.subscription_cost_manual
        )

        claims_processing_cost = (
            pricing_input.pure_theoretical_premium * self.claims_processing_rate
        )
        administrative_cost = (
            pricing_input.pure_theoretical_premium * self.administrative_rate
        )

        # Determine risk level based on zone concentration
        risk_level = self._get_risk_level(
            zone_concentration_ratio * 1000
        )  # Scale to match SCR ranges

        # Calculate risk-adjusted scores (simplified)
        scr_score = (
            (zone_concentration_ratio * 1000)
            if zone_concentration_ratio <= 1
            else 800.0
        )  # Cap SCR

        return PolicyAnalysisReport(
            policy_id=pricing_input.policy_id,
            risk_level=risk_level,
            scr_score=scr_score,
            climate_risk_breakdown={
                "concentration_ratio": zone_concentration_ratio,
                "concentration_level": self.determine_concentration_level(
                    zone_concentration_ratio
                ),
                "supply_demand_adjustment": supply_demand_adjustment,
                "zone_policies_count": len(pricing_input.zone_policies_premiums),
                "total_zone_premiums": sum(pricing_input.zone_policies_premiums),
                "free_capital": pricing_input.free_capital,
            },
            decision=(
                "APPROVED"
                if scr_score < 700
                else "CONDITIONAL" if scr_score < 800 else "REJECTED"
            ),
            decision_reason=f"Based on concentration level: {self.determine_concentration_level(zone_concentration_ratio)}",
            final_premium=final_premium,
            pure_theoretical_premium=pricing_input.pure_theoretical_premium,
            subscription_cost=subscription_cost,
            claims_cost=claims_processing_cost,
            admin_cost=administrative_cost,
            premium_issued=final_premium,
            processing_method=(
                "automated"
                if len(pricing_input.zone_policies_premiums) > 10
                else "manual"
            ),
            risk_category=self.determine_concentration_level(zone_concentration_ratio),
            cost_breakdown={
                "supply_demand_adjustment": supply_demand_adjustment,
                "loading_margin_applied": pricing_input.loading_margin,
                "total_risk_factor_applied": pricing_input.total_risk_factor,
                "climate_change_factor_applied": pricing_input.climate_change_factor,
            },
            calculation_method="integrated_climate_insurance_pricing",
            calculation_timestamp=datetime.now(),
        )

    def _get_risk_level(self, scr_score: float) -> str:
        """Determine risk level based on SCR score"""
        for level, (min_val, max_val) in self.risk_thresholds.items():
            if min_val <= scr_score < max_val:
                return level.upper()

        return "CRITICAL"  # Default for scores above critical threshold

    def calculate_operating_costs(
        self,
        premium_issued: float,
        processing_method: str = "automated",
        risk_category: str = "standard",
        coverage_type: str = "property",
        claim_history_count: int = 0,
    ) -> Dict[str, float]:
        """
        Calculate operating costs components:
        CO = (Custo_subscrição + Custo_sinistros + Custo_admin) / Prêmio_emitido

        Where:
        - Custo_subscrição = R$ 150 (automated) or R$ 450 (manual)
        - Custo_sinistros = 0.08 × Prêmio (fraud detection, processing)
        - Custo_admin = 0.12 × Prêmio (technology, compliance)
        """
        # Calculate subscription cost
        subscription_cost = (
            self.subscription_cost_automated
            if processing_method.lower() == "automated"
            else self.subscription_cost_manual
        )

        # Adjust subscription cost by risk category
        risk_factors = {"low": 0.8, "standard": 1.0, "high": 1.2, "special": 1.5}
        subscription_cost *= risk_factors.get(risk_category.lower(), 1.0)

        # Calculate claims processing cost (0.08 × Prêmio)
        claims_cost = premium_issued * self.claims_processing_rate

        # Add additional claims cost if there's a history of claims
        if claim_history_count > 0:
            claims_cost += claim_history_count * 50  # Additional R$ 50 per past claim

        # Calculate administrative cost (0.12 × Prêmio)
        admin_cost = premium_issued * self.administrative_rate

        # Adjust admin cost by coverage type
        coverage_factors = {
            "property": 1.0,
            "liability": 1.1,
            "vehicle": 0.95,
            "agricultural": 1.05,
            "marine": 1.2,
            "aviation": 1.3,
        }
        admin_cost *= coverage_factors.get(coverage_type.lower(), 1.0)

        # Calculate total operating costs
        total_operating_costs = subscription_cost + claims_cost + admin_cost

        # Calculate operating cost ratio
        operating_cost_ratio = (
            total_operating_costs / premium_issued if premium_issued > 0 else 0.0
        )

        return {
            "subscription_cost": subscription_cost,
            "claims_cost": claims_cost,
            "admin_cost": admin_cost,
            "total_operating_costs": total_operating_costs,
            "operating_cost_ratio": operating_cost_ratio,
            "cost_breakdown": {
                "subscription_percentage": (
                    subscription_cost / total_operating_costs
                    if total_operating_costs > 0
                    else 0.0
                ),
                "claims_percentage": (
                    claims_cost / total_operating_costs
                    if total_operating_costs > 0
                    else 0.0
                ),
                "admin_percentage": (
                    admin_cost / total_operating_costs
                    if total_operating_costs > 0
                    else 0.0
                ),
            },
            "risk_category_multiplier": risk_factors.get(risk_category.lower(), 1.0),
            "coverage_type_multiplier": coverage_factors.get(
                coverage_type.lower(), 1.0
            ),
        }

    def calculate_profitability_analysis(
        self, premium_issued: float, expected_claims: float, operating_costs: float
    ) -> Dict[str, float]:
        """
        Calculate profitability metrics based on premium, expected claims, and operating costs
        """
        if premium_issued <= 0:
            return {
                "profitability_ratio": 0.0,
                "profit_margin": 0.0,
                "loss_ratio": 0.0,
                "combined_ratio": float("inf"),
                "net_income": -expected_claims - operating_costs,
                "profitability_status": "NOT_APPLICABLE",
            }

        # Calculate net income (premium minus claims minus operating costs)
        net_income = premium_issued - expected_claims - operating_costs

        # Calculate profitability ratio (net income / premium)
        profitability_ratio = net_income / premium_issued

        # Calculate profit margin (profit / premium)
        profit_margin = (
            max(0, net_income) / premium_issued if premium_issued > 0 else 0.0
        )

        # Calculate loss ratio (claims / premium)
        loss_ratio = expected_claims / premium_issued if premium_issued > 0 else 0.0

        # Calculate combined ratio (claims + operating costs / premium)
        combined_ratio = (
            (expected_claims + operating_costs) / premium_issued
            if premium_issued > 0
            else float("inf")
        )

        # Determine profitability status
        if profitability_ratio > 0.05:  # More than 5% profit
            profitability_status = "HIGHLY_PROFITABLE"
        elif profitability_ratio > 0.02:  # More than 2% profit
            profitability_status = "PROFITABLE"
        elif profitability_ratio > -0.02:  # Within 2% loss/profit
            profitability_status = "BREAK_EVEN"
        elif profitability_ratio > -0.05:  # Within 5% loss
            profitability_status = "MINOR_LOSS"
        else:
            profitability_status = "SIGNIFICANT_LOSS"

        return {
            "profitability_ratio": profitability_ratio,
            "profit_margin": profit_margin,
            "loss_ratio": loss_ratio,
            "combined_ratio": combined_ratio,
            "net_income": net_income,
            "profitability_status": profitability_status,
            "required_premium_for_break_even": expected_claims + operating_costs,
            "premium_loading_needed": (
                (expected_claims + operating_costs) / premium_issued
                if premium_issued > 0
                else float("inf")
            ),
        }


# Global instance
comprehensive_pricing_service = ComprehensivePricingService()


def calculate_comprehensive_premium(
    pricing_input: PolicyPricingInput,
) -> PolicyAnalysisReport:
    """Convenience function to calculate comprehensive premium"""
    return comprehensive_pricing_service.calculate_comprehensive_pricing(pricing_input)


def calculate_zone_concentration_ratio(
    zone_policies_premiums: List[float], free_capital: float
) -> float:
    """Convenience function to calculate zone concentration ratio"""
    return comprehensive_pricing_service.calculate_zone_concentration_ratio(
        zone_policies_premiums, free_capital
    )


def calculate_supply_demand_adjustment(concentration_ratio: float) -> float:
    """Convenience function to calculate supply-demand adjustment"""
    return comprehensive_pricing_service.calculate_supply_demand_adjustment(
        concentration_ratio
    )


def calculate_operating_costs(
    premium_issued: float,
    processing_method: str = "automated",
    risk_category: str = "standard",
    coverage_type: str = "property",
    claim_history_count: int = 0,
) -> Dict[str, float]:
    """Convenience function to calculate operating costs"""
    return comprehensive_pricing_service.calculate_operating_costs(
        premium_issued,
        processing_method,
        risk_category,
        coverage_type,
        claim_history_count,
    )


def calculate_profitability_analysis(
    premium_issued: float, expected_claims: float, operating_costs: float
) -> Dict[str, float]:
    """Convenience function to calculate profitability analysis"""
    return comprehensive_pricing_service.calculate_profitability_analysis(
        premium_issued, expected_claims, operating_costs
    )

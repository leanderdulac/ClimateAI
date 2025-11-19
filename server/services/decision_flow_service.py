"""
Decision Flow Service for Climate Insurance Underwriting
Implements the conditional workflow based on SCR score:
- SCR < 300: Green flow (Automatic acceptance)
- 300 ≤ SCR < 600: Yellow flow (Semi-automatic with conditions check)
- 600 ≤ SCR < 800: Orange flow (Manual underwriting + mandatory reinsurance)
- SCR ≥ 800: Red flow (Automatic rejection with parametric alternative)

Formula implemented:
Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PolicyApplication:
    """Information about an insurance policy application"""

    policy_id: str
    premium_theoretical_pure: float  # PTP (Pure Theoretical Premium)
    scr_score: float  # SCR score for the policy
    claim_history_count: int  # Number of previous claims
    mitigation_measures_count: int  # Number of implemented mitigation measures
    zone_concentration_percentage: float  # Zone concentration percentage (0-100%)
    coverage_amount: float  # Total coverage amount
    property_value: float  # Property value
    coverage_type: str = "property"  # Type of coverage
    location_coordinates: Tuple[float, float] = (0.0, 0.0)  # (latitude, longitude)
    policy_age_months: int = 0  # Policy age in months
    risk_factors: Optional[Dict[str, float]] = None  # Additional risk factors
    mitigation_details: Optional[List[Dict[str, Any]]] = (
        None  # Details of mitigation measures
    )


@dataclass
class DecisionFlowResult:
    """Result of decision flow analysis"""

    flow_color: str  # 'green', 'yellow', 'orange', 'red'
    decision: str  # 'accepted', 'conditionally_accepted', 'requires_manual_review', 'rejected'
    final_premium: float  # Final calculated premium
    premium_multiplier: float  # Applied premium multiplier
    conditions: List[str]  # Required conditions (if any)
    recommendations: List[str]  # Recommendations
    justification: str  # Reasoning for decision
    processing_time: str  # Time when processed
    application_data: Dict[str, Any]  # Application data
    risk_adjustments: Dict[str, float]  # Risk adjustment details
    workflow_details: Dict[str, Any]  # Workflow details
    calculation_timestamp: datetime


@dataclass
class ReinsuranceRequirements:
    """Requirements for reinsurance based on policy risk"""

    mandatory_reinsurance: bool
    reinsurance_type: str  # 'quota_share', 'excess_of_loss', etc.
    reinsurance_percentage: float  # Percentage to be reinsured
    reinsurance_trigger: float  # SCR score that triggered reinsurance requirement
    treaty_details: Dict[str, Any]


class DecisionFlowService:
    """
    Service that implements decision flow logic based on SCR score:
    - Green (SCR < 300): Automatic acceptance with minimal loading (15%)
    - Yellow (300 ≤ SCR < 600): Conditional acceptance based on criteria
    - Orange (600 ≤ SCR < 800): Manual review with mandatory reinsurance
    - Red (SCR ≥ 800): Automatic rejection with parametric alternative
    """

    def __init__(self):
        # SCR thresholds for decision flows
        self.flow_thresholds = {
            "green_max": 300.0,  # SCR < 300 for green flow
            "yellow_max": 600.0,  # 300 ≤ SCR < 600 for yellow flow
            "orange_max": 800.0,  # 600 ≤ SCR < 800 for orange flow
        }

        # Criteria for yellow flow acceptance
        self.yellow_criteria = {
            "max_claim_history": 2,  # Max 2 previous claims
            "min_mitigation_measures": 2,  # Minimum 2 mitigation measures required
            "max_concentration_percentage": 15.0,  # Max 15% concentration in zone
        }

        # Premium multipliers for different flows
        self.premium_multipliers = {
            "green": 1.15,  # 15% loading for green flow
            "yellow_ok": 1.25,  # 25% loading when yellow criteria are met
            "yellow_conditional": 1.30,  # 30% loading with conditions
            "orange": 1.50,  # 50% loading for orange flow (manual + reinsurance)
            "red": 0.0,  # No premium for red flow (rejection)
        }

    def determine_flow_color(self, scr_score: float) -> str:
        """
        Determine workflow flow based on SCR score

        Args:
            scr_score: Current SCR score

        Returns:
            Flow color ('green', 'yellow', 'orange', 'red')
        """
        if scr_score < self.flow_thresholds["green_max"]:
            return "green"
        elif scr_score < self.flow_thresholds["yellow_max"]:
            return "yellow"
        elif scr_score < self.flow_thresholds["orange_max"]:
            return "orange"
        else:
            return "red"

    def evaluate_yellow_criteria(
        self, application: PolicyApplication
    ) -> Dict[str, Any]:
        """
        Evaluate criteria for yellow flow acceptance:
        - claim_history_count <= 2
        - mitigation_measures_count >= 2
        - zone_concentration_percentage <= 15%

        Args:
            application: Policy application data

        Returns:
            Dictionary with evaluation results
        """
        # Check claim history criteria
        claim_history_ok = (
            application.claim_history_count <= self.yellow_criteria["max_claim_history"]
        )

        # Check mitigation measures criteria
        mitigation_measures_ok = (
            application.mitigation_measures_count
            >= self.yellow_criteria["min_mitigation_measures"]
        )

        # Check concentration criteria
        concentration_ok = (
            application.zone_concentration_percentage
            <= self.yellow_criteria["max_concentration_percentage"]
        )

        # Overall criteria assessment
        criteria_met = claim_history_ok and mitigation_measures_ok and concentration_ok

        return {
            "criteria_met": criteria_met,
            "claim_history_ok": claim_history_ok,
            "mitigation_measures_ok": mitigation_measures_ok,
            "concentration_ok": concentration_ok,
            "claim_history_count": application.claim_history_count,
            "mitigation_measures_count": application.mitigation_measures_count,
            "zone_concentration_percentage": application.zone_concentration_percentage,
            "individual_criteria_results": {
                "claim_history_check": f"Claims: {application.claim_history_count} ≤ {self.yellow_criteria['max_claim_history']} = {claim_history_ok}",
                "mitigation_check": f"Mitigation: {application.mitigation_measures_count} ≥ {self.yellow_criteria['min_mitigation_measures']} = {mitigation_measures_ok}",
                "concentration_check": f"Concentration: {application.zone_concentration_percentage:.1f}% ≤ {self.yellow_criteria['max_concentration_percentage']}% = {concentration_ok}",
            },
        }

    def calculate_policy_application(
        self, application: PolicyApplication
    ) -> DecisionFlowResult:
        """
        Process a policy application through the decision flow

        Args:
            application: Policy application with all required information

        Returns:
            DecisionFlowResult with flow determination and premium calculation
        """
        # Determine flow color based on SCR score
        flow_color = self.determine_flow_color(application.scr_score)
        processing_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Initialize result components
        decision = ""
        final_premium = 0.0
        premium_multiplier = 0.0
        conditions = []
        recommendations = []
        justification = ""
        reinsurance_reqs = None

        if flow_color == "green":
            # Green flow: Automatic acceptance with minimal loading
            decision = "accepted"
            premium_multiplier = self.premium_multipliers["green"]
            final_premium = application.premium_theoretical_pure * premium_multiplier
            conditions = []
            recommendations = [
                "Policy automatically accepted based on low climate risk (SCR < 300)",
                "Consider maintaining or improving mitigation measures to keep renewal rates favorable",
                f"Premium loaded at {premium_multiplier-1:.0%} above pure theoretical premium",
            ]
            justification = f"Green flow activated: SCR {application.scr_score:.2f} < 300 (low risk threshold). Automatic acceptance with minimal loading."

        elif flow_color == "yellow":
            # Yellow flow: Evaluate conditions
            criteria_evaluation = self.evaluate_yellow_criteria(application)

            if criteria_evaluation["criteria_met"]:
                # All criteria met, accept with moderate loading
                decision = "accepted"
                premium_multiplier = self.premium_multipliers["yellow_ok"]
                final_premium = (
                    application.premium_theoretical_pure * premium_multiplier
                )
                conditions = []
                recommendations = [
                    "Policy accepted based on meeting all yellow flow criteria",
                    f"Claim history: {application.claim_history_count} claims (≤{self.yellow_criteria['max_claim_history']} required)",
                    f"Mitigation measures: {application.mitigation_measures_count} measures (≥{self.yellow_criteria['min_mitigation_measures']} required)",
                    f"Zone concentration: {application.zone_concentration_percentage:.1f}% (≤{self.yellow_criteria['max_concentration_percentage']:.0f}% required)",
                    f"Premium loaded at {premium_multiplier-1:.0%} above pure theoretical premium",
                ]
                justification = "Yellow flow - all criteria met. Conditional acceptance with moderate loading."
            else:
                # Criteria not met, apply conditions
                decision = "conditionally_accepted"
                premium_multiplier = self.premium_multipliers["yellow_conditional"]
                final_premium = (
                    application.premium_theoretical_pure * premium_multiplier
                )

                # Determine which conditions need to be met
                if not criteria_evaluation["claim_history_ok"]:
                    conditions.append(
                        f"Reduce claim history to ≤{self.yellow_criteria['max_claim_history']} claims"
                    )

                if not criteria_evaluation["mitigation_measures_ok"]:
                    conditions.append(
                        f"Implement ≥{self.yellow_criteria['min_mitigation_measures']} mitigation measures"
                    )

                if not criteria_evaluation["concentration_ok"]:
                    conditions.append(
                        f"Reduce zone concentration to ≤{self.yellow_criteria['max_concentration_percentage']:.0f}%"
                    )

                recommendations = (
                    [
                        "Policy conditionally accepted based on yellow flow criteria",
                        "Following conditions must be satisfied:",
                    ]
                    + conditions
                    + [
                        f"Premium loaded at {premium_multiplier-1:.0%} above pure theoretical premium (higher due to unmet criteria)"
                    ]
                )

                justification = "Yellow flow - some criteria not met. Conditional acceptance with requirements to satisfy conditions."

        elif flow_color == "orange":
            # Orange flow: Manual review with mandatory reinsurance
            decision = "requires_manual_review"
            premium_multiplier = self.premium_multipliers["orange"]
            final_premium = application.premium_theoretical_pure * premium_multiplier

            reinsurance_reqs = ReinsuranceRequirements(
                mandatory_reinsurance=True,
                reinsurance_type="quota_share",
                reinsurance_percentage=0.50,  # 50% quota share
                reinsurance_trigger=application.scr_score,
                treaty_details={
                    "scr_threshold": self.flow_thresholds["orange_max"],
                    "reinsurance_percentage": 0.50,
                    "reinsurance_type": "quota_share",
                    "coverage_amount_subject_to_reinsurance": application.coverage_amount
                    * 0.50,
                },
            )

            conditions = [
                "Requires manual review by climate risk committee",
                "Mandatory quota-share reinsurance (50%) required",
                "Additional underwriting scrutiny needed",
                "Risk profile requires expert evaluation",
            ]

            recommendations = [
                "Policy requires detailed manual review due to high climate risk (300 ≤ SCR < 800)",
                "Climate risk committee assessment required",
                "50% quota-share reinsurance mandatory",
                f"Premium loaded at {premium_multiplier-1:.0%} above pure theoretical premium",
                "Consider alternative coverage options if standard terms are not acceptable",
            ]

            justification = f"Orange flow activated: SCR {application.scr_score:.2f} in range [300, 800). Manual review required with mandatory reinsurance."

        else:  # red flow
            # Red flow: Automatic rejection with parametric alternative
            decision = "rejected"
            premium_multiplier = self.premium_multipliers["red"]
            final_premium = 0.0  # No premium since rejected

            conditions = [
                "Policy automatically rejected due to excessive climate risk (SCR ≥ 800)",
                "Standard coverage unavailable at this risk level",
            ]

            recommendations = [
                "Standard coverage unavailable due to excessive climate risk (SCR ≥ 800)",
                "Consider parametric insurance alternative with index-based payouts",
                "Risk mitigation improvements required before standard coverage eligibility",
                "Contact underwriting team for parametric insurance options",
            ]

            justification = f"Red flow activated: SCR {application.scr_score:.2f} ≥ 800 (critical risk threshold). Automatic rejection with parametric alternative."

        # Calculate risk adjustments based on flow
        risk_adjustments = {
            "base_premium": application.premium_theoretical_pure,
            "flow_based_loading": premium_multiplier - 1.0,
            "scr_based_risk_loading": application.scr_score
            / 1000.0,  # Proportional to SCR
            "final_premium": final_premium,
        }

        # Prepare workflow details
        workflow_details = {
            "flow_color": flow_color,
            "scr_score": application.scr_score,
            "thresholds_applied": self.flow_thresholds,
            "decision_flow_path": f"SCR = {application.scr_score:.2f} → {flow_color.capitalize()} Flow → {decision.replace('_', ' ').title()}",
            "premium_calculation_method": f"PTP × {premium_multiplier:.2f} = {application.premium_theoretical_pure:.2f} × {premium_multiplier:.2f} = {final_premium:.2f}",
            "reinsurance_requirements": (
                vars(reinsurance_reqs) if reinsurance_reqs else None
            ),
            "yellow_criteria_evaluation": (
                self.evaluate_yellow_criteria(application)
                if flow_color == "yellow"
                else None
            ),
        }

        return DecisionFlowResult(
            flow_color=flow_color,
            decision=decision,
            final_premium=final_premium,
            premium_multiplier=premium_multiplier,
            conditions=conditions,
            recommendations=recommendations,
            justification=justification,
            processing_time=processing_time,
            application_data={
                "policy_id": application.policy_id,
                "ptp": application.premium_theoretical_pure,
                "scr_score": application.scr_score,
                "claim_history_count": application.claim_history_count,
                "mitigation_measures_count": application.mitigation_measures_count,
                "zone_concentration_percentage": application.zone_concentration_percentage,
                "coverage_amount": application.coverage_amount,
                "property_value": application.property_value,
                "coverage_type": application.coverage_type,
            },
            risk_adjustments=risk_adjustments,
            workflow_details=workflow_details,
            calculation_timestamp=datetime.now(),
        )

    def calculate_supply_demand_adjustment(self, concentration_ratio: float) -> float:
        """
        Calculate supply-demand adjustment based on concentration in zone
        - If concentration > 25% → Adjustment = 1.30 (capacity loading)
        - If concentration < 10% → Adjustment = 0.90 (diversification discount)

        Args:
            concentration_ratio: Ratio of premiums in zone to free capital (0-1 scale)

        Returns:
            Supply-demand adjustment factor
        """
        if concentration_ratio > 0.25:  # More than 25% concentration
            return 1.30  # 30% capacity loading
        elif concentration_ratio < 0.10:  # Less than 10% concentration
            return 0.90  # 10% diversification discount
        else:
            return 1.00  # No adjustment for moderate concentration

    def calculate_final_premium_with_adjustments(
        self,
        ptp: float,
        ml: float,
        tr: float,
        cc: float,
        supply_demand_adjustment: float,
    ) -> float:
        """
        Calculate final premium using the complete formula:
        Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda

        Args:
            ptp: Pure Theoretical Premium
            ml: Loading Margin factor
            tr: Total Risk factor
            cc: Climate Change factor
            supply_demand_adjustment: Supply-demand adjustment factor

        Returns:
            Final premium amount
        """
        final_premium = ptp * (1 + ml) * (1 + tr) * (1 + cc) * supply_demand_adjustment
        return max(0, final_premium)  # Ensure non-negative premium

    def batch_process_applications(
        self, applications: List[PolicyApplication]
    ) -> List[DecisionFlowResult]:
        """
        Process multiple applications in batch

        Args:
            applications: List of policy applications to process

        Returns:
            List of decision flow results
        """
        results = []
        for application in applications:
            result = self.calculate_policy_decision(application)
            results.append(result)
        return results

    def analyze_portfolio_flow_distribution(
        self, applications: List[PolicyApplication]
    ) -> Dict[str, Any]:
        """
        Analyze distribution of applications across decision flows

        Args:
            applications: List of applications to analyze

        Returns:
            Portfolio distribution analysis
        """
        flow_counts = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
        decisions = {
            "accepted": 0,
            "conditionally_accepted": 0,
            "requires_manual_review": 0,
            "rejected": 0,
        }

        total_scr = 0.0
        total_premium = 0.0
        processed_results = []

        for application in applications:
            result = self.calculate_policy_decision(application)
            flow_counts[result.flow_color] += 1
            decisions[result.decision] += 1
            total_scr += application.scr_score
            if result.decision in ["accepted", "conditionally_accepted"]:
                total_premium += result.final_premium

            processed_results.append(
                {
                    "policy_id": application.policy_id,
                    "scr_score": application.scr_score,
                    "flow_color": result.flow_color,
                    "decision": result.decision,
                    "final_premium": result.final_premium,
                    "premium_multiplier": result.premium_multiplier,
                }
            )

        portfolio_size = len(applications)
        avg_scr = total_scr / portfolio_size if portfolio_size > 0 else 0.0

        return {
            "total_applications": portfolio_size,
            "flow_distribution": flow_counts,
            "decision_distribution": decisions,
            "average_scr_score": avg_scr,
            "total_accepted_premium": total_premium,
            "acceptance_rate": (
                (decisions["accepted"] + decisions["conditionally_accepted"])
                / portfolio_size
                if portfolio_size > 0
                else 0.0
            ),
            "manual_review_rate": (
                decisions["requires_manual_review"] / portfolio_size
                if portfolio_size > 0
                else 0.0
            ),
            "rejection_rate": (
                decisions["rejected"] / portfolio_size if portfolio_size > 0 else 0.0
            ),
            "detailed_results": processed_results,
        }


# Global instance
decision_flow_service = DecisionFlowService()


def calculate_policy_application(application: PolicyApplication) -> DecisionFlowResult:
    """Convenience function to process policy through decision flow"""
    return decision_flow_service.calculate_policy_application(application)


def evaluate_yellow_criteria(application: PolicyApplication) -> Dict[str, Any]:
    """Convenience function to evaluate yellow flow criteria"""
    return decision_flow_service.evaluate_yellow_criteria(application)


def calculate_supply_demand_adjustment(concentration_ratio: float) -> float:
    """Convenience function to calculate supply-demand adjustment"""
    return decision_flow_service.calculate_supply_demand_adjustment(concentration_ratio)


def batch_process_policy_applications(
    applications: List[PolicyApplication],
) -> List[DecisionFlowResult]:
    """Convenience function for batch processing"""
    return decision_flow_service.batch_process_applications(applications)


def analyze_portfolio_flow_distribution(
    applications: List[PolicyApplication],
) -> Dict[str, Any]:
    """Convenience function for portfolio analysis"""
    return decision_flow_service.analyze_portfolio_flow_distribution(applications)

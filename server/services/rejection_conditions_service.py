"""
Autonomous Rejection and Conditioning Rules Engine
Implements hard stops and soft stops for climate insurance underwriting:

Hard Stops (Automatic Rejection):
1. SCR ≥ 800 (critical climate risk)
2. Cluster concentration > 35% and SCR > 600
3. Exposed value > R$ 10M and SCR > 700 (requires facultative reinsurance)
4. 3+ climate claims in last 5 years and no mitigation
5. Location in 100-year flood zone with projected increase > 150% and no drainage system

Soft Stops (Conditioning Rules):
1. Flooding: Drainage capacity > 500-year precipitation + pumping capacity > 100L/s
2. Wind: Minimum resistance class C (NBR 6123) + certified structural anchoring
3. Fire: Defensible space 30m + flame-retardant coating
4. General mitigation: Resilience score ≥ 60/100
5. Implementation timeframe: 90 days with drone-based IoT inspection
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RejectionReason(Enum):
    """Reasons for automatic rejection"""

    CRITICAL_CLIMATE_RISK = "critical_climate_risk"
    HIGH_CONCENTRATION_RISK = "high_concentration_risk"
    HIGH_VALUE_HIGH_RISK = "high_value_high_risk"
    HIGH_CLAIM_HISTORY_NO_MITIGATION = "high_claim_history_no_mitigation"
    FLOOD_ZONE_NO_DRAINAGE = "flood_zone_no_drainage"
    CUSTOMER_DECLINED_CONDITIONS = "customer_declined_conditions"


class ConditionType(Enum):
    """Types of conditions that can be imposed"""

    DRAINAGE_SYSTEM = "drainage_system"
    WIND_RESISTANCE = "wind_resistance"
    FIRE_PREVENTION = "fire_prevention"
    GENERAL_MITIGATION = "general_mitigation"
    LOCATION_IMPROVEMENT = "location_improvement"


@dataclass
class PolicyProfile:
    """Comprehensive policy profile for hard/soft stop evaluation"""

    policy_id: str
    scr_score: float
    exposed_value: float  # Value at risk
    zone_concentration_percentage: float  # Concentration in cluster
    climate_claim_history: List[Dict[str, Any]]  # History of climate claims
    mitigation_measures_implemented: List[
        str
    ]  # List of implemented mitigation measures
    location_coordinates: tuple  # (latitude, longitude)
    flood_zone_status: str  # 'none', 'frequent', '100_year'
    projected_flood_increase: float  # Projected increase in flooding (%)
    drainage_system_capacity: float  # L/s capacity
    wind_resistance_class: str  # A, B, C, D according to NBR 6123
    structural_anchoring_certified: bool
    fire_defensible_space_meters: float  # Space around property
    flame_retardant_coating_applied: bool
    resilience_score: float  # 0-100 scale
    implementation_deadline_days: int = 90
    inspection_method: str = "drone_iot"


@dataclass
class RejectionConditionsResult:
    """Result of hard/soft stop evaluation"""

    policy_id: str
    is_rejected: bool
    rejection_reason: Optional[str]
    conditions_required: List[Dict[str, Any]]
    is_conditionally_approved: bool
    conditional_approval_reasons: List[str]
    evaluation_timestamp: datetime


class RejectionConditionsEngine:
    """
    Engine for evaluating hard stops (automatic rejections) and soft stops (conditional approvals)
    """

    def __init__(self):
        # Thresholds for hard stops
        self.scr_hard_stop_threshold = 800.0
        self.cluster_concentration_threshold = 0.35  # 35%
        self.cluster_scr_threshold = 600.0  # SCR > 600
        self.exposed_value_threshold = 10000000.0  # R$ 10M
        self.high_risk_value_threshold = 700.0  # SCR > 700 for high value
        self.high_climate_claim_threshold = 3  # 3+ claims in 5 years
        self.flood_projection_threshold = 1.5  # 150% increase projected
        self.drainage_threshold = 100.0  # 100 L/s pump capacity
        self.min_resilience_score = 60.0  # Minimum resilience score
        self.fire_defensible_space_threshold = 30.0  # 30 meters

        # Wind resistance class mapping (NBR 6123)
        self.wind_resistance_classes = {
            "A": 1,
            "B": 2,
            "C": 3,  # Minimum required
            "D": 4,
        }

        # Default condition requirements
        self.condition_requirements = {
            "drainage_system": {
                "minimum_capacity": 100.0,  # L/s
                "precipitation_threshold": "500_years",  # Reference precipitation
            },
            "wind_resistance": {"minimum_class": "C", "certification_required": True},
            "fire_prevention": {
                "minimum_space": 30.0,  # meters
                "flame_retardant_required": True,
            },
            "general_mitigation": {"minimum_resilience_score": 60.0},
        }

    def evaluate_hard_stops(self, policy: PolicyProfile) -> Dict[str, Any]:
        """
        Evaluate policy against hard stop criteria

        Args:
            policy: Policy profile to evaluate

        Returns:
            Dictionary with rejection evaluation results
        """
        reasons = []

        # Rule 1: SCR ≥ 800 (critical climate risk)
        if policy.scr_score >= 800.0:
            reasons.append(
                {
                    "rule": "critical_climate_risk",
                    "reason": f"SCR score {policy.scr_score} >= 800",
                    "severity": "critical",
                }
            )

        # Rule 2: Cluster concentration > 35% and SCR > 600
        if policy.zone_concentration_percentage > 0.35 and policy.scr_score > 600.0:
            reasons.append(
                {
                    "rule": "high_concentration_risk",
                    "reason": f"Zone concentration {policy.zone_concentration_percentage*100:.1f}% > 35% and SCR > 600",
                    "severity": "high",
                }
            )

        # Rule 3: Exposed value > R$ 10M and SCR > 700
        if policy.exposed_value > 10000000.0 and policy.scr_score > 700.0:
            reasons.append(
                {
                    "rule": "high_value_high_risk",
                    "reason": f"Exposed value R$ {policy.exposed_value:,.2f} > R$ 10,000,000 and SCR > 700",
                    "severity": "high",
                }
            )

        # Rule 4: 3+ climate claims in last 5 years and no mitigation
        recent_claims = [
            claim
            for claim in policy.climate_claim_history
            if self._is_recent_claim(claim, 5)
        ]
        claim_count = len(recent_claims)

        if claim_count >= 3 and len(policy.mitigation_measures_implemented) == 0:
            reasons.append(
                {
                    "rule": "high_claim_history_no_mitigation",
                    "reason": f"{claim_count}+ climate claims in last 5 years with no mitigation measures",
                    "severity": "high",
                }
            )

        # Rule 5: Location in 100-year flood zone with projected increase > 150% and no drainage system
        if (
            policy.flood_zone_status == "100_year"
            and policy.projected_flood_increase > 1.5
            and policy.drainage_system_capacity == 0
        ):
            reasons.append(
                {
                    "rule": "flood_zone_no_drainage",
                    "reason": f"Located in 100-year flood zone with projected increase > 150% and no drainage system",
                    "severity": "high",
                }
            )

        is_rejected = len(reasons) > 0

        return {
            "is_rejected": is_rejected,
            "rejection_reasons": reasons,
            "hard_stop_rules_checked": {
                "scr_800_threshold": policy.scr_score >= 800.0,
                "cluster_concentration_rule": policy.zone_concentration_percentage
                > 0.35
                and policy.scr_score > 600.0,
                "high_value_rule": policy.exposed_value > 10000000.0
                and policy.scr_score > 700.0,
                "high_claim_history_rule": claim_count >= 3
                and len(policy.mitigation_measures_implemented) == 0,
                "flood_zone_rule": policy.flood_zone_status == "100_year"
                and policy.projected_flood_increase > 1.5
                and policy.drainage_system_capacity == 0,
            },
        }

    def evaluate_soft_stops(self, policy: PolicyProfile) -> List[Dict[str, Any]]:
        """
        Evaluate policy for soft stop conditions that require mitigation measures

        Args:
            policy: Policy profile to evaluate

        Returns:
            List of required conditions to approve the policy
        """
        conditions = []

        # Condition 1: Flooding mitigation
        if policy.scr_score > 400 and "flood" in policy.mitigation_measures_implemented:
            # Check if drainage capacity is adequate for 500-year event
            if policy.drainage_system_capacity < 100.0:
                conditions.append(
                    {
                        "type": "drainage_system",
                        "requirement": f"Drainage system capacity > {100.0} L/s",
                        "current_capacity": policy.drainage_system_capacity,
                        "required_capacity": 100.0,
                        "implementation_deadline": policy.implementation_deadline_days,
                        "inspection_method": policy.inspection_method,
                        "severity": "high" if policy.scr_score > 600 else "medium",
                    }
                )

        # Condition 2: Wind mitigation
        wind_resistance_value = self.wind_resistance_classes.get(
            policy.wind_resistance_class, 0
        )
        min_required_value = self.wind_resistance_classes.get("C", 0)

        if policy.scr_score > 450 and "wind" in policy.mitigation_measures_implemented:
            if (
                wind_resistance_value < min_required_value
                or not policy.structural_anchoring_certified
            ):
                conditions.append(
                    {
                        "type": "wind_resistance",
                        "requirement": f"Minimum wind resistance class C (NBR 6123) + certified structural anchoring",
                        "current_class": policy.wind_resistance_class,
                        "required_class": "C",
                        "anchoring_current": policy.structural_anchoring_certified,
                        "anchoring_required": True,
                        "implementation_deadline": policy.implementation_deadline_days,
                        "inspection_method": policy.inspection_method,
                        "severity": "high" if policy.scr_score > 650 else "medium",
                    }
                )

        # Condition 3: Fire mitigation
        if policy.scr_score > 300 and "fire" in policy.mitigation_measures_implemented:
            if (
                policy.fire_defensible_space_meters < 30.0
                or not policy.flame_retardant_coating_applied
            ):
                conditions.append(
                    {
                        "type": "fire_prevention",
                        "requirement": f"Defensible space 30m + flame-retardant coating",
                        "current_space": policy.fire_defensible_space_meters,
                        "required_space": 30.0,
                        "coating_current": policy.flame_retardant_coating_applied,
                        "coating_required": True,
                        "implementation_deadline": policy.implementation_dead_days,
                        "inspection_method": policy.inspection_method,
                        "severity": "medium" if policy.scr_score > 500 else "low",
                    }
                )

        # Condition 4: General mitigation
        if policy.resilience_score < 60.0:
            conditions.append(
                {
                    "type": "general_mitigation",
                    "requirement": f"Resilience score ≥ {60.0}/100",
                    "current_score": policy.resilience_score,
                    "required_score": 60.0,
                    "implementation_deadline": policy.implementation_deadline_days,
                    "inspection_method": policy.inspection_method,
                    "severity": "high" if policy.scr_score > 700 else "medium",
                }
            )

        return conditions

    def make_autonomous_decision(
        self, policy: PolicyProfile
    ) -> RejectionConditionsResult:
        """
        Make autonomous decision based on hard stops and soft stops

        Args:
            policy: Policy profile to evaluate

        Returns:
            RejectionConditionsResult with decision and recommendations
        """
        # Check hard stops first (these result in immediate rejection)
        hard_stop_result = self.evaluate_hard_stops(policy)

        if hard_stop_result["is_rejected"]:
            return RejectionConditionsResult(
                policy_id=policy.policy_id,
                is_rejected=True,
                rejection_reason=hard_stop_result["rejection_reasons"][0][
                    "reason"
                ],  # First reason
                conditions_required=[],
                is_conditionally_approved=False,
                conditional_approval_reasons=[],
                evaluation_timestamp=datetime.now(),
            )

        # Check soft stops (conditions that must be met for approval)
        soft_stop_conditions = self.evaluate_soft_stops(policy)

        if soft_stop_conditions:
            # Conditional approval - requires implementation of conditions
            conditional_reasons = [cond["requirement"] for cond in soft_stop_conditions]
            return RejectionConditionsResult(
                policy_id=policy.policy_id,
                is_rejected=False,
                rejection_reason=None,
                conditions_required=soft_stop_conditions,
                is_conditionally_approved=True,
                conditional_approval_reasons=conditional_reasons,
                evaluation_timestamp=datetime.now(),
            )
        else:
            # Policy passes both hard stops and soft stops - approved as-is
            return RejectionConditionsResult(
                policy_id=policy.policy_id,
                is_rejected=False,
                rejection_reason=None,
                conditions_required=[],
                is_conditionally_approved=False,
                conditional_approval_reasons=[],
                evaluation_timestamp=datetime.now(),
            )

    def _is_recent_claim(self, claim: Dict[str, Any], years_back: int) -> bool:
        """
        Check if a claim is recent within specified number of years

        Args:
            claim: Claim data with date
            years_back: Number of years to check

        Returns:
            Boolean indicating if claim is recent
        """
        if "date" not in claim:
            return False

        try:
            claim_date = datetime.fromisoformat(str(claim["date"]))
            years_diff = (datetime.now() - claim_date).days / 365.25
            return years_diff <= years_back
        except:
            return False  # If date parsing fails, assume not recent

    def get_conditioning_guidelines(self) -> Dict[str, Any]:
        """
        Get detailed guidelines for implementing conditions
        """
        return {
            "drainage_system_guidelines": {
                "minimum_capacity": f"> {100.0} L/s",
                "reference_event": "500-year precipitation",
                "verification_method": "IoT sensors + drone inspection",
                "implementation_deadline": "90 days",
                "cost_range": "R$ 20,000 - R$ 100,000",
                "maintenance_requirement": "Annual certification",
            },
            "wind_resistance_guidelines": {
                "minimum_class": "C (NBR 6123)",
                "certification_required": True,
                "verification_method": "Structural engineer + drone inspection",
                "implementation_deadline": "90 days",
                "cost_range": "R$ 5,000 - R$ 50,000",
                "maintenance_requirement": "Every 5 years",
            },
            "fire_prevention_guidelines": {
                "minimum_space": f"{30.0} meters",
                "flame_retardant_required": True,
                "verification_method": "Drone inspection + certification",
                "implementation_deadline": "90 days",
                "cost_range": "R$ 3,000 - R$ 20,000",
                "maintenance_requirement": "Annual inspection",
            },
            "general_mitigation_guidelines": {
                "minimum_resilience_score": 60.0,
                "measurement_method": "Resilience assessment checklist",
                "verification_method": "On-site inspection + documentation",
                "implementation_deadline": "90 days",
                "cost_range": "R$ 1,000 - R$ 25,000",
                "maintenance_requirement": "Bi-annual assessment",
            },
        }

    def calculate_resilience_score(
        self,
        drainage_capacity: float,
        wind_resistance_value: float,
        fire_space: float,
        fire_coating: bool,
        structural_certification: bool,
        mitigation_measures: List[str],
    ) -> float:
        """
        Calculate resilience score based on implemented measures

        Args:
            drainage_capacity: Drainage system capacity in L/s
            wind_resistance_value: Value of wind resistance (1=A, 2=B, 3=C, 4=D)
            fire_space: Fire defensible space in meters
            fire_coating: Whether flame retardant coating is applied
            structural_certification: Whether structural anchoring is certified
            mitigation_measures: List of mitigation measures implemented

        Returns:
            Resilience score (0-100 scale)
        """
        score = 0.0

        # Drainage component (0-20 points)
        score += min(20.0, (drainage_capacity / 100.0) * 20.0)

        # Wind resistance component (0-25 points)
        score += min(25.0, wind_resistance_value * 6.25)  # 6.25 points per class level

        # Fire prevention component (0-20 points)
        score += min(10.0, (fire_space / 30.0) * 10.0)  # Space: 0-10 pts
        if fire_coating:
            score += 10.0  # Flame retardant: 10 pts

        # Structural certification component (0-15 points)
        if structural_certification:
            score += 15.0

        # Mitigation measures component (0-20 points)
        mit_score = len(mitigation_measures) * 5.0  # 5 points per mitigation
        score += min(20.0, mit_score)

        return min(100.0, score)

    def calculate_conditioning_probability(
        self, unmet_conditions: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate probability that all conditions will be properly implemented

        Args:
            unmet_conditions: List of unmet conditions

        Returns:
            Probability (0-1) that conditions will be implemented
        """
        if not unmet_conditions:
            return 1.0  # 100% if no conditions needed

        # Base probability starts at 1.0
        prob = 1.0

        for condition in unmet_conditions:
            severity = condition.get("severity", "medium")

            # Adjust probability based on severity and effort
            if severity == "high":
                prob *= 0.8  # 80% chance for high-severity requirements
            elif severity == "medium":
                prob *= 0.9  # 90% chance for medium requirements
            else:  # low
                prob *= 0.95  # 95% chance for low requirements

        return prob


# Global instance
rejection_conditions_service = RejectionConditionsEngine()


def evaluate_policy_hard_stops(policy: PolicyProfile) -> Dict[str, Any]:
    """Convenience function to evaluate hard stops for a policy"""
    return rejection_conditions_service.evaluate_hard_stops(policy)


def evaluate_policy_soft_stops(policy: PolicyProfile) -> List[Dict[str, Any]]:
    """Convenience function to evaluate soft stops for a policy"""
    return rejection_conditions_service.evaluate_soft_stops(policy)


def make_policy_decision(policy: PolicyProfile) -> RejectionConditionsResult:
    """Convenience function to make autonomous policy decision"""
    return rejection_conditions_service.make_autonomous_decision(policy)


def calculate_policy_resilience_score(
    drainage_capacity: float,
    wind_resistance_class: str,
    fire_space: float,
    fire_coating: bool,
    structural_certification: bool,
    mitigation_measures: List[str],
) -> float:
    """Convenience function to calculate policy resilience score"""
    wind_value = rejection_conditions_service.wind_resistance_classes.get(
        wind_resistance_class, 0
    )
    return rejection_conditions_service.calculate_resilience_score(
        drainage_capacity,
        wind_value,
        fire_space,
        fire_coating,
        structural_certification,
        mitigation_measures,
    )


def calculate_conditioning_probability(unmet_conditions: List[Dict[str, Any]]) -> float:
    """Convenience function to calculate conditioning probability"""
    return rejection_conditions_service.calculate_conditioning_probability(
        unmet_conditions
    )

"""
Matriz de Decisão de Subscrição (MDS) - Underwriting Decision Matrix
Implements comprehensive underwriting decision logic based on risk scores, actuarial analysis, and commercial pricing.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import norm

logger = logging.getLogger(__name__)


class Decision(Enum):
    """Underwriting decision options"""

    ACCEPT = "accept"
    ACCEPT_WITH_CONDITIONS = "accept_with_conditions"
    ACCEPT_WITH_RISK_LOADINGS = "accept_with_risk_loadings"
    REJECT = "reject"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


class Condition(Enum):
    """Possible underwriting conditions"""

    PREMIUM_LOAD = "premium_load"
    DEDUCTIBLE_INCREASE = "deductible_increase"
    EXCLUSION = "exclusion"
    ADDITIONAL_INSPECTION = "additional_inspection"
    COVERAGE_LIMITATION = "coverage_limitation"
    CO_INSURANCE = "co_insurance"
    REPORTING_REQUIREMENTS = "reporting_requirements"


@dataclass
class UnderwritingDecision:
    """Result of underwriting decision process"""

    decision: Decision
    conditions: List[Condition]
    premium_adjustment: float
    coverage_modifications: List[str]
    risk_score: float
    profit_margin: float
    justification: List[str]
    decision_timestamp: datetime
    confidence_level: float
    review_required: bool


@dataclass
class ApplicationData:
    """Input data for underwriting decision"""

    applicant_id: str
    coverage_requested: float
    coverage_type: str
    asset_value: float
    location_coordinates: Tuple[float, float]
    applicant_profile: Dict[str, Any]  # Demographics, credit, etc.
    policy_features: Dict[str, Any]  # Deductible, term, etc.
    historical_claims: List[Dict[str, Any]]


@dataclass
class ModuleInputs:
    """Inputs from all upstream modules"""

    climate_risk_score: float  # From SCR
    climate_risk_breakdown: Dict[str, float]
    actuarial_premium: float  # From AAT
    actuarial_indicators: Dict[str, float]
    commercial_premium: float  # From EPC
    market_position: str
    pricing_strategy: str


class MDSModuleService:
    """
    Underwriting decision engine that synthesizes inputs from all modules
    to make informed underwriting decisions with appropriate conditions.
    """

    def __init__(self):
        self.decision_thresholds = {
            "accept_threshold": 0.7,  # Climate risk score below this is acceptable
            "conditional_threshold": 0.85,  # Between accept and reject thresholds
            "reject_threshold": 0.95,  # Above this is automatically rejected
        }

        self.profitability_thresholds = {
            "minimum_acceptable": 0.03,  # 3% minimum margin
            "target_margin": 0.15,  # 15% target
            "maximum_risk": 0.30,  # 30% cap for risk-adjusted premiums
        }

        self.automated_decision_limits = {
            "max_coverage": 1000000,  # $1M automated approval limit
            "min_risk_score": 0.6,  # Above this requires manual review
            "max_premium_load": 0.50,  # Above 50% load requires manual review
        }

        self.condition_matrix = {
            # Conditions to apply based on risk score ranges
            "0.5-0.7": [],
            "0.7-0.85": [Condition.PREMIUM_LOAD],
            "0.85-0.95": [Condition.PREMIUM_LOAD, Condition.DEDUCTIBLE_INCREASE],
            "0.95+": [],  # REJECT is a decision, not a condition
        }

        self.pricing_elasticity = {
            # How much pricing can be adjusted based on risk
            "max_load_for_accept": 0.40,  # 40% maximum load for acceptance
            "min_deductible_multiplier": 1.5,  # Minimum deductible increase factor
            "max_coverage_reduction": 0.80,  # Maximum coverage reduction
        }

    def make_underwriting_decision(
        self, application: ApplicationData, module_inputs: ModuleInputs
    ) -> UnderwritingDecision:
        """
        Make comprehensive underwriting decision based on all module inputs.

        Args:
            application: Application data
            module_inputs: Inputs from all upstream modules

        Returns:
            UnderwritingDecision with complete decision and reasoning
        """
        # Extract key metrics from module inputs
        risk_score = module_inputs.climate_risk_score
        actuarial_premium = module_inputs.actuarial_premium
        commercial_premium = module_inputs.commercial_premium

        # Calculate profit margin
        profit_margin = (
            (commercial_premium - actuarial_premium) / commercial_premium
            if commercial_premium > 0
            else 0
        )

        # Determine primary decision based on risk score
        decision = self._determine_primary_decision(
            risk_score, application, module_inputs
        )

        # Determine conditions based on risk level
        conditions = self._determine_conditions(risk_score, decision)

        # Calculate premium adjustment
        premium_adjustment = self._calculate_premium_adjustment(
            risk_score, commercial_premium, decision
        )

        # Determine coverage modifications
        coverage_modifications = self._determine_coverage_modifications(
            risk_score, application.coverage_requested, decision
        )

        # Generate justification
        justification = self._generate_justification(
            decision, risk_score, profit_margin, conditions, module_inputs, application
        )

        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(
            module_inputs, application, decision
        )

        # Determine if manual review is required
        review_required = self._requires_manual_review(
            risk_score, premium_adjustment, application, decision
        )

        # If manual review is required, change decision to manual review
        if review_required and decision != Decision.REJECT:
            decision = Decision.REQUIRES_MANUAL_REVIEW

        return UnderwritingDecision(
            decision=decision,
            conditions=conditions,
            premium_adjustment=premium_adjustment,
            coverage_modifications=coverage_modifications,
            risk_score=risk_score,
            profit_margin=profit_margin,
            justification=justification,
            decision_timestamp=datetime.now(),
            confidence_level=confidence_level,
            review_required=review_required,
        )

    def _determine_primary_decision(
        self,
        risk_score: float,
        application: ApplicationData,
        module_inputs: ModuleInputs,
    ) -> Decision:
        """Determine the primary underwriting decision based on risk score"""
        # Check automated decision limits
        if (
            application.coverage_requested
            > self.automated_decision_limits["max_coverage"]
        ):
            return Decision.REQUIRES_MANUAL_REVIEW

        # Apply risk-based thresholds
        if risk_score < self.decision_thresholds["accept_threshold"]:
            return Decision.ACCEPT
        elif risk_score < self.decision_thresholds["conditional_threshold"]:
            return Decision.ACCEPT_WITH_CONDITIONS
        elif risk_score < self.decision_thresholds["reject_threshold"]:
            return Decision.ACCEPT_WITH_RISK_LOADINGS
        else:
            return Decision.REJECT

    def _determine_conditions(
        self, risk_score: float, decision: Decision
    ) -> List[Condition]:
        """Determine appropriate conditions based on risk score and decision"""
        if decision == Decision.REJECT:
            return []
        elif decision == Decision.ACCEPT:
            return []
        elif decision == Decision.ACCEPT_WITH_CONDITIONS:
            if 0.7 <= risk_score < 0.85:
                return [Condition.PREMIUM_LOAD]
            else:
                return [Condition.PREMIUM_LOAD, Condition.DEDUCTIBLE_INCREASE]
        elif decision == Decision.ACCEPT_WITH_RISK_LOADINGS:
            conditions = [Condition.PREMIUM_LOAD]
            if risk_score > 0.9:
                conditions.extend(
                    [Condition.DEDUCTIBLE_INCREASE, Condition.COVERAGE_LIMITATION]
                )
            return conditions
        else:  # Manual review
            return [Condition.ADDITIONAL_INSPECTION]

    def _calculate_premium_adjustment(
        self, risk_score: float, commercial_premium: float, decision: Decision
    ) -> float:
        """Calculate premium adjustment based on risk score and decision"""
        if decision == Decision.REJECT:
            return 0.0  # No adjustment needed for rejected applications

        # Risk-based loading formula: higher risk = higher loading
        if risk_score < 0.5:
            loading = 0.05  # Low risk gets small load
        elif risk_score < 0.7:
            loading = 0.15  # Medium risk gets moderate load
        elif risk_score < 0.85:
            loading = 0.25  # High risk gets significant load
        elif risk_score < 0.95:
            loading = 0.40  # Very high risk gets maximum automated load
        else:
            loading = 0.0  # Rejected anyway, no loading

        return commercial_premium * loading

    def _determine_coverage_modifications(
        self, risk_score: float, coverage_requested: float, decision: Decision
    ) -> List[str]:
        """Determine coverage modifications based on risk score"""
        modifications = []

        if decision == Decision.REJECT:
            return modifications

        # Apply coverage modifications based on risk
        if risk_score > 0.8:
            modifications.append(f"Coverage reduced by 20% for high risk")

        if risk_score > 0.9:
            modifications.extend(
                [
                    f"Coverage reduced by 40% for very high risk",
                    f"Co-insurance of 20% required",
                ]
            )

        # Deductible adjustments
        if risk_score > 0.7:
            modifications.append(f"Deductible increased by 50%")

        if risk_score > 0.9:
            modifications.append(f"Deductible increased by 100% (doubled)")

        return modifications

    def _generate_justification(
        self,
        decision: Decision,
        risk_score: float,
        profit_margin: float,
        conditions: List[Condition],
        module_inputs: ModuleInputs,
        application: ApplicationData,
    ) -> List[str]:
        """Generate justification for the underwriting decision"""
        justification = []

        # Climate risk justification
        justification.append(f"Climate risk score: {risk_score:.2f}")
        if risk_score < 0.5:
            justification.append("Climate risk is within acceptable parameters")
        elif risk_score < 0.7:
            justification.append(
                "Climate risk is moderate, manageable with standard procedures"
            )
        elif risk_score < 0.85:
            justification.append(
                "Climate risk is elevated, requiring additional risk management"
            )
        elif risk_score < 0.95:
            justification.append(
                "Climate risk is high, requiring significant risk mitigation"
            )
        else:
            justification.append("Climate risk is excessive, policy not viable")

        # Actuarial justification
        if decision != Decision.REJECT:
            act_premium = module_inputs.actuarial_premium
            comm_premium = module_inputs.commercial_premium
            justification.append(
                f"Actuarial premium: ${act_premium:,.2f}, Commercial premium: ${comm_premium:,.2f}"
            )

            if profit_margin >= self.profitability_thresholds["minimum_acceptable"]:
                justification.append(
                    f"Projected profit margin of {profit_margin:.1%} meets minimum requirements"
                )
            else:
                justification.append(
                    f"Projected profit margin of {profit_margin:.1%} is below minimum acceptable ({self.profitability_thresholds['minimum_acceptable']:.0%})"
                )

        # Decision-specific justification
        if decision == Decision.ACCEPT:
            justification.append("Application meets all underwriting criteria")
        elif decision == Decision.ACCEPT_WITH_CONDITIONS:
            condition_names = [cond.value for cond in conditions]
            justification.append(
                f"Application conditionally accepted with: {', '.join(condition_names)}"
            )
        elif decision == Decision.ACCEPT_WITH_RISK_LOADINGS:
            justification.append(
                f"Significant risk loadings applied due to high climate risk"
            )
        elif decision == Decision.REJECT:
            justification.append(
                "Application rejected due to excessive risk or unprofitability"
            )
        elif decision == Decision.REQUIRES_MANUAL_REVIEW:
            justification.append(
                "Application requires manual review due to high risk or special circumstances"
            )

        return justification

    def _calculate_confidence_level(
        self,
        module_inputs: ModuleInputs,
        application: ApplicationData,
        decision: Decision,
    ) -> float:
        """Calculate confidence level in the underwriting decision"""
        # Factors that influence confidence:
        # 1. Data quality score (from climate risk)
        climate_data_quality = min(
            1.0, module_inputs.climate_risk_score + 0.3
        )  # Invert risk for quality

        # 2. Time since last claim (if applicable)
        claim_data = application.historical_claims
        if claim_data:
            # Assuming more recent claims reduce confidence
            latest_claim = max(claim.get("date", "2000-01-01") for claim in claim_data)
            import datetime

            latest_date = datetime.datetime.fromisoformat(latest_claim.split("T")[0])
            days_since_claim = (datetime.datetime.now() - latest_date).days
            claim_factor = min(
                1.0, days_since_claim / 1095
            )  # Max confidence after 3 years
        else:
            claim_factor = 1.0  # No claims is good

        # 3. Market position impact
        if module_inputs.market_position == "competitive":
            market_factor = 0.9
        elif module_inputs.market_position == "low_priced":
            market_factor = 0.8
        else:
            market_factor = 1.0

        # 4. Risk score (inversely related to confidence as risk increases)
        risk_factor = max(0.3, 1.0 - module_inputs.climate_risk_score)

        # Calculate overall confidence
        confidence = (
            climate_data_quality * 0.25
            + claim_factor * 0.25
            + market_factor * 0.25
            + risk_factor * 0.25
        )

        return confidence

    def _requires_manual_review(
        self,
        risk_score: float,
        premium_adjustment: float,
        application: ApplicationData,
        decision: Decision,
    ) -> bool:
        """Determine if application requires manual review"""
        # Manual review required if:
        # 1. Risk score above threshold
        if risk_score > self.automated_decision_limits["min_risk_score"]:
            return True

        # 2. Premium adjustment above threshold
        if premium_adjustment > self.automated_decision_limits["max_premium_load"]:
            return True

        # 3. Coverage requested exceeds automated limit
        if (
            application.coverage_requested
            > self.automated_decision_limits["max_coverage"]
        ):
            return True

        # 4. Special coverage types (would normally check against list)
        special_coverage = ["nuclear", "hazardous_materials", "experimental_tech"]
        if any(sc in application.coverage_type.lower() for sc in special_coverage):
            return True

        # 5. Complex risk combinations - skip check if no breakdown data available
        # Note: module_inputs not available in this scope, so we skip this check
        # This would need to be passed as a parameter in a real implementation

        return False

    def apply_policy_rules(
        self, application: ApplicationData, module_inputs: ModuleInputs
    ) -> Dict[str, Any]:
        """
        Apply policy-specific underwriting rules

        Args:
            application: Application data
            module_inputs: Inputs from all modules

        Returns:
            Dictionary of rule application results
        """
        results = {"rules_applied": [], "overrides": [], "additional_conditions": []}

        # Example of applying policy-type-specific rules
        coverage_type = application.coverage_type.lower()

        if "agriculture" in coverage_type or "crop" in coverage_type:
            # Agricultural specific rules
            results["rules_applied"].append("Agricultural risk assessment applied")

            # Seasonal factors
            if module_inputs.climate_risk_breakdown.get("flood_risk", 0) > 0.7:
                results["additional_conditions"].append(
                    "Increased flood monitoring required"
                )

            # Soil/land type considerations
            soil_quality = application.applicant_profile.get("soil_quality", "medium")
            if soil_quality == "poor":
                results["overrides"].append(
                    "Additional premium load for poor soil quality"
                )

        elif "property" in coverage_type:
            # Property specific rules
            results["rules_applied"].append("Property insurance rules applied")

            # Building age considerations
            building_age = application.applicant_profile.get("building_age", 20)
            if building_age > 50:
                results["additional_conditions"].append(
                    "Historical property inspection required"
                )

        elif "infrastructure" in coverage_type:
            # Infrastructure specific rules
            results["rules_applied"].append("Infrastructure risk assessment applied")

            # Critical infrastructure considerations
            if application.applicant_profile.get("critical_infrastructure", False):
                results["overrides"].append("Enhanced coverage terms may apply")

        # Apply location-specific rules
        lat, lon = application.location_coordinates
        if abs(lat) < 23.5:  # Tropical region
            results["additional_conditions"].append(
                "Tropical climate risk factors applied"
            )

        return results

    def calculate_risk_tolerances(
        self, applicant_profile: Dict[str, Any], coverage_type: str
    ) -> Dict[str, float]:
        """
        Calculate client-specific risk tolerances based on profile

        Args:
            applicant_profile: Profile of the applicant
            coverage_type: Type of coverage

        Returns:
            Dictionary of risk tolerances
        """
        # Base tolerances
        tolerances = {
            "max_climate_risk_score": 0.85,
            "max_premium_load": 0.35,
            "min_profit_margin": 0.08,
        }

        # Adjust based on applicant profile
        client_type = applicant_profile.get("client_type", "individual")
        if client_type == "corporate":
            # Corporates may accept higher risks for larger accounts
            tolerances["max_climate_risk_score"] = 0.90
            tolerances["max_premium_load"] = 0.45
        elif client_type == "government":
            # Government entities may have different risk tolerances
            tolerances["max_climate_risk_score"] = 0.80
            tolerances["min_profit_margin"] = 0.05  # Lower profit requirement

        # Adjust based on coverage type
        if "experimental" in coverage_type:
            tolerances["max_climate_risk_score"] = (
                0.70  # Lower tolerance for experimental
            )
            tolerances["max_premium_load"] = 0.50  # Higher tolerance for loading

        # Adjust based on volume/size
        if applicant_profile.get("portfolio_size", 1) > 100:
            # Large portfolios get more flexible terms
            tolerances["max_climate_risk_score"] = min(
                0.95, tolerances["max_climate_risk_score"] + 0.05
            )

        return tolerances

    def get_decision_tree_path(
        self, risk_score: float, profit_margin: float, coverage_amount: float
    ) -> List[str]:
        """
        Get the decision tree path that led to the final decision

        Args:
            risk_score: Climate risk score
            profit_margin: Projected profit margin
            coverage_amount: Coverage amount requested

        Returns:
            List of decision steps taken
        """
        path = ["Application received"]

        # Risk assessment
        if risk_score < self.decision_thresholds["accept_threshold"]:
            path.append("Risk score acceptable")
        elif risk_score < self.decision_thresholds["conditional_threshold"]:
            path.append("Risk score requires conditions")
        elif risk_score < self.decision_thresholds["reject_threshold"]:
            path.append("Risk score requires significant loadings")
        else:
            path.append("Risk score exceeds maximum acceptable")

        # Profitability assessment
        if profit_margin >= self.profitability_thresholds["minimum_acceptable"]:
            path.append("Profitability targets met")
        else:
            path.append("Profitability below minimum threshold")

        # Coverage limits
        if coverage_amount <= self.automated_decision_limits["max_coverage"]:
            path.append("Coverage amount within automated limits")
        else:
            path.append("Coverage exceeds automated approval limits")

        path.append("Decision rendered")
        return path


# Global instance
mds_module_service = MDSModuleService()


def make_underwriting_decision(
    application: ApplicationData, module_inputs: ModuleInputs
) -> UnderwritingDecision:
    """Convenience function to make underwriting decision"""
    return mds_module_service.make_underwriting_decision(application, module_inputs)


def apply_policy_rules(
    application: ApplicationData, module_inputs: ModuleInputs
) -> Dict[str, Any]:
    """Convenience function to apply policy rules"""
    return mds_module_service.apply_policy_rules(application, module_inputs)


def calculate_risk_tolerances(
    applicant_profile: Dict[str, Any], coverage_type: str
) -> Dict[str, float]:
    """Convenience function to calculate risk tolerances"""
    return mds_module_service.calculate_risk_tolerances(
        applicant_profile, coverage_type
    )


def get_decision_tree_path(
    risk_score: float, profit_margin: float, coverage_amount: float
) -> List[str]:
    """Convenience function to get decision tree path"""
    return mds_module_service.get_decision_tree_path(
        risk_score, profit_margin, coverage_amount
    )

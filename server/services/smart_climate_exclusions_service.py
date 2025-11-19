"""
Smart Climate Exclusions Service
Handles exclusions for:
- Eventos não-modeláveis: Terremoto induzido por clima (low confidence)
- Falha de mitigação: Se cliente não implementou medidas exigidas
- Litígio climático: Responsabilidade civil por emissões (ainda não maduro)

Plus governance recommendations:
- Aprovação manual obrigatória para SCR > 600 (não delegar totalmente à IA)
- Comitê de risco climático trimestral para revisar decisões do sistema
- Auditoria externa anual dos modelos (validação por atuárias independentes)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ClimateExclusionType(Enum):
    """Types of climate exclusions"""

    UNMODELABLE_EVENTS = "evento_nao_modelavel"
    MITIGATION_FAILURE = "falha_mitigacao"
    CLIMATE_LITIGATION = "litigio_climatico"
    OTHER = "outro"


class GovernanceRecommendation(Enum):
    """Types of governance recommendations"""

    MANUAL_APPROVAL_REQUIRED = "aprovacao_manual_obrigatoria"
    QUARTERLY_COMMITTEE_REVIEW = "comite_risco_trimestral"
    ANNUAL_EXTERNAL_AUDIT = "auditoria_externa_anual"


@dataclass
class ClimateExclusion:
    """Data structure for a climate exclusion"""

    exclusion_id: str
    exclusion_type: ClimateExclusionType
    risk_description: str
    loading_factor: float  # 5.0 = 500% loading for events not covered
    confidence_level: float  # 0.0 to 1.0, low confidence events get excluded
    coverage_status: str  # "excluded", "covered_with_loading", "covered_normal"
    reason: str
    implementation_date: datetime
    review_date: datetime


@dataclass
class GovernanceRule:
    """Data structure for governance recommendations"""

    rule_id: str
    rule_type: GovernanceRecommendation
    trigger_condition: str  # Condition that triggers the rule
    threshold_value: float  # Value that triggers the rule (e.g., SCR > 600)
    required_action: str  # Action to be taken
    review_frequency: str  # How often this should be reviewed
    status: str  # "active", "inactive", "pending"
    implementation_date: datetime


@dataclass
class ExclusionDecision:
    """Result of exclusion evaluation"""

    policy_id: str
    excluded_risks: List[ClimateExclusion]
    coverage_status: Dict[str, str]  # Risk type -> coverage status
    governance_recommendations: List[GovernanceRule]
    final_premium_adjustment: float  # Additional loading based on exclusions
    decision_timestamp: datetime
    decision_reasons: List[str]


class SmartClimateExclusionsService:
    """
    Service to handle smart climate exclusions and governance recommendations
    based on the specified requirements
    """

    def __init__(self):
        # Default loading factor for excluded risks (500% as specified)
        self.default_excluded_loading_factor = 5.0  # 500%

        # Confidence thresholds
        self.low_confidence_threshold = 0.3  # Below this is considered low confidence
        self.medium_confidence_threshold = 0.6

        # Governance thresholds
        self.manual_approval_threshold = 600  # SCR > 600 requires manual approval

        # Exclusion definitions based on requirements
        self.exclusion_definitions = {
            ClimateExclusionType.UNMODELABLE_EVENTS: {
                "description": "Terremoto induzido por clima (low confidence)",
                "loading_factor": self.default_excluded_loading_factor,
                "confidence_threshold": self.low_confidence_threshold,
                "coverage_status": "excluded",
                "reason": "Evento não modelável com baixa confiança",
            },
            ClimateExclusionType.MITIGATION_FAILURE: {
                "description": "Falha de mitigação: cliente não implementou medidas exigidas",
                "loading_factor": self.default_excluded_loading_factor,
                "confidence_threshold": 0.0,  # Always applies if mitigation failed
                "coverage_status": "covered_with_loading",
                "reason": "Falha na implementação de medidas de mitigação",
            },
            ClimateExclusionType.CLIMATE_LITIGATION: {
                "description": "Litígio climático: Responsabilidade civil por emissões (ainda não maduro)",
                "loading_factor": self.default_excluded_loading_factor,
                "confidence_threshold": 0.3,  # Low maturity = low confidence
                "coverage_status": "excluded",
                "reason": "Modelo imaturo para litígio climático",
            },
        }

        # Governance rules based on requirements
        self.governance_rules = [
            GovernanceRule(
                rule_id="GVR_001",
                rule_type=GovernanceRecommendation.MANUAL_APPROVAL_REQUIRED,
                trigger_condition="SCR > 600",
                threshold_value=600.0,
                required_action="Aprovação manual obrigatória para SCR > 600 (não delegar totalmente à IA)",
                review_frequency="single",
                status="active",
                implementation_date=datetime.now(),
            ),
            GovernanceRule(
                rule_id="GVR_002",
                rule_type=GovernanceRecommendation.QUARTERLY_COMMITTEE_REVIEW,
                trigger_condition="trimestral",
                threshold_value=0.0,
                required_action="Comitê de risco climático trimestral para revisar decisões do sistema",
                review_frequency="quarterly",
                status="active",
                implementation_date=datetime.now(),
            ),
            GovernanceRule(
                rule_id="GVR_003",
                rule_type=GovernanceRecommendation.ANNUAL_EXTERNAL_AUDIT,
                trigger_condition="anual",
                threshold_value=0.0,
                required_action="Auditoria externa anual dos modelos (validação por atuárias independentes)",
                review_frequency="annual",
                status="active",
                implementation_date=datetime.now(),
            ),
        ]

        # Store active exclusions and decisions
        self.active_exclusions: Dict[str, ClimateExclusion] = {}
        self.governance_decisions: Dict[str, ExclusionDecision] = {}

    def evaluate_climate_exclusions(
        self,
        policy_id: str,
        climate_risk_factors: Dict[str, Any],
        mitigation_status: Optional[Dict[str, Any]] = None,
        model_confidence: Optional[Dict[str, float]] = None,
    ) -> ExclusionDecision:
        """
        Evaluate climate exclusions based on policy data

        Args:
            policy_id: Policy identifier
            climate_risk_factors: Climate risk factors for the policy
            mitigation_status: Status of mitigation measures implementation
            model_confidence: Confidence levels for different climate models

        Returns:
            ExclusionDecision with exclusions and governance recommendations
        """
        excluded_risks = []
        coverage_status = {}
        decision_reasons = []

        # Evaluate unmodelable events (like climate-induced earthquakes with low confidence)
        if model_confidence and "climate_induced_seismicity" in model_confidence:
            confidence = model_confidence["climate_induced_seismicity"]
            if confidence < self.low_confidence_threshold:
                exclusion = self._create_exclusion(
                    policy_id, ClimateExclusionType.UNMODELABLE_EVENTS, confidence
                )
                excluded_risks.append(exclusion)
                coverage_status["climate_induced_seismicity"] = "excluded"
                decision_reasons.append(
                    f"Climate-induced seismicity model confidence too low: {confidence:.2f} < {self.low_confidence_threshold}"
                )

        # Evaluate mitigation failure
        if mitigation_status:
            if not self._check_mitigation_implementation(mitigation_status):
                exclusion = self._create_exclusion(
                    policy_id,
                    ClimateExclusionType.MITIGATION_FAILURE,
                    1.0,  # High confidence that mitigation failed
                )
                excluded_risks.append(exclusion)
                coverage_status["mitigation_failure"] = "covered_with_loading"
                decision_reasons.append(
                    "Client failed to implement required mitigation measures"
                )

        # Evaluate climate litigation risk (still immature)
        litigation_maturity = climate_risk_factors.get(
            "litigation_maturity", 0.2
        )  # Default low maturity
        if litigation_maturity < 0.4:  # Considered immature
            exclusion = self._create_exclusion(
                policy_id, ClimateExclusionType.CLIMATE_LITIGATION, litigation_maturity
            )
            excluded_risks.append(exclusion)
            coverage_status["climate_litigation"] = "excluded"
            decision_reasons.append(
                f"Climate litigation models not mature enough: {litigation_maturity:.2f} < 0.4 threshold"
            )

        # Calculate governance recommendations
        governance_recommendations = self._get_governance_recommendations(
            climate_risk_factors.get("scr_score", 0)
        )

        # Calculate premium adjustment based on exclusions
        premium_adjustment = self._calculate_premium_adjustment(excluded_risks)

        decision = ExclusionDecision(
            policy_id=policy_id,
            excluded_risks=excluded_risks,
            coverage_status=coverage_status,
            governance_recommendations=governance_recommendations,
            final_premium_adjustment=premium_adjustment,
            decision_timestamp=datetime.now(),
            decision_reasons=decision_reasons,
        )

        # Store the decision
        self.governance_decisions[policy_id] = decision

        logger.info(
            f"Exclusion evaluation completed for policy {policy_id}. "
            f"{len(excluded_risks)} risks excluded, "
            f"{len(governance_recommendations)} governance recommendations"
        )

        return decision

    def _create_exclusion(
        self,
        policy_id: str,
        exclusion_type: ClimateExclusionType,
        model_confidence: float,
    ) -> ClimateExclusion:
        """Create a climate exclusion based on the type and confidence"""
        definition = self.exclusion_definitions[exclusion_type]

        exclusion_id = f"EXCL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{policy_id[:8]}_{exclusion_type.value[:3].upper()}"

        # Determine coverage status based on confidence
        coverage_status = definition["coverage_status"]
        if (
            definition["confidence_threshold"] > 0
            and model_confidence < definition["confidence_threshold"]
        ):
            coverage_status = "excluded"

        exclusion = ClimateExclusion(
            exclusion_id=exclusion_id,
            exclusion_type=exclusion_type,
            risk_description=definition["description"],
            loading_factor=definition["loading_factor"],
            confidence_level=model_confidence,
            coverage_status=coverage_status,
            reason=definition["reason"],
            implementation_date=datetime.now(),
            review_date=datetime.now() + timedelta(days=365),  # Annual review
        )

        # Store the exclusion
        self.active_exclusions[exclusion_id] = exclusion

        return exclusion

    def _check_mitigation_implementation(
        self, mitigation_status: Dict[str, Any]
    ) -> bool:
        """Check if required mitigation measures have been implemented"""
        required_measures = mitigation_status.get("required_measures", [])
        implemented_measures = mitigation_status.get("implemented_measures", [])

        # Check if all required measures are implemented
        for required_measure in required_measures:
            if required_measure not in implemented_measures:
                return False
        return True

    def _get_governance_recommendations(self, scr_score: float) -> List[GovernanceRule]:
        """Get governance recommendations based on the SCR score"""
        recommendations = []

        for rule in self.governance_rules:
            if rule.status != "active":
                continue

            # Check if manual approval rule applies
            if (
                rule.rule_type == GovernanceRecommendation.MANUAL_APPROVAL_REQUIRED
                and scr_score > self.manual_approval_threshold
            ):
                recommendations.append(rule)
            # Check if quarterly/annual review applies
            elif rule.rule_type in [
                GovernanceRecommendation.QUARTERLY_COMMITTEE_REVIEW,
                GovernanceRecommendation.ANNUAL_EXTERNAL_AUDIT,
            ]:
                recommendations.append(rule)

        return recommendations

    def _calculate_premium_adjustment(
        self, excluded_risks: List[ClimateExclusion]
    ) -> float:
        """Calculate premium adjustment based on excluded risks"""
        # For risks that are covered with loading (500%), calculate adjustment
        loading_adjustment = 0.0

        for exclusion in excluded_risks:
            if exclusion.coverage_status == "covered_with_loading":
                # Apply the loading factor to the risk component
                loading_adjustment += exclusion.loading_factor

        return loading_adjustment

    def get_exclusion_decision(self, policy_id: str) -> Optional[ExclusionDecision]:
        """Get the exclusion decision for a specific policy"""
        return self.governance_decisions.get(policy_id)

    def get_upcoming_reviews(self) -> List[Tuple[str, datetime, str]]:
        """Get policies and exclusions requiring upcoming reviews"""
        upcoming_reviews = []

        # Check exclusions for review
        for exclusion_id, exclusion in self.active_exclusions.items():
            if exclusion.review_date <= datetime.now() + timedelta(
                days=30
            ):  # Next 30 days
                upcoming_reviews.append(
                    (exclusion_id, exclusion.review_date, "exclusion")
                )

        # Check governance decisions for review
        for policy_id, decision in self.governance_decisions.items():
            # For quarterly and annual reviews
            if decision.decision_timestamp.month % 3 == 0:  # Quarterly check
                next_quarterly_review = decision.decision_timestamp + timedelta(days=90)
                if next_quarterly_review <= datetime.now() + timedelta(days=30):
                    upcoming_reviews.append(
                        (policy_id, next_quarterly_review, "quarterly_governance")
                    )

            annual_review = decision.decision_timestamp + timedelta(days=365)
            if annual_review <= datetime.now() + timedelta(days=30):
                upcoming_reviews.append((policy_id, annual_review, "annual_governance"))

        return upcoming_reviews

    def update_governance_rule(self, rule_id: str, new_status: str) -> GovernanceRule:
        """Update the status of a governance rule"""
        for rule in self.governance_rules:
            if rule.rule_id == rule_id:
                rule.status = new_status
                rule.implementation_date = datetime.now()
                logger.info(f"Updated governance rule {rule_id} to status {new_status}")
                return rule

        raise ValueError(f"Governance rule {rule_id} not found")


# Global instance
smart_exclusions_service = SmartClimateExclusionsService()


def evaluate_climate_exclusions(
    policy_id: str,
    climate_risk_factors: Dict[str, Any],
    mitigation_status: Optional[Dict[str, Any]] = None,
    model_confidence: Optional[Dict[str, float]] = None,
) -> ExclusionDecision:
    """Convenience function to evaluate climate exclusions"""
    return smart_exclusions_service.evaluate_climate_exclusions(
        policy_id, climate_risk_factors, mitigation_status, model_confidence
    )


def get_exclusion_decision(policy_id: str) -> Optional[ExclusionDecision]:
    """Convenience function to get exclusion decision"""
    return smart_exclusions_service.get_exclusion_decision(policy_id)


def get_upcoming_reviews() -> List[Tuple[str, datetime, str]]:
    """Convenience function to get upcoming reviews"""
    return smart_exclusions_service.get_upcoming_reviews()


def update_governance_rule(rule_id: str, new_status: str) -> GovernanceRule:
    """Convenience function to update governance rule"""
    return smart_exclusions_service.update_governance_rule(rule_id, new_status)

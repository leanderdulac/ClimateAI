"""
Policy Uncertainty Clause Management Service
Handles the specific clause:
"O prêmio incorpora projeções climáticas com incerteza intrínseca de 35-60% para períodos >10 anos.
O segurador reserva o direito de revisão anual conforme novos dados CMIP7 ou eventos de calibragem."
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PolicyUncertaintyClause:
    """Data structure for policy uncertainty clause"""

    policy_id: str
    uncertainty_range_min: float  # 0.35 (35%)
    uncertainty_range_max: float  # 0.60 (60%)
    projection_horizon: int  # in years (e.g., 10 for >10 years)
    cmip_data_source: str  # e.g., "CMIP7"
    calibration_events_enabled: bool
    annual_review_clause: bool
    clause_text: str
    creation_date: datetime
    last_updated: datetime
    next_review_date: datetime


@dataclass
class CalibrationEvent:
    """Data structure for calibration events that may trigger policy review"""

    event_id: str
    event_type: (
        str  # "CMIP_data_release", "extreme_weather_event", "model_update", etc.
    )
    event_description: str
    event_date: datetime
    impact_on_uncertainty: float  # 0.0 to 1.0, how much this affects uncertainty
    policies_affected: List[str]
    triggered_review: bool
    review_reason: str


class PolicyUncertaintyService:
    """Service to handle policy uncertainty clauses and related functionality"""

    def __init__(self):
        # Default values from the specified clause
        self.default_uncertainty_min = 0.35  # 35%
        self.default_uncertainty_max = 0.60  # 60%
        self.default_horizon_years = 10  # >10 years
        self.default_cmip_source = "CMIP7"
        self.clause_text_template = (
            "O prêmio incorpora projeções climáticas com incerteza intrínseca de {min_pct:.0f}-{max_pct:.0f}% "
            "para períodos >{horizon} anos. O segurador reserva o direito de revisão anual conforme novos "
            "dados {cmip_source} ou eventos de calibragem."
        )

        # List of calibration events that can trigger policy reviews
        self.calibration_event_types = [
            "CMIP_data_release",  # New CMIP data releases (e.g., CMIP7)
            "extreme_weather_event",  # Severe climate events that calibrate models
            "model_update",  # Climate model updates and improvements
            "regulatory_change",  # New climate regulations affecting risk
            "scientific_discovery",  # New scientific findings affecting projections
            "data_quality_issue",  # Issues with data quality that require recalibration
        ]

        # Store active clauses and calibration events
        self.active_clauses: Dict[str, PolicyUncertaintyClause] = {}
        self.calibration_events: Dict[str, CalibrationEvent] = {}

    def create_uncertainty_clause(
        self,
        policy_id: str,
        uncertainty_min: Optional[float] = None,
        uncertainty_max: Optional[float] = None,
        projection_horizon: Optional[int] = None,
        cmip_source: Optional[str] = None,
    ) -> PolicyUncertaintyClause:
        """
        Create a policy uncertainty clause with the specified parameters

        Args:
            policy_id: The policy identifier
            uncertainty_min: Minimum uncertainty percentage (default 35%)
            uncertainty_max: Maximum uncertainty percentage (default 60%)
            projection_horizon: Projection horizon in years (default 10 for >10 years)
            cmip_source: Climate model intercomparison project source (default CMIP7)

        Returns:
            PolicyUncertaintyClause with the specified parameters
        """
        # Use defaults if not provided
        uncertainty_min = uncertainty_min or self.default_uncertainty_min
        uncertainty_max = uncertainty_max or self.default_uncertainty_max
        projection_horizon = projection_horizon or self.default_horizon_years
        cmip_source = cmip_source or self.default_cmip_source

        # Validate uncertainty ranges
        if (
            uncertainty_min < 0
            or uncertainty_max > 1
            or uncertainty_min > uncertainty_max
        ):
            raise ValueError(
                f"Uncertainty values must be between 0 and 1, with min <= max. Got: {uncertainty_min}, {uncertainty_max}"
            )

        # Create the clause text
        clause_text = self.clause_text_template.format(
            min_pct=uncertainty_min * 100,
            max_pct=uncertainty_max * 100,
            horizon=projection_horizon,
            cmip_source=cmip_source,
        )

        # Calculate next review date (annual review)
        next_review_date = datetime.now() + timedelta(days=365)

        clause = PolicyUncertaintyClause(
            policy_id=policy_id,
            uncertainty_range_min=uncertainty_min,
            uncertainty_range_max=uncertainty_max,
            projection_horizon=projection_horizon,
            cmip_data_source=cmip_source,
            calibration_events_enabled=True,
            annual_review_clause=True,
            clause_text=clause_text,
            creation_date=datetime.now(),
            last_updated=datetime.now(),
            next_review_date=next_review_date,
        )

        # Store the clause
        self.active_clauses[policy_id] = clause

        logger.info(
            f"Created uncertainty clause for policy {policy_id} with {uncertainty_min*100:.0f}-{uncertainty_max*100:.0f}% uncertainty"
        )
        return clause

    def get_uncertainty_clause(
        self, policy_id: str
    ) -> Optional[PolicyUncertaintyClause]:
        """Get the uncertainty clause for a specific policy"""
        return self.active_clauses.get(policy_id)

    def update_clause_for_cmip_data(
        self, policy_id: str, new_cmip_source: str
    ) -> PolicyUncertaintyClause:
        """Update a policy's clause when new CMIP data is released"""
        clause = self.active_clauses.get(policy_id)
        if not clause:
            raise ValueError(
                f"Policy {policy_id} does not have an active uncertainty clause"
            )

        # Update the CMIP source and reset the review date
        clause.cmip_data_source = new_cmip_source
        clause.last_updated = datetime.now()
        clause.next_review_date = datetime.now() + timedelta(
            days=365
        )  # Reset to annual review

        # Update the clause text
        clause.clause_text = self.clause_text_template.format(
            min_pct=clause.uncertainty_range_min * 100,
            max_pct=clause.uncertainty_range_max * 100,
            horizon=clause.projection_horizon,
            cmip_source=new_cmip_source,
        )

        logger.info(
            f"Updated uncertainty clause for policy {policy_id} with new CMIP source: {new_cmip_source}"
        )
        return clause

    def register_calibration_event(
        self,
        event_type: str,
        event_description: str,
        policies_affected: List[str],
        impact_on_uncertainty: float = 0.1,
    ) -> CalibrationEvent:
        """
        Register a calibration event that may affect policy uncertainty

        Args:
            event_type: Type of calibration event
            event_description: Description of the event
            policies_affected: List of policy IDs affected by this event
            impact_on_uncertainty: How much this event impacts uncertainty (0.0 to 1.0)

        Returns:
            CalibrationEvent object
        """
        if event_type not in self.calibration_event_types:
            raise ValueError(
                f"Invalid event type. Valid types: {self.calibration_event_types}"
            )

        if impact_on_uncertainty < 0 or impact_on_uncertainty > 1:
            raise ValueError("Impact on uncertainty must be between 0.0 and 1.0")

        event_id = (
            f"CE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{event_type[:3].upper()}"
        )

        event = CalibrationEvent(
            event_id=event_id,
            event_type=event_type,
            event_description=event_description,
            event_date=datetime.now(),
            impact_on_uncertainty=impact_on_uncertainty,
            policies_affected=policies_affected,
            triggered_review=True,
            review_reason=f"Calibration event ({event_type}) with impact {impact_on_uncertainty:.2f}",
        )

        # Store the event
        self.calibration_events[event_id] = event

        # Update clauses for affected policies
        for policy_id in policies_affected:
            if policy_id in self.active_clauses:
                clause = self.active_clauses[policy_id]
                clause.last_updated = datetime.now()
                # Adjust next review date based on event impact
                days_to_review = max(
                    30, int(365 * (1 - impact_on_uncertainty))
                )  # Higher impact = sooner review
                clause.next_review_date = datetime.now() + timedelta(
                    days=days_to_review
                )

        logger.info(
            f"Registered calibration event {event_id} affecting {len(policies_affected)} policies"
        )
        return event

    def get_policies_requiring_review(
        self, as_of_date: Optional[datetime] = None
    ) -> List[str]:
        """
        Get list of policies that require review based on current date

        Args:
            as_of_date: Date to check for required reviews (defaults to now)

        Returns:
            List of policy IDs requiring review
        """
        if as_of_date is None:
            as_of_date = datetime.now()

        policies_requiring_review = []
        for policy_id, clause in self.active_clauses.items():
            if clause.next_review_date <= as_of_date:
                policies_requiring_review.append(policy_id)

        # Also check for policies affected by recent calibration events
        # (Implementation would check recent events and their impact)

        return policies_requiring_review

    def calculate_adjusted_uncertainty(
        self, base_uncertainty: float, calibration_events: List[CalibrationEvent]
    ) -> float:
        """
        Calculate adjusted uncertainty based on calibration events

        Args:
            base_uncertainty: Base uncertainty value
            calibration_events: List of calibration events that may affect this policy

        Returns:
            Adjusted uncertainty value
        """
        adjustment_factor = 1.0
        for event in calibration_events:
            # Adjust uncertainty based on event impact
            adjustment_factor *= 1 + event.impact_on_uncertainty

        adjusted_uncertainty = base_uncertainty * adjustment_factor

        # Ensure it stays within reasonable bounds based on the original clause
        original_clause = (
            self.active_clauses.get(calibration_events[0].policies_affected[0])
            if calibration_events
            else None
        )
        if original_clause:
            min_uncertainty = original_clause.uncertainty_range_min
            max_uncertainty = original_clause.uncertainty_range_max
            adjusted_uncertainty = max(
                min_uncertainty, min(max_uncertainty, adjusted_uncertainty)
            )

        return adjusted_uncertainty


# Global instance
policy_uncertainty_service = PolicyUncertaintyService()


def create_uncertainty_clause(
    policy_id: str,
    uncertainty_min: Optional[float] = None,
    uncertainty_max: Optional[float] = None,
    projection_horizon: Optional[int] = None,
    cmip_source: Optional[str] = None,
) -> PolicyUncertaintyClause:
    """Convenience function to create a policy uncertainty clause"""
    return policy_uncertainty_service.create_uncertainty_clause(
        policy_id, uncertainty_min, uncertainty_max, projection_horizon, cmip_source
    )


def get_uncertainty_clause(policy_id: str) -> Optional[PolicyUncertaintyClause]:
    """Convenience function to get a policy uncertainty clause"""
    return policy_uncertainty_service.get_uncertainty_clause(policy_id)


def update_clause_for_cmip_data(
    policy_id: str, new_cmip_source: str
) -> PolicyUncertaintyClause:
    """Convenience function to update a clause for new CMIP data"""
    return policy_uncertainty_service.update_clause_for_cmip_data(
        policy_id, new_cmip_source
    )


def register_calibration_event(
    event_type: str,
    event_description: str,
    policies_affected: List[str],
    impact_on_uncertainty: float = 0.1,
) -> CalibrationEvent:
    """Convenience function to register a calibration event"""
    return policy_uncertainty_service.register_calibration_event(
        event_type, event_description, policies_affected, impact_on_uncertainty
    )


def get_policies_requiring_review(as_of_date: Optional[datetime] = None) -> List[str]:
    """Convenience function to get policies requiring review"""
    return policy_uncertainty_service.get_policies_requiring_review(as_of_date)


def calculate_adjusted_uncertainty(
    base_uncertainty: float, calibration_events: List[CalibrationEvent]
) -> float:
    """Convenience function to calculate adjusted uncertainty"""
    return policy_uncertainty_service.calculate_adjusted_uncertainty(
        base_uncertainty, calibration_events
    )

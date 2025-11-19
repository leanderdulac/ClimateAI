import pytest

from server.services.policy_valuation_service import (
    PolicyMetrics,
    PolicyValuationService,
    PolicyValuationTier,
)


def make_service() -> PolicyValuationService:
    return PolicyValuationService()


def test_poor_policy_always_triggers_high_priority_notification():
    service = make_service()
    metrics = PolicyMetrics(
        premium_amount=10,
        expected_claims=100,
        claim_frequency=0.9,
        claim_severity=50000,
        climate_risk_score=900,
        physical_risk=0.9,
        transition_risk=0.8,
        mitigation_effectiveness=0.1,
        model_confidence=0.3,
        concentration_risk=0.9,
        geographic_factor=0.8,
        regulatory_factor=0.7,
        economic_factor=0.8,
    )

    valuation = service.calculate_policy_valuation("POL_POOR", metrics)
    notifications = service.get_pending_notifications()

    assert valuation.valuation_tier == PolicyValuationTier.POOR
    assert valuation.notification_required is True
    assert valuation.notification_priority == 5
    assert len(notifications) == 1
    assert notifications[0]["priority"] == 5
    assert notifications[0]["policy_id"] == "POL_POOR"


def test_fair_policy_triggers_notification_with_priority():
    service = make_service()
    metrics = PolicyMetrics(
        premium_amount=160,
        expected_claims=80,
        claim_frequency=0.35,
        claim_severity=12000,
        climate_risk_score=450,
        physical_risk=0.35,
        transition_risk=0.35,
        mitigation_effectiveness=0.6,
        model_confidence=0.68,
        concentration_risk=0.25,
        geographic_factor=0.2,
        regulatory_factor=0.2,
        economic_factor=0.2,
    )

    valuation = service.calculate_policy_valuation("POL_FAIR", metrics)
    notifications = service.get_pending_notifications()

    assert valuation.valuation_tier == PolicyValuationTier.FAIR
    assert valuation.notification_required is True
    assert valuation.notification_priority == 4
    assert len(notifications) == 1
    assert notifications[0]["priority"] == 4
    assert notifications[0]["policy_id"] == "POL_FAIR"


def test_good_policy_high_confidence_notifies():
    service = make_service()
    metrics = PolicyMetrics(
        premium_amount=200,
        expected_claims=80,
        claim_frequency=0.2,
        claim_severity=10000,
        climate_risk_score=400,
        physical_risk=0.3,
        transition_risk=0.3,
        mitigation_effectiveness=0.7,
        model_confidence=0.85,
        concentration_risk=0.2,
        geographic_factor=0.2,
        regulatory_factor=0.2,
        economic_factor=0.2,
    )

    valuation = service.calculate_policy_valuation("POL_GOOD_CONF", metrics)
    notifications = service.get_pending_notifications()

    assert valuation.valuation_tier == PolicyValuationTier.GOOD
    assert valuation.notification_required is True
    assert valuation.notification_priority == 4
    assert len(notifications) == 1
    assert notifications[0]["policy_id"] == "POL_GOOD_CONF"


def test_good_policy_low_confidence_does_not_notify():
    service = make_service()
    metrics = PolicyMetrics(
        premium_amount=250,
        expected_claims=80,
        claim_frequency=0.2,
        claim_severity=10000,
        climate_risk_score=350,
        physical_risk=0.25,
        transition_risk=0.25,
        mitigation_effectiveness=0.75,
        model_confidence=0.6,
        concentration_risk=0.15,
        geographic_factor=0.15,
        regulatory_factor=0.2,
        economic_factor=0.2,
    )

    valuation = service.calculate_policy_valuation("POL_GOOD_LOWCONF", metrics)
    notifications = service.get_pending_notifications()

    assert valuation.valuation_tier == PolicyValuationTier.GOOD
    assert valuation.notification_required is False
    assert len(notifications) == 0

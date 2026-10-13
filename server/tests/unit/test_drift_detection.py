"""Unit tests for MLOps DriftDetectionService."""

import pytest
from services.drift_detection_service import (
    DriftDetectionService,
    DriftSeverity,
    FeatureDriftReport,
    ClimateDriftAssessment,
)


def test_psi_calculation_identical_distributions():
    service = DriftDetectionService()
    baseline = [20.0, 21.0, 22.0, 23.0, 24.0, 25.0] * 10
    current = [20.0, 21.0, 22.0, 23.0, 24.0, 25.0] * 10
    psi = service.calculate_psi(baseline, current)
    assert psi == pytest.approx(0.0, abs=0.05)


def test_psi_calculation_shifted_distributions():
    service = DriftDetectionService()
    baseline = [10.0, 11.0, 12.0, 13.0, 14.0] * 20
    # Heavy shift
    current = [30.0, 31.0, 32.0, 33.0, 34.0] * 20
    psi = service.calculate_psi(baseline, current)
    assert psi > 0.20


def test_feature_drift_no_drift():
    service = DriftDetectionService()
    baseline = [15.0 + (i % 5) for i in range(100)]
    current = [15.0 + (i % 5) for i in range(100)]

    report = service.detect_feature_drift(baseline, current, feature_name="temperature")
    assert isinstance(report, FeatureDriftReport)
    assert not report.drift_detected
    assert report.severity == DriftSeverity.NONE
    assert report.suggested_risk_margin_multiplier == 1.0


def test_feature_drift_severe_drift():
    service = DriftDetectionService()
    baseline = [10.0 + (i % 3) for i in range(100)]
    current = [35.0 + (i % 3) for i in range(100)]

    report = service.detect_feature_drift(baseline, current, feature_name="rainfall_mm")
    assert report.drift_detected
    assert report.suggested_risk_margin_multiplier > 1.0


def test_multivariate_climate_drift_assessment():
    service = DriftDetectionService()
    baseline_dataset = {
        "temperature": [20.0, 21.0, 22.0, 23.0] * 25,
        "precipitation": [5.0, 10.0, 15.0, 20.0] * 25,
    }
    current_dataset = {
        "temperature": [20.0, 21.0, 22.0, 23.0] * 25,
        "precipitation": [50.0, 70.0, 90.0, 120.0] * 25,  # extreme rainfall drift
    }

    assessment = service.assess_multivariate_climate_drift(baseline_dataset, current_dataset)
    assert isinstance(assessment, ClimateDriftAssessment)
    assert assessment.overall_drift_detected is True
    assert len(assessment.feature_reports) == 2
    assert assessment.recommended_actuarial_buffer >= 1.10

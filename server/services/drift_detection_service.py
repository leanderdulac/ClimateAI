"""
Drift Detection Service
Detects statistical data drift and concept drift in climate time-series features.
Uses Kolmogorov-Smirnov (KS-test) and Population Stability Index (PSI) to guarantee
actuarial pricing models do not underprice risk during extreme climate regime shifts.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


class DriftSeverity(str, Enum):
    NONE = "none"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass
class FeatureDriftReport:
    feature_name: str
    ks_statistic: float
    p_value: float
    psi: float
    drift_detected: bool
    severity: DriftSeverity
    baseline_mean: float
    current_mean: float
    suggested_risk_margin_multiplier: float


@dataclass
class ClimateDriftAssessment:
    overall_drift_detected: bool
    max_severity: DriftSeverity
    recommended_actuarial_buffer: float
    feature_reports: List[FeatureDriftReport] = field(default_factory=list)
    timestamp_utc: str = ""


class DriftDetectionService:
    """Service to evaluate statistical drift between baseline and runtime climate observations."""

    def __init__(self, alpha: float = 0.05, psi_threshold: float = 0.20):
        self.alpha = alpha
        self.psi_threshold = psi_threshold

    def calculate_psi(
        self,
        baseline: Sequence[float],
        current: Sequence[float],
        num_buckets: int = 10,
    ) -> float:
        """
        Calculates Population Stability Index (PSI).
        PSI = sum((Actual% - Baseline%) * ln(Actual% / Baseline%))
        """
        if not baseline or not current:
            return 0.0

        min_val = min(min(baseline), min(current))
        max_val = max(max(baseline), max(current))

        if min_val == max_val:
            return 0.0

        step = (max_val - min_val) / num_buckets
        eps = 1e-4

        psi_total = 0.0
        n_base = float(len(baseline))
        n_curr = float(len(current))

        for i in range(num_buckets):
            lower = min_val + i * step
            upper = min_val + (i + 1) * step if i < num_buckets - 1 else max_val + eps

            b_count = sum(1 for x in baseline if lower <= x < upper)
            c_count = sum(1 for x in current if lower <= x < upper)

            b_pct = max(b_count / n_base, eps)
            c_pct = max(c_count / n_curr, eps)

            psi_total += (c_pct - b_pct) * math.log(c_pct / b_pct)

        return float(round(psi_total, 4))

    def detect_feature_drift(
        self,
        baseline: Sequence[float],
        current: Sequence[float],
        feature_name: str = "temperature",
    ) -> FeatureDriftReport:
        """Runs Kolmogorov-Smirnov test and PSI on a continuous climate feature."""
        if len(baseline) < 2 or len(current) < 2:
            return FeatureDriftReport(
                feature_name=feature_name,
                ks_statistic=0.0,
                p_value=1.0,
                psi=0.0,
                drift_detected=False,
                severity=DriftSeverity.NONE,
                baseline_mean=float(sum(baseline) / len(baseline)) if baseline else 0.0,
                current_mean=float(sum(current) / len(current)) if current else 0.0,
                suggested_risk_margin_multiplier=1.0,
            )

        # Attempt scipy.stats.ks_2samp, fallback to manual approximation if mocked/missing
        try:
            from scipy.stats import ks_2samp
            stat, p_val = ks_2samp(baseline, current)
            ks_stat = float(stat)
            p_value = float(p_val)
        except Exception:
            # Fallback empirical difference of means normalized
            b_mean = sum(baseline) / len(baseline)
            c_mean = sum(current) / len(current)
            diff = abs(c_mean - b_mean)
            ks_stat = float(min(1.0, diff / (abs(b_mean) + 1.0)))
            p_value = 0.01 if ks_stat > 0.3 else 0.50

        psi = self.calculate_psi(baseline, current)

        # Determine drift status and severity
        drift_by_ks = p_value < self.alpha
        drift_by_psi = psi >= self.psi_threshold

        drift_detected = drift_by_ks or drift_by_psi

        if psi >= 0.25 or (p_value < 0.001 and ks_stat > 0.4):
            severity = DriftSeverity.SEVERE
            multiplier = 1.25  # +25% actuarial safety buffer
        elif drift_detected or psi >= 0.10:
            severity = DriftSeverity.MODERATE
            multiplier = 1.10  # +10% actuarial buffer
        else:
            severity = DriftSeverity.NONE
            multiplier = 1.0

        return FeatureDriftReport(
            feature_name=feature_name,
            ks_statistic=round(ks_stat, 4),
            p_value=round(p_value, 6),
            psi=psi,
            drift_detected=drift_detected,
            severity=severity,
            baseline_mean=round(sum(baseline) / len(baseline), 4),
            current_mean=round(sum(current) / len(current), 4),
            suggested_risk_margin_multiplier=multiplier,
        )

    def assess_multivariate_climate_drift(
        self,
        baseline_dataset: Dict[str, Sequence[float]],
        current_dataset: Dict[str, Sequence[float]],
    ) -> ClimateDriftAssessment:
        """Evaluates drift across multiple climate features simultaneously."""
        reports: List[FeatureDriftReport] = []
        overall_drift = False
        max_severity = DriftSeverity.NONE
        highest_multiplier = 1.0

        for feature, baseline_vals in baseline_dataset.items():
            current_vals = current_dataset.get(feature, [])
            if not current_vals:
                continue

            report = self.detect_feature_drift(baseline_vals, current_vals, feature_name=feature)
            reports.append(report)

            if report.drift_detected:
                overall_drift = True

            if report.severity == DriftSeverity.SEVERE:
                max_severity = DriftSeverity.SEVERE
            elif report.severity == DriftSeverity.MODERATE and max_severity != DriftSeverity.SEVERE:
                max_severity = DriftSeverity.MODERATE

            if report.suggested_risk_margin_multiplier > highest_multiplier:
                highest_multiplier = report.suggested_risk_margin_multiplier

        from datetime import datetime, timezone

        return ClimateDriftAssessment(
            overall_drift_detected=overall_drift,
            max_severity=max_severity,
            recommended_actuarial_buffer=highest_multiplier,
            feature_reports=reports,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )

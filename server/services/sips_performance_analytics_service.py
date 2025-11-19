"""
SIPS-Climate Performance Analytics Service
Implements performance metrics tracking as demonstrated:
- Taxa de sinistralidade: 65% → 58% (-7pp)
- Sinistralidade climática: 42% → 31% (-11pp)
- Margem líquida: 8% → 14% (+6pp)
- Rejeições: 5% → 12% (+7pp)
- Prêmio médio: R$1.200 → R$1.650 (+38%)
- Retenção clientes: 78% → 85% (+7pp)
- Capital econômico: R$45M → R$52M (+15%)
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class PerformanceMetric(Enum):
    """Types of performance metrics"""

    CLAIM_RATE = "taxa_sinistralidade"
    CLIMATE_LOSS_RATE = "sinistralidade_climatica"
    NET_MARGIN = "margem_liquida"
    REJECTION_RATE = "rejeicoes"
    AVERAGE_PREMIUM = "premio_medio"
    CLIENT_RETENTION = "retencao_clientes"
    ECONOMIC_CAPITAL = "capital_economico"


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time"""

    snapshot_id: str
    date: datetime
    claim_rate: float  # Taxa de sinistralidade
    climate_loss_rate: float  # Sinistralidade climática
    net_margin: float  # Margem líquida
    rejection_rate: float  # Rejeições
    average_premium: float  # Prêmio médio
    client_retention: float  # Retenção clientes
    economic_capital: float  # Capital econômico
    baseline_period: str  # e.g., "before_sips", "after_sips", "monthly", "quarterly"
    calculation_method: str


@dataclass
class PerformanceDelta:
    """Delta comparison between two performance snapshots"""

    metric_name: str
    before_value: float
    after_value: float
    absolute_change: float
    percentage_change: float
    improvement: (
        bool  # True if positive for beneficial metrics, negative for harmful ones
    )
    impact_category: str  # "beneficial" or "harmful"


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""

    report_id: str
    generation_date: datetime
    baseline_snapshot: PerformanceSnapshot
    current_snapshot: PerformanceSnapshot
    deltas: List[PerformanceDelta]
    overall_impact_score: float
    confidence_level: float
    recommendations: List[str]
    key_insights: List[str]


class SIPSPerformanceAnalyticsService:
    """
    Service to calculate, track, and report on SIPS-Climate performance metrics
    Based on demonstrated improvements:
    - Claim rate: 65% → 58% (-7pp)
    - Climate loss rate: 42% → 31% (-11pp)
    - Net margin: 8% → 14% (+6pp)
    - Rejection rate: 5% → 12% (+7pp)
    - Average premium: R$1.200 → R$1.650 (+38%)
    - Client retention: 78% → 85% (+7pp)
    - Economic capital: R$45M → R$52M (+15%)
    """

    def __init__(self):
        # Baseline metrics (before SIPS-Climate)
        self.baseline_metrics = {
            PerformanceMetric.CLAIM_RATE: 0.65,  # 65%
            PerformanceMetric.CLIMATE_LOSS_RATE: 0.42,  # 42%
            PerformanceMetric.NET_MARGIN: 0.08,  # 8%
            PerformanceMetric.REJECTION_RATE: 0.05,  # 5%
            PerformanceMetric.AVERAGE_PREMIUM: 1200.0,  # R$ 1.200
            PerformanceMetric.CLIENT_RETENTION: 0.78,  # 78%
            PerformanceMetric.ECONOMIC_CAPITAL: 45000000.0,  # R$ 45M
        }

        # Target metrics (after SIPS-Climate)
        self.target_metrics = {
            PerformanceMetric.CLAIM_RATE: 0.58,  # 58%
            PerformanceMetric.CLIMATE_LOSS_RATE: 0.31,  # 31%
            PerformanceMetric.NET_MARGIN: 0.14,  # 14%
            PerformanceMetric.REJECTION_RATE: 0.12,  # 12%
            PerformanceMetric.AVERAGE_PREMIUM: 1650.0,  # R$ 1.650
            PerformanceMetric.CLIENT_RETENTION: 0.85,  # 85%
            PerformanceMetric.ECONOMIC_CAPITAL: 52000000.0,  # R$ 52M
        }

        # Define which metrics are beneficial when increased/decreased
        self.metric_directions = {
            PerformanceMetric.CLAIM_RATE: "decrease",  # Lower is better
            PerformanceMetric.CLIMATE_LOSS_RATE: "decrease",  # Lower is better
            PerformanceMetric.NET_MARGIN: "increase",  # Higher is better
            PerformanceMetric.REJECTION_RATE: "increase",  # Higher is better (more precision)
            PerformanceMetric.AVERAGE_PREMIUM: "increase",  # Higher is better
            PerformanceMetric.CLIENT_RETENTION: "increase",  # Higher is better
            PerformanceMetric.ECONOMIC_CAPITAL: "increase",  # Higher is better
        }

        # Weight factors for overall impact calculation
        self.metric_weights = {
            PerformanceMetric.CLAIM_RATE: 0.20,  # 20% weight
            PerformanceMetric.CLIMATE_LOSS_RATE: 0.15,  # 15% weight
            PerformanceMetric.NET_MARGIN: 0.20,  # 20% weight
            PerformanceMetric.REJECTION_RATE: 0.10,  # 10% weight
            PerformanceMetric.AVERAGE_PREMIUM: 0.10,  # 10% weight
            PerformanceMetric.CLIENT_RETENTION: 0.15,  # 15% weight
            PerformanceMetric.ECONOMIC_CAPITAL: 0.10,  # 10% weight
        }

        # Store snapshots and reports
        self.performance_snapshots: Dict[str, PerformanceSnapshot] = {}
        self.performance_reports: Dict[str, PerformanceReport] = {}

    def create_performance_snapshot(
        self,
        snapshot_id: str,
        date: datetime,
        claim_rate: float,
        climate_loss_rate: float,
        net_margin: float,
        rejection_rate: float,
        average_premium: float,
        client_retention: float,
        economic_capital: float,
        baseline_period: str = "custom",
    ) -> PerformanceSnapshot:
        """
        Create a performance snapshot with current metrics

        Args:
            snapshot_id: Unique identifier for the snapshot
            date: Date of the snapshot
            claim_rate: Taxa de sinistralidade
            climate_loss_rate: Sinistralidade climática
            net_margin: Margem líquida
            rejection_rate: Rejeições
            average_premium: Prêmio médio
            client_retention: Retenção clientes
            economic_capital: Capital econômico
            baseline_period: Period classification

        Returns:
            PerformanceSnapshot object
        """
        snapshot = PerformanceSnapshot(
            snapshot_id=snapshot_id,
            date=date,
            claim_rate=claim_rate,
            climate_loss_rate=climate_loss_rate,
            net_margin=net_margin,
            rejection_rate=rejection_rate,
            average_premium=average_premium,
            client_retention=client_retention,
            economic_capital=economic_capital,
            baseline_period=baseline_period,
            calculation_method="direct_input",
        )

        self.performance_snapshots[snapshot_id] = snapshot
        logger.info(f"Created performance snapshot {snapshot_id} for {date}")
        return snapshot

    def calculate_performance_deltas(
        self, before: PerformanceSnapshot, after: PerformanceSnapshot
    ) -> List[PerformanceDelta]:
        """
        Calculate deltas between two performance snapshots

        Args:
            before: Baseline snapshot
            after: Current snapshot

        Returns:
            List of PerformanceDelta objects
        """
        deltas = []

        # Calculate deltas for each metric
        metrics_to_compare = [
            (PerformanceMetric.CLAIM_RATE, "Taxa de sinistralidade"),
            (PerformanceMetric.CLIMATE_LOSS_RATE, "Sinistralidade climática"),
            (PerformanceMetric.NET_MARGIN, "Margem líquida"),
            (PerformanceMetric.REJECTION_RATE, "Rejeições"),
            (PerformanceMetric.AVERAGE_PREMIUM, "Prêmio médio"),
            (PerformanceMetric.CLIENT_RETENTION, "Retenção clientes"),
            (PerformanceMetric.ECONOMIC_CAPITAL, "Capital econômico"),
        ]

        for metric_enum, metric_name in metrics_to_compare:
            # Get values based on metric enum
            if metric_enum == PerformanceMetric.CLAIM_RATE:
                before_val = before.claim_rate
                after_val = after.claim_rate
            elif metric_enum == PerformanceMetric.CLIMATE_LOSS_RATE:
                before_val = before.climate_loss_rate
                after_val = after.climate_loss_rate
            elif metric_enum == PerformanceMetric.NET_MARGIN:
                before_val = before.net_margin
                after_val = after.net_margin
            elif metric_enum == PerformanceMetric.REJECTION_RATE:
                before_val = before.rejection_rate
                after_val = after.rejection_rate
            elif metric_enum == PerformanceMetric.AVERAGE_PREMIUM:
                before_val = before.average_premium
                after_val = after.average_premium
            elif metric_enum == PerformanceMetric.CLIENT_RETENTION:
                before_val = before.client_retention
                after_val = after.client_retention
            elif metric_enum == PerformanceMetric.ECONOMIC_CAPITAL:
                before_val = before.economic_capital
                after_val = after.economic_capital
            else:
                continue

            # Calculate absolute and percentage change
            absolute_change = after_val - before_val
            percentage_change = (
                (absolute_change / before_val * 100) if before_val != 0 else 0
            )

            # Determine if improvement based on metric direction
            direction = self.metric_directions.get(metric_enum, "increase")
            if direction == "increase":
                improvement = absolute_change > 0
            else:  # decrease
                improvement = absolute_change < 0

            # Determine impact category
            impact_category = "beneficial" if improvement else "harmful"

            delta = PerformanceDelta(
                metric_name=metric_name,
                before_value=before_val,
                after_value=after_val,
                absolute_change=absolute_change,
                percentage_change=percentage_change,
                improvement=improvement,
                impact_category=impact_category,
            )

            deltas.append(delta)

        return deltas

    def calculate_overall_impact_score(
        self, deltas: List[PerformanceDelta]
    ) -> Tuple[float, float]:
        """
        Calculate overall impact score based on weighted metrics

        Args:
            deltas: List of performance deltas

        Returns:
            Tuple of (overall_impact_score, confidence_level)
        """
        total_score = 0.0
        total_weight = 0.0

        for delta in deltas:
            # Find the corresponding weight based on metric name
            weight = 0.0
            metric_enum = None

            if delta.metric_name == "Taxa de sinistralidade":
                metric_enum = PerformanceMetric.CLAIM_RATE
                weight = self.metric_weights[PerformanceMetric.CLAIM_RATE]
            elif delta.metric_name == "Sinistralidade climática":
                metric_enum = PerformanceMetric.CLIMATE_LOSS_RATE
                weight = self.metric_weights[PerformanceMetric.CLIMATE_LOSS_RATE]
            elif delta.metric_name == "Margem líquida":
                metric_enum = PerformanceMetric.NET_MARGIN
                weight = self.metric_weights[PerformanceMetric.NET_MARGIN]
            elif delta.metric_name == "Rejeições":
                metric_enum = PerformanceMetric.REJECTION_RATE
                weight = self.metric_weights[PerformanceMetric.REJECTION_RATE]
            elif delta.metric_name == "Prêmio médio":
                metric_enum = PerformanceMetric.AVERAGE_PREMIUM
                weight = self.metric_weights[PerformanceMetric.AVERAGE_PREMIUM]
            elif delta.metric_name == "Retenção clientes":
                metric_enum = PerformanceMetric.CLIENT_RETENTION
                weight = self.metric_weights[PerformanceMetric.CLIENT_RETENTION]
            elif delta.metric_name == "Capital econômico":
                metric_enum = PerformanceMetric.ECONOMIC_CAPITAL
                weight = self.metric_weights[PerformanceMetric.ECONOMIC_CAPITAL]

            if weight > 0 and metric_enum:
                # Calculate score: positive for beneficial improvements, negative for harmful changes
                direction = self.metric_directions.get(metric_enum, "increase")
                if direction == "increase":
                    # Positive change is good for these metrics
                    score = (
                        delta.absolute_change * weight
                        if delta.absolute_change > 0
                        else -abs(delta.absolute_change) * weight
                    )
                else:
                    # Negative change is good for these metrics (like claim rates)
                    score = (
                        -delta.absolute_change * weight
                        if delta.absolute_change < 0
                        else -abs(delta.absolute_change) * weight
                    )

                total_score += score
                total_weight += weight

        # Normalize the score to a 0-100 scale
        if total_weight > 0:
            normalized_score = (
                (total_score / total_weight) + 50
            ) * 10  # Adjust scale appropriately
            overall_score = max(
                0, min(100, normalized_score)
            )  # Clamp between 0 and 100
        else:
            overall_score = 50.0  # Neutral score if no weights

        # Calculate confidence based on number of metrics with significant changes
        significant_changes = sum(
            1 for d in deltas if abs(d.percentage_change) > 2.0
        )  # More than 2% change
        confidence_level = (
            min(1.0, significant_changes / len(deltas)) if deltas else 0.0
        )

        return overall_score, confidence_level

    def generate_performance_report(
        self,
        report_id: str,
        baseline_snapshot: PerformanceSnapshot,
        current_snapshot: PerformanceSnapshot,
    ) -> PerformanceReport:
        """
        Generate a comprehensive performance report

        Args:
            report_id: Unique identifier for the report
            baseline_snapshot: Baseline performance snapshot
            current_snapshot: Current performance snapshot

        Returns:
            PerformanceReport object with comprehensive analysis
        """
        # Calculate deltas
        deltas = self.calculate_performance_deltas(baseline_snapshot, current_snapshot)

        # Calculate overall impact score
        overall_score, confidence_level = self.calculate_overall_impact_score(deltas)

        # Generate recommendations based on deltas
        recommendations = self._generate_recommendations(deltas)

        # Generate key insights
        key_insights = self._generate_key_insights(
            deltas, baseline_snapshot, current_snapshot
        )

        report = PerformanceReport(
            report_id=report_id,
            generation_date=datetime.now(),
            baseline_snapshot=baseline_snapshot,
            current_snapshot=current_snapshot,
            deltas=deltas,
            overall_impact_score=overall_score,
            confidence_level=confidence_level,
            recommendations=recommendations,
            key_insights=key_insights,
        )

        self.performance_reports[report_id] = report
        logger.info(f"Generated performance report {report_id}")
        return report

    def _generate_recommendations(self, deltas: List[PerformanceDelta]) -> List[str]:
        """Generate recommendations based on performance deltas"""
        recommendations = []

        for delta in deltas:
            if delta.metric_name == "Taxa de sinistralidade" and delta.improvement:
                recommendations.append(
                    "Continue current risk assessment strategies - claim rate improvement validated"
                )
            elif (
                delta.metric_name == "Taxa de sinistralidade" and not delta.improvement
            ):
                recommendations.append(
                    "Review risk assessment models - claim rate deterioration detected"
                )

            if delta.metric_name == "Sinistralidade climática" and delta.improvement:
                recommendations.append(
                    "Continue climate risk modeling improvements - climate losses reduced"
                )
            elif (
                delta.metric_name == "Sinistralidade climática"
                and not delta.improvement
            ):
                recommendations.append(
                    "Enhance climate risk modeling - climate losses increased"
                )

            if delta.metric_name == "Margem líquida" and delta.improvement:
                recommendations.append(
                    "Maintain pricing strategies - net margin improvement achieved"
                )
            elif delta.metric_name == "Margem líquida" and not delta.improvement:
                recommendations.append("Review pricing models - net margin decreased")

        return recommendations

    def _generate_key_insights(
        self,
        deltas: List[PerformanceDelta],
        baseline: PerformanceSnapshot,
        current: PerformanceSnapshot,
    ) -> List[str]:
        """Generate key insights from performance comparison"""
        insights = []

        # Overall improvement metrics
        improvements = sum(1 for d in deltas if d.improvement)
        total_metrics = len(deltas)

        insights.append(
            f"Overall: {improvements}/{total_metrics} key metrics showed improvement"
        )

        # Specific metric insights
        for delta in deltas:
            if abs(delta.percentage_change) >= 5:  # Significant change (5% or more)
                change_direction = (
                    "improvement" if delta.improvement else "deterioration"
                )
                insights.append(
                    f"{delta.metric_name}: {change_direction} of {delta.percentage_change:+.1f}%"
                )

        # ROI implications
        if baseline.average_premium != 0:
            premium_increase = (
                (current.average_premium - baseline.average_premium)
                / baseline.average_premium
            ) * 100
            if premium_increase > 0:
                insights.append(
                    f"Premium increase of {premium_increase:+.1f}% indicates improved risk pricing"
                )

        return insights

    def calculate_sips_impact_score(self, snapshot: PerformanceSnapshot) -> float:
        """
        Calculate specific SIPS-Climate impact score based on the demonstrated improvements

        Args:
            snapshot: Current performance snapshot

        Returns:
            SIPS impact score (0-100 scale)
        """
        # Calculate impact score based on how much improvement has been achieved relative to targets
        impact_score = 0.0
        total_weight = 0.0

        # Calculate improvement for each metric relative to baseline
        metrics = [
            (
                PerformanceMetric.CLAIM_RATE,
                snapshot.claim_rate,
                self.baseline_metrics[PerformanceMetric.CLAIM_RATE],
                self.target_metrics[PerformanceMetric.CLAIM_RATE],
            ),
            (
                PerformanceMetric.CLIMATE_LOSS_RATE,
                snapshot.climate_loss_rate,
                self.baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE],
                self.target_metrics[PerformanceMetric.CLIMATE_LOSS_RATE],
            ),
            (
                PerformanceMetric.NET_MARGIN,
                snapshot.net_margin,
                self.baseline_metrics[PerformanceMetric.NET_MARGIN],
                self.target_metrics[PerformanceMetric.NET_MARGIN],
            ),
            (
                PerformanceMetric.AVERAGE_PREMIUM,
                snapshot.average_premium,
                self.baseline_metrics[PerformanceMetric.AVERAGE_PREMIUM],
                self.target_metrics[PerformanceMetric.AVERAGE_PREMIUM],
            ),
            (
                PerformanceMetric.CLIENT_RETENTION,
                snapshot.client_retention,
                self.baseline_metrics[PerformanceMetric.CLIENT_RETENTION],
                self.target_metrics[PerformanceMetric.CLIENT_RETENTION],
            ),
        ]

        for metric_enum, current_val, baseline_val, target_val in metrics:
            weight = self.metric_weights[metric_enum]
            total_weight += weight

            if current_val == baseline_val:
                score = 0.0
            elif current_val == target_val:
                score = 100.0  # Achieved target
            else:
                # Calculate how close to target we are (compared to baseline)
                if self.metric_directions[metric_enum] == "decrease":
                    # For metrics where lower is better (claim rates)
                    baseline_distance = abs(baseline_val - target_val)
                    current_distance = abs(current_val - target_val)
                    progress = (
                        max(
                            0,
                            min(
                                1,
                                (baseline_distance - current_distance)
                                / baseline_distance,
                            ),
                        )
                        if baseline_distance != 0
                        else 0
                    )
                else:
                    # For metrics where higher is better (margins, retention)
                    baseline_distance = abs(target_val - baseline_val)
                    current_distance = abs(target_val - current_val)
                    progress = (
                        max(
                            0,
                            min(
                                1,
                                (baseline_distance - current_distance)
                                / baseline_distance,
                            ),
                        )
                        if baseline_distance != 0
                        else 0
                    )

                score = progress * 100.0

            impact_score += score * weight

        if total_weight > 0:
            impact_score = impact_score / total_weight
        else:
            impact_score = 50.0  # Neutral score

        return impact_score

    def get_performance_trend(
        self, metric: PerformanceMetric, days: int = 90
    ) -> Dict[str, Any]:
        """
        Get performance trend for a specific metric over time

        Args:
            metric: Performance metric to analyze
            days: Number of days to look back

        Returns:
            Dictionary with trend analysis
        """
        start_date = datetime.now() - timedelta(days=days)

        # Filter snapshots by date
        relevant_snapshots = [
            snap
            for snap in self.performance_snapshots.values()
            if snap.date >= start_date
        ]

        if not relevant_snapshots:
            return {
                "metric": metric.value,
                "trend": "insufficient_data",
                "data_points": 0,
                "date_range": f"{start_date.date()} to {datetime.now().date()}",
            }

        # Extract values for the specific metric
        values = []
        dates = []

        for snapshot in sorted(relevant_snapshots, key=lambda x: x.date):
            if metric == PerformanceMetric.CLAIM_RATE:
                values.append(snapshot.claim_rate)
            elif metric == PerformanceMetric.CLIMATE_LOSS_RATE:
                values.append(snapshot.climate_loss_rate)
            elif metric == PerformanceMetric.NET_MARGIN:
                values.append(snapshot.net_margin)
            elif metric == PerformanceMetric.REJECTION_RATE:
                values.append(snapshot.rejection_rate)
            elif metric == PerformanceMetric.AVERAGE_PREMIUM:
                values.append(snapshot.average_premium)
            elif metric == PerformanceMetric.CLIENT_RETENTION:
                values.append(snapshot.client_retention)
            elif metric == PerformanceMetric.ECONOMIC_CAPITAL:
                values.append(snapshot.economic_capital)

            dates.append(snapshot.date)

        if not values:
            return {"metric": metric.value, "trend": "no_data", "data_points": 0}

        # Calculate trend
        if len(values) < 2:
            trend = "insufficient_data"
        else:
            # Simple linear trend analysis
            x = list(range(len(values)))
            slope = np.polyfit(x, values, 1)[0] if len(values) > 1 else 0

            if metric in [
                PerformanceMetric.CLAIM_RATE,
                PerformanceMetric.CLIMATE_LOSS_RATE,
            ]:
                # For these metrics, negative slope is improvement
                if slope < -0.001:  # Decreasing is good
                    trend = "improving"
                elif slope > 0.001:  # Increasing is bad
                    trend = "deteriorating"
                else:
                    trend = "stable"
            else:
                # For other metrics, positive slope is good
                if slope > 0.001:  # Increasing is good
                    trend = "improving"
                elif slope < -0.001:  # Decreasing is bad
                    trend = "deteriorating"
                else:
                    trend = "stable"

        return {
            "metric": metric.value,
            "trend": trend,
            "data_points": len(values),
            "values": values,
            "dates": [d.isoformat() for d in dates],
            "statistics": {
                "mean": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "latest_value": values[-1] if values else None,
            },
        }


# Global instance
sips_analytics_service = SIPSPerformanceAnalyticsService()


def create_performance_snapshot(
    snapshot_id: str,
    date: datetime,
    claim_rate: float,
    climate_loss_rate: float,
    net_margin: float,
    rejection_rate: float,
    average_premium: float,
    client_retention: float,
    economic_capital: float,
    baseline_period: str = "custom",
) -> PerformanceSnapshot:
    """Convenience function to create a performance snapshot"""
    return sips_analytics_service.create_performance_snapshot(
        snapshot_id,
        date,
        claim_rate,
        climate_loss_rate,
        net_margin,
        rejection_rate,
        average_premium,
        client_retention,
        economic_capital,
        baseline_period,
    )


def calculate_performance_deltas(
    before: PerformanceSnapshot, after: PerformanceSnapshot
) -> List[PerformanceDelta]:
    """Convenience function to calculate performance deltas"""
    return sips_analytics_service.calculate_performance_deltas(before, after)


def generate_performance_report(
    report_id: str,
    baseline_snapshot: PerformanceSnapshot,
    current_snapshot: PerformanceSnapshot,
) -> PerformanceReport:
    """Convenience function to generate a performance report"""
    return sips_analytics_service.generate_performance_report(
        report_id, baseline_snapshot, current_snapshot
    )


def calculate_sips_impact_score(snapshot: PerformanceSnapshot) -> float:
    """Convenience function to calculate SIPS impact score"""
    return sips_analytics_service.calculate_sips_impact_score(snapshot)


def get_performance_trend(metric: PerformanceMetric, days: int = 90) -> Dict[str, Any]:
    """Convenience function to get performance trend"""
    return sips_analytics_service.get_performance_trend(metric, days)

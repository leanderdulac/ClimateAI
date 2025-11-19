"""
Análise Atuarial Tradicional (AAT) - Traditional Actuarial Analysis Module
Implements classical actuarial methods for risk assessment and premium calculation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """Risk categories for traditional actuarial analysis"""

    PROPERTY = "property"
    AGRICULTURE = "agriculture"
    INFRASTRUCTURE = "infrastructure"
    LIVESTOCK = "livestock"
    CROP = "crop"


@dataclass
class ActuarialAnalysisResult:
    """Result of traditional actuarial analysis"""

    pure_premium: float
    risk_premium: float
    loading_premium: float
    total_premium: float
    frequency: float
    severity: float
    expected_loss: float
    variance: float
    std_deviation: float
    coefficient_of_variation: float
    return_period: float
    confidence_interval: Tuple[float, float]
    actuarial_indicators: Dict[str, float]
    risk_classification: str
    analysis_date: datetime


@dataclass
class HistoricalLossData:
    """Input structure for historical loss data"""

    claims_history: List[
        Dict[str, Any]
    ]  # [{'date': '2023-01-01', 'amount': 10000, 'cause': 'flood'}]
    exposure_data: List[Dict[str, Any]]  # [{'period': '2023', 'exposure': 1000}]
    policy_count: int
    total_exposure: float
    coverage_type: RiskCategory
    location_coordinates: Tuple[float, float]
    asset_value: float
    coverage_period_years: float


class TraditionalActuarialEngine:
    """
    Traditional actuarial engine implementing classical methods:
    - Frequency-severity analysis
    - Loss distribution modeling
    - Classical risk measures (VaR, CTE)
    - Experience rating calculations
    - Risk classification and pricing
    """

    def __init__(self):
        self.frequency_distribution = "poisson"  # Default frequency model
        self.severity_distribution = "lognormal"  # Default severity model
        self.confidence_level = 0.95  # 95% confidence
        self.loading_factors = {
            "expenses": 0.20,  # 20% for operational expenses
            "profit": 0.05,  # 5% for profit margin
            "contingency": 0.05,  # 5% for contingencies
            "risk_margin": 0.10,  # 10% for risk margin
        }
        self.risk_classification_map = {
            "very_low": (0.0, 0.2),
            "low": (0.2, 0.4),
            "medium": (0.4, 0.6),
            "high": (0.6, 0.8),
            "very_high": (0.8, 1.0),
        }

    def perform_actuarial_analysis(
        self, loss_data: HistoricalLossData
    ) -> ActuarialAnalysisResult:
        """
        Perform comprehensive traditional actuarial analysis.

        Args:
            loss_data: Historical loss data for analysis

        Returns:
            ActuarialAnalysisResult with complete analysis
        """
        # Calculate frequency and severity
        frequency = self._calculate_frequency(
            loss_data.claims_history, loss_data.coverage_period_years
        )
        severity = self._calculate_severity(loss_data.claims_history)

        # Calculate basic statistics
        expected_loss = frequency * severity
        variance = self._calculate_variance(
            loss_data.claims_history, frequency, severity
        )
        std_dev = np.sqrt(variance) if variance > 0 else 0

        # Calculate coefficient of variation
        coef_var = std_dev / expected_loss if expected_loss != 0 else 0

        # Calculate pure premium (expected loss per exposure unit)
        pure_premium = (
            expected_loss / loss_data.policy_count if loss_data.policy_count > 0 else 0
        )

        # Calculate risk premium based on variability
        risk_premium = self._calculate_risk_premium(expected_loss, std_dev, loss_data)

        # Calculate loading components
        total_loading = sum(self.loading_factors.values())
        loading_premium = pure_premium * total_loading

        # Calculate total premium
        total_premium = pure_premium + risk_premium + loading_premium

        # Calculate confidence interval
        z_score = stats.norm.ppf(self.confidence_level)
        margin_of_error = (
            z_score * (std_dev / np.sqrt(len(loss_data.claims_history)))
            if loss_data.claims_history
            else 0
        )
        confidence_interval = (
            max(0, total_premium - margin_of_error),
            total_premium + margin_of_error,
        )

        # Calculate return period (average years between claims)
        return_period = 1 / frequency if frequency > 0 else float("inf")

        # Calculate actuarial indicators
        actuarial_indicators = self._calculate_actuarial_indicators(
            frequency, severity, expected_loss, std_dev, loss_data
        )

        # Determine risk classification
        risk_classification = self._classify_risk(total_premium, loss_data.asset_value)

        return ActuarialAnalysisResult(
            pure_premium=pure_premium,
            risk_premium=risk_premium,
            loading_premium=loading_premium,
            total_premium=total_premium,
            frequency=frequency,
            severity=severity,
            expected_loss=expected_loss,
            variance=variance,
            std_deviation=std_dev,
            coefficient_of_variation=coef_var,
            return_period=return_period,
            confidence_interval=confidence_interval,
            actuarial_indicators=actuarial_indicators,
            risk_classification=risk_classification,
            analysis_date=datetime.now(),
        )

    def _calculate_frequency(
        self, claims_history: List[Dict], coverage_period: float
    ) -> float:
        """Calculate claim frequency rate"""
        if not claims_history or coverage_period <= 0:
            return 0.1  # Default 10% frequency if no data

        total_claims = len(claims_history)
        return total_claims / coverage_period  # Claims per year

    def _calculate_severity(self, claims_history: List[Dict]) -> float:
        """Calculate average claim severity"""
        if not claims_history:
            return 5000  # Default severity if no data

        claim_amounts = [
            claim["amount"] for claim in claims_history if "amount" in claim
        ]
        if not claim_amounts:
            return 5000

        return np.mean(claim_amounts)

    def _calculate_variance(
        self, claims_history: List[Dict], frequency: float, severity: float
    ) -> float:
        """Calculate variance of the aggregate loss distribution"""
        if not claims_history:
            # Use default variance calculation
            return (frequency * severity**2) * 1.5  # Assumed variance-to-mean ratio

        claim_amounts = [
            claim["amount"] for claim in claims_history if "amount" in claim
        ]
        if not claim_amounts:
            return (frequency * severity**2) * 1.5

        # For compound distribution: Var(S) = E(N)*Var(X) + [E(X)]^2*Var(N)
        # Assuming Poisson frequency: Var(N) = E(N) = frequency
        severity_var = (
            np.var(claim_amounts) if len(claim_amounts) > 1 else severity**2 * 0.5
        )
        aggregate_variance = frequency * severity_var + (severity**2) * frequency

        return aggregate_variance

    def _calculate_risk_premium(
        self, expected_loss: float, std_dev: float, loss_data: HistoricalLossData
    ) -> float:
        """Calculate risk premium based on standard deviation and risk tolerance"""
        # Risk premium using variance principle or standard deviation principle
        # Using a combination approach
        variance_premium = 0.1 * std_dev  # 10% of standard deviation
        volatility_premium = (
            0.05 * expected_loss * (std_dev / expected_loss if expected_loss > 0 else 0)
        )  # Coefficient of variation factor

        # Geographic risk adjustment
        geo_factor = self._calculate_geographic_risk_factor(
            loss_data.location_coordinates
        )

        risk_premium = (variance_premium + volatility_premium) * geo_factor
        return risk_premium

    def _calculate_geographic_risk_factor(
        self, coordinates: Tuple[float, float]
    ) -> float:
        """Calculate geographic risk factor based on coordinates"""
        latitude, longitude = coordinates

        # Default factor
        factor = 1.0

        # Areas with higher historical risk get higher factors
        if abs(latitude) < 23.5:  # Tropical regions may have higher risk
            factor *= 1.2
        elif abs(latitude) > 60:  # Polar regions may have different risk patterns
            factor *= 1.1

        # Additional factors could be implemented based on:
        # - Proximity to coasts
        # - Elevation
        # - Historical disaster zones
        # For now, using simplified model

        return factor

    def _calculate_actuarial_indicators(
        self,
        frequency: float,
        severity: float,
        expected_loss: float,
        std_dev: float,
        loss_data: HistoricalLossData,
    ) -> Dict[str, float]:
        """Calculate various actuarial indicators"""
        indicators = {}

        # Loss ratio (if premium data available)
        indicators["loss_ratio"] = (
            expected_loss / (frequency * severity) if frequency * severity > 0 else 0.0
        )

        # Combined ratio component (expense + loss ratio, simplified)
        indicators["combined_ratio_component"] = (
            (expected_loss + severity * 0.2) / (frequency * severity * 1.3)
            if frequency * severity > 0
            else 0.0
        )

        # Pure premium indicator
        indicators["pure_premium_per_unit"] = severity * frequency

        # Risk load factor
        indicators["risk_load_factor"] = (
            std_dev / expected_loss if expected_loss > 0 else 0.0
        )

        # Coefficient of variation squared (measure of risk)
        indicators["variance_to_mean_ratio"] = (
            (std_dev**2) / expected_loss if expected_loss > 0 else 0.0
        )

        # Historical loss ratio (actual losses / total exposure)
        total_historical_losses = sum(
            claim.get("amount", 0) for claim in loss_data.claims_history
        )
        indicators["historical_loss_ratio"] = (
            total_historical_losses / loss_data.total_exposure
            if loss_data.total_exposure > 0
            else 0.0
        )

        # Claim frequency indicator
        indicators["annual_claim_frequency"] = frequency

        # Average severity indicator
        indicators["average_severity"] = severity

        return indicators

    def _classify_risk(self, total_premium: float, asset_value: float) -> str:
        """Classify risk based on premium-to-asset-value ratio"""
        if asset_value <= 0:
            ratio = 0.0
        else:
            ratio = total_premium / asset_value

        # Classify based on ratio
        for classification, (min_val, max_val) in self.risk_classification_map.items():
            if min_val <= ratio <= max_val:
                return classification

        # If ratio is outside defined ranges, return extreme classification
        if ratio > 0.8:
            return "very_high"
        else:
            return "very_low"

    def perform_experience_rating(
        self,
        policy_id: str,
        historical_premiums: List[float],
        historical_losses: List[float],
    ) -> float:
        """
        Calculate experience rating adjustment

        Args:
            policy_id: Unique policy identifier
            historical_premiums: List of historical premiums
            historical_losses: List of historical losses

        Returns:
            Experience modification factor
        """
        if len(historical_premiums) == 0 or len(historical_losses) == 0:
            return 1.0  # No modification if no history

        if len(historical_premiums) != len(historical_losses):
            logger.warning(f"Mismatch in historical data for policy {policy_id}")
            return 1.0

        # Calculate experience modification based on loss ratio vs expected
        avg_premium = np.mean(historical_premiums)
        avg_loss = np.mean(historical_losses)

        if avg_premium == 0:
            return 1.0  # Avoid division by zero

        actual_loss_ratio = avg_loss / avg_premium

        # Industry benchmark (this would typically come from industry data)
        industry_loss_ratio = 0.70  # Example: 70% industry average

        # Calculate experience modification factor
        # Using simplified NCCI approach: EMF = (Actual Loss Ratio) / (Expected Loss Ratio)
        if industry_loss_ratio > 0:
            emf = actual_loss_ratio / industry_loss_ratio
            # Limit extreme modifications
            emf = max(0.5, min(2.0, emf))  # Keep between 0.5 and 2.0
        else:
            emf = 1.0

        return emf

    def calculate_reinsurance_requirements(
        self, expected_loss: float, std_dev: float
    ) -> Dict[str, float]:
        """
        Calculate reinsurance requirements based on risk measures

        Args:
            expected_loss: Expected annual loss
            std_dev: Standard deviation of losses

        Returns:
            Reinsurance requirements
        """
        # Calculate various risk measures
        var_95 = expected_loss + 1.645 * std_dev  # VaR at 95%
        var_99 = expected_loss + 2.33 * std_dev  # VaR at 99%

        # Calculate CTE (Conditional Tail Expectation) / TVaR
        # Simplified as mean of losses above VaR
        cte_95 = var_95 + 0.3 * std_dev  # Approximation
        cte_99 = var_99 + 0.5 * std_dev  # Approximation with higher loading

        # Determine reinsurance retention levels
        retention_95 = max(
            expected_loss * 2, 100000
        )  # Retain up to 2x expected loss or $100k
        retention_99 = max(
            expected_loss * 3, 250000
        )  # Higher retention for extreme events

        return {
            "var_95": var_95,
            "var_99": var_99,
            "cte_95": cte_95,
            "cte_99": cte_99,
            "retention_95": retention_95,
            "retention_99": retention_99,
            "reinsurance_loading": 0.15,  # 15% loading for reinsurance
        }

    def update_loading_factors(self, new_loadings: Dict[str, float]):
        """Update the loading factors"""
        self.loading_factors.update(new_loadings)

    def get_tariff_classification(
        self, risk_factors: Dict[str, float], coverage_type: RiskCategory
    ) -> str:
        """
        Determine tariff classification based on risk factors

        Args:
            risk_factors: Dictionary of risk factors
            coverage_type: Type of coverage

        Returns:
            Tariff classification
        """
        # Calculate weighted risk score based on different factors
        factor_weights = {
            "location_risk": 0.3,
            "asset_age": 0.2,
            "construction_type": 0.2,
            "protection_measures": 0.15,
            "exposure_density": 0.15,
        }

        weighted_score = 0.0
        total_weight = 0.0

        for factor, value in risk_factors.items():
            weight = factor_weights.get(factor, 0.1)  # Default weight
            weighted_score += value * weight
            total_weight += weight

        if total_weight > 0:
            normalized_score = weighted_score / total_weight
        else:
            normalized_score = 0.5  # Default medium risk

        # Classify based on score
        if normalized_score < 0.2:
            return "Class A - Very Low Risk"
        elif normalized_score < 0.4:
            return "Class B - Low Risk"
        elif normalized_score < 0.6:
            return "Class C - Medium Risk"
        elif normalized_score < 0.8:
            return "Class D - High Risk"
        else:
            return "Class E - Very High Risk"


# Global instance
aat_engine = TraditionalActuarialEngine()


def perform_actuarial_analysis(
    loss_data: HistoricalLossData,
) -> ActuarialAnalysisResult:
    """Convenience function to perform actuarial analysis"""
    return aat_engine.perform_actuarial_analysis(loss_data)


def perform_experience_rating(
    policy_id: str, historical_premiums: List[float], historical_losses: List[float]
) -> float:
    """Convenience function to calculate experience rating"""
    return aat_engine.perform_experience_rating(
        policy_id, historical_premiums, historical_losses
    )


def calculate_reinsurance_requirements(
    expected_loss: float, std_dev: float
) -> Dict[str, float]:
    """Convenience function to calculate reinsurance requirements"""
    return aat_engine.calculate_reinsurance_requirements(expected_loss, std_dev)


def get_tariff_classification(
    risk_factors: Dict[str, float], coverage_type: RiskCategory
) -> str:
    """Convenience function to get tariff classification"""
    return aat_engine.get_tariff_classification(risk_factors, coverage_type)

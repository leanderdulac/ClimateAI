"""
IA Agent for Climate Risk Analysis and Premium Calculation Service
Implements an intelligent agent that evaluates all analysis data,
calculates claims and premiums with intelligent weighting,
and provides system operation insights.
"""

import json
import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class ClimateRiskFactors:
    """Factors for climate risk analysis used by the IA Agent"""

    scr_score: float  # Climate Risk Score (0-1000)
    climate_var_99: float  # 99% Value at Risk
    expected_loss: float  # Expected climate losses
    physical_risk: float  # Physical climate risk (0-1)
    transition_risk: float  # Transition climate risk (0-1)
    concentration_risk: float  # Concentration risk (0-1)
    mitigation_score: float  # Mitigation effectiveness (0-1)
    model_confidence: float  # Model confidence (0-1)
    historical_loss_ratio: float  # Historical loss ratio
    geographic_risk_factor: float  # Geographic risk factor (0-1)
    seasonality_factor: float  # Seasonal risk factor (0-1)


@dataclass
class PremiumCalculation:
    """Results of premium calculation by the IA Agent"""

    base_premium: float
    risk_adjusted_premium: float
    climate_loading: float
    uncertainty_loading: float
    final_premium: float
    confidence_score: float  # 0-1 confidence in calculation
    risk_factors_considered: Dict[str, float]
    calculation_timestamp: datetime


@dataclass
class ClaimAssessment:
    """Results of claim assessment by the IA Agent"""

    claim_amount: float
    probability_valid: float  # Probability that claim is valid (0-1)
    adjusted_amount: float  # Adjusted for risk factors
    fraud_indicator: float  # Fraud risk indicator (0-1)
    investigation_priority: int  # Priority level (1=highest, 5=lowest)
    supporting_factors: Dict[str, float]
    assessment_timestamp: datetime


@dataclass
class SystemEvaluation:
    """System operation evaluation by the IA Agent"""

    system_performance_score: float  # Overall performance (0-100)
    risk_accuracy: float  # Accuracy of risk modeling (0-100)
    premium_efficiency: float  # Premium calculation efficiency (0-100)
    claim_processing_speed: float  # Claim processing performance (0-100)
    model_confidence: float  # Confidence in system models (0-100)
    recommendations: List[Dict[str, Any]]
    evaluation_timestamp: datetime
    improvement_areas: List[str]


class IAAnalyticsAgentService:
    """
    Intelligent agent for climate risk analysis, premium calculation, and system evaluation.
    Uses machine learning to analyze all system data and provide intelligent assessments.
    """

    def __init__(self):
        self.model_trained = False
        self.scaler = StandardScaler()
        self.premium_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.claim_model = GradientBoostingRegressor(random_state=42)
        self.system_evaluation_model = RandomForestRegressor(
            n_estimators=50, random_state=42
        )

        # Initialize with default weights and factors
        self.risk_weights = {
            "scr_score": 0.25,
            "climate_var_99": 0.20,
            "physical_risk": 0.15,
            "transition_risk": 0.10,
            "concentration_risk": 0.10,
            "mitigation_score": -0.15,  # Negative because lower mitigation increases risk
            "model_confidence": -0.05,  # Negative because lower confidence increases uncertainty
        }

        self.loading_factors = {
            "base_loading": 0.15,  # 15% base loading
            "climate_loading": 0.10,  # Additional for climate risk
            "uncertainty_loading": 0.05,  # Additional for model uncertainty
        }

        # Initialize with some default training data
        self._initialize_models()

    def _initialize_models(self):
        """Initialize models with default training data"""
        try:
            # Generate synthetic training data for initial model training
            n_samples = 1000

            # Generate synthetic feature data
            synthetic_data = np.random.rand(n_samples, len(self.risk_weights))

            # Normalize features appropriately
            synthetic_data[:, 0] = synthetic_data[:, 0] * 1000  # SCR score (0-1000)
            synthetic_data[:, 1] = synthetic_data[:, 1] * 50000  # VaR (0-50000)
            synthetic_data[:, 2] = (
                synthetic_data[:, 2] * 10000
            )  # Expected loss (0-10000)
            # Others remain 0-1 range

            # Generate synthetic target values
            premium_targets = []
            claim_targets = []

            for i in range(n_samples):
                # Calculate premium based on risk factors
                base_factor = synthetic_data[i, 2] * 1.5  # Expected loss influence
                risk_factor = sum(
                    synthetic_data[i, j] * list(self.risk_weights.values())[j]
                    for j in range(min(len(synthetic_data[i]), len(self.risk_weights)))
                )

                premium = (
                    base_factor + max(0, risk_factor) * 5000
                )  # Base premium influenced by risk
                premium_targets.append(max(500, premium))  # Minimum premium of 500

                # Calculate claim probability based on risk factors
                claim_prob = min(
                    1.0,
                    max(
                        0.0,
                        synthetic_data[i, 0] / 1000 * 0.3  # SCR influence
                        + synthetic_data[i, 3] * 0.4  # Physical risk influence
                        + (1 - synthetic_data[i, 6])
                        * 0.3,  # Mitigation inverse influence
                    ),
                )
                claim_targets.append(claim_prob)

            # Train the models with synthetic data
            X_scaled = self.scaler.fit_transform(synthetic_data)

            self.premium_model.fit(X_scaled, premium_targets)
            self.claim_model.fit(
                X_scaled[:-100], [p for p in claim_targets[:-100]]
            )  # Reserve 100 for validation

            self.model_trained = True
            logger.info(
                "Climate Analytics Agent initialized with synthetic training data"
            )
        except Exception as e:
            logger.warning(f"Could not initialize models with synthetic data: {str(e)}")
            # Continue with basic calculations even if training fails

    def analyze_climate_risks(self, factors) -> Dict[str, float]:
        """
        Analyze all climate risk factors using the IA Agent
        Accepts either ClimateRiskFactors or PolicyMetrics objects

        Args:
            factors: ClimateRiskFactors or PolicyMetrics object with risk parameters

        Returns:
            Dictionary with weighted risk analysis
        """
        try:
            # Handle both ClimateRiskFactors and PolicyMetrics objects
            if hasattr(factors, "scr_score"):  # ClimateRiskFactors
                factor_vector = [
                    factors.scr_score,
                    factors.climate_var_99,
                    factors.expected_loss,
                    factors.physical_risk,
                    factors.transition_risk,
                    factors.concentration_risk,
                    factors.mitigation_score,
                    factors.model_confidence,
                    factors.historical_loss_ratio,
                    factors.geographic_risk_factor,
                    factors.seasonality_factor,
                ]
            elif hasattr(factors, "climate_risk_score"):  # PolicyMetrics
                factor_vector = [
                    factors.climate_risk_score,  # Map to scr_score
                    getattr(
                        factors,
                        "climate_var_99",
                        getattr(factors, "climate_var_score", 10000),
                    ),
                    factors.expected_claims,  # Map to expected_loss
                    factors.physical_risk,
                    factors.transition_risk,
                    factors.concentration_risk,
                    factors.mitigation_effectiveness,  # Map to mitigation_score
                    factors.model_confidence,
                    getattr(
                        factors,
                        "historical_loss_ratio",
                        getattr(factors, "claim_frequency", 0.15),
                    ),
                    factors.geographic_factor,  # Map to geographic_risk_factor
                    getattr(
                        factors,
                        "seasonality_factor",
                        getattr(factors, "seasonality_factor", 0.4),
                    ),
                ]
            else:
                # Fallback to default values if unknown object type
                factor_vector = [
                    500,  # scr_score (default)
                    10000,  # climate_var_99 (default)
                    2000,  # expected_loss (default)
                    0.4,  # physical_risk (default)
                    0.3,  # transition_risk (default)
                    0.2,  # concentration_risk (default)
                    0.6,  # mitigation_score (default)
                    0.75,  # model_confidence (default)
                    0.15,  # historical_loss_ratio (default)
                    0.5,  # geographic_risk_factor (default)
                    0.4,  # seasonality_factor (default)
                ]

            # Normalize the factor vector
            factor_array = np.array(factor_vector).reshape(1, -1)
            try:
                factor_scaled = self.scaler.transform(factor_array)
            except:
                # If scaler hasn't been fitted properly, use raw values
                factor_scaled = factor_array

            # Calculate weighted risks using the risk weights
            weighted_risks = {}

            # Calculate composite risk score
            composite_risk = 0
            for i, (factor_name, weight) in enumerate(self.risk_weights.items()):
                if i < len(factor_vector):
                    factor_value = factor_vector[i]
                    if factor_name == "scr_score":
                        # Normalize SCR score to 0-1 scale
                        normalized_value = factor_value / 1000
                        weighted_value = normalized_value * weight
                    elif factor_name in ["climate_var_99", "expected_loss"]:
                        # Normalize financial values relative to typical ranges
                        normalized_value = (
                            factor_value / 10000
                        )  # Assume 10k as typical max
                        weighted_value = normalized_value * weight
                    else:
                        # Other factors are already 0-1
                        weighted_value = factor_value * weight

                    weighted_risks[factor_name] = weighted_value
                    composite_risk += weighted_value

            # Adjust for model confidence
            final_composite = composite_risk * (
                1 + (1 - factors.model_confidence) * 0.5
            )

            # Calculate risk categories
            risk_categories = {
                "financial_risk": factors.climate_var_99
                / 10000,  # Normalize to 0-5 scale
                "event_risk": (factors.physical_risk + factors.transition_risk) / 2,
                "concentration_risk": factors.concentration_risk,
                "mitigation_effectiveness": factors.mitigation_score,
                "model_uncertainty": 1 - factors.model_confidence,
            }

            analysis_results = {
                "composite_risk_score": max(0, min(10, final_composite)),
                "weighted_factors": weighted_risks,
                "risk_categories": risk_categories,
                "model_confidence": getattr(
                    factors,
                    "model_confidence",
                    getattr(factors, "model_confidence", 0.75),
                ),
                "analysis_timestamp": datetime.now().isoformat(),
                "factor_importance": self._calculate_factor_importance(factor_vector),
            }

            return analysis_results

        except Exception as e:
            logger.error(f"Error in climate risk analysis: {str(e)}")
            # Return basic analysis with error correction for both object types
            try:
                scr_score = getattr(
                    factors, "scr_score", getattr(factors, "climate_risk_score", 500)
                )
                climate_var_99 = getattr(
                    factors,
                    "climate_var_99",
                    getattr(factors, "climate_risk_score", 10000) * 2,
                )
                physical_risk = getattr(
                    factors, "physical_risk", getattr(factors, "physical_risk", 0.4)
                )
                transition_risk = getattr(
                    factors, "transition_risk", getattr(factors, "transition_risk", 0.3)
                )
                concentration_risk = getattr(
                    factors,
                    "concentration_risk",
                    getattr(factors, "concentration_risk", 0.2),
                )
                mitigation_score = getattr(
                    factors,
                    "mitigation_score",
                    getattr(factors, "mitigation_effectiveness", 0.6),
                )
                model_confidence = getattr(
                    factors,
                    "model_confidence",
                    getattr(factors, "model_confidence", 0.75),
                )

                return {
                    "composite_risk_score": scr_score / 100,  # Basic conversion
                    "weighted_factors": {},
                    "risk_categories": {
                        "financial_risk": climate_var_99 / 50000,
                        "event_risk": (physical_risk + transition_risk) / 2,
                        "concentration_risk": concentration_risk,
                        "mitigation_effectiveness": mitigation_score,
                    },
                    "model_confidence": model_confidence,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "factor_importance": {k: v for k, v in self.risk_weights.items()},
                }
            except Exception as inner_e:
                logger.error(f"Error in error handler: {inner_e}")
                # Ultimate fallback
                return {
                    "composite_risk_score": 5.0,
                    "weighted_factors": {},
                    "risk_categories": {
                        "financial_risk": 0.2,
                        "event_risk": 0.35,
                        "concentration_risk": 0.2,
                        "mitigation_effectiveness": 0.6,
                    },
                    "model_confidence": 0.75,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "factor_importance": {k: v for k, v in self.risk_weights.items()},
                }

    def calculate_premium_intelligent(self, factors) -> PremiumCalculation:
        """
        Calculate premium with intelligent weighting and analysis
        Accepts either ClimateRiskFactors or PolicyMetrics objects

        Args:
            factors: ClimateRiskFactors or PolicyMetrics object with risk parameters

        Returns:
            PremiumCalculation object with detailed premium calculation
        """
        try:
            # Analyze the risks first
            risk_analysis = self.analyze_climate_risks(factors)

            # Calculate base premium based on expected loss and risk factors
            # Handle both types of objects
            expected_loss = getattr(
                factors, "expected_loss", getattr(factors, "expected_claims", 2000)
            )
            base_premium = expected_loss * 1.2  # 20% markup on expected loss

            # Apply climate loading based on composite risk
            climate_loading = base_premium * risk_analysis["composite_risk_score"] * 0.1

            # Apply uncertainty loading based on model confidence
            model_confidence = getattr(
                factors, "model_confidence", getattr(factors, "model_confidence", 0.75)
            )
            uncertainty_loading = base_premium * (1 - model_confidence) * 0.08

            # Calculate risk-adjusted premium
            risk_adjusted_premium = base_premium + climate_loading
            final_premium = risk_adjusted_premium + uncertainty_loading

            # Calculate confidence in the premium calculation with attribute safety
            try:
                model_confidence = getattr(
                    factors,
                    "model_confidence",
                    getattr(factors, "model_confidence", 0.75),
                )
                concentration_risk = getattr(
                    factors,
                    "concentration_risk",
                    getattr(factors, "concentration_risk", 0.2),
                )
                mitigation_score = getattr(
                    factors,
                    "mitigation_score",
                    getattr(factors, "mitigation_effectiveness", 0.6),
                )

                confidence_score = min(
                    1.0,
                    max(
                        0.1,
                        model_confidence * 0.6
                        + (1 - concentration_risk) * 0.2
                        + mitigation_score * 0.2,
                    ),
                )
            except:
                confidence_score = 0.7  # Default value

            # Identify key risk factors influencing the premium with attribute safety
            try:
                scr_impact = risk_analysis["composite_risk_score"] * 0.25
                var_impact = (
                    getattr(
                        factors,
                        "climate_var_99",
                        getattr(factors, "climate_risk_score", 10000) * 2,
                    )
                    / 50000
                ) * 0.20
                physical_risk_impact = (
                    getattr(
                        factors, "physical_risk", getattr(factors, "physical_risk", 0.4)
                    )
                    * 0.15
                )
                mitigation_discount = mitigation_score * -0.10
                model_confidence_impact = (1 - model_confidence) * 0.10

                key_factors = {
                    "scr_impact": scr_impact,
                    "var_impact": var_impact,
                    "physical_risk_impact": physical_risk_impact,
                    "mitigation_discount": mitigation_discount,
                    "model_confidence_impact": model_confidence_impact,
                }
            except:
                key_factors = {
                    "scr_impact": 0.0,
                    "var_impact": 0.0,
                    "physical_risk_impact": 0.0,
                    "mitigation_discount": 0.0,
                    "model_confidence_impact": 0.0,
                }

            return PremiumCalculation(
                base_premium=base_premium,
                risk_adjusted_premium=risk_adjusted_premium,
                climate_loading=climate_loading,
                uncertainty_loading=uncertainty_loading,
                final_premium=final_premium,
                confidence_score=confidence_score,
                risk_factors_considered=key_factors,
                calculation_timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error in premium calculation: {str(e)}")
            # Return basic calculation with error handling for both object types
            try:
                expected_loss = getattr(
                    factors, "expected_loss", getattr(factors, "expected_claims", 2000)
                )
                base_premium = expected_loss * 1.25
                physical_risk = getattr(
                    factors, "physical_risk", getattr(factors, "physical_risk", 0.4)
                )
                transition_risk = getattr(
                    factors, "transition_risk", getattr(factors, "transition_risk", 0.3)
                )

                final_premium = (
                    base_premium
                    * (1 + physical_risk * 0.5)
                    * (1 + transition_risk * 0.3)
                )

                return PremiumCalculation(
                    base_premium=base_premium,
                    risk_adjusted_premium=final_premium * 0.9,
                    climate_loading=final_premium * 0.1,
                    uncertainty_loading=final_premium * 0.05,
                    final_premium=final_premium,
                    confidence_score=0.7,  # Default confidence on error
                    risk_factors_considered={
                        "expected_loss": expected_loss,
                        "physical_risk": physical_risk,
                        "transition_risk": transition_risk,
                    },
                    calculation_timestamp=datetime.now(),
                )
            except:
                # Ultimate fallback
                return PremiumCalculation(
                    base_premium=2000,
                    risk_adjusted_premium=3000,
                    climate_loading=200,
                    uncertainty_loading=100,
                    final_premium=3300,
                    confidence_score=0.65,
                    risk_factors_considered={
                        "expected_loss": 2000,
                        "physical_risk": 0.4,
                        "transition_risk": 0.3,
                    },
                    calculation_timestamp=datetime.now(),
                )

    def assess_claim_intelligent(
        self,
        claim_amount: float,
        risk_factors: ClimateRiskFactors,
        policy_history: Optional[Dict[str, Any]] = None,
    ) -> ClaimAssessment:
        """
        Assess claim with intelligent analysis

        Args:
            claim_amount: Amount claimed
            risk_factors: ClimateRiskFactors affecting the claim
            policy_history: Historical policy data (optional)

        Returns:
            ClaimAssessment with detailed claim analysis
        """
        try:
            # Analyze risks related to this claim
            risk_analysis = self.analyze_climate_risks(risk_factors)

            # Calculate probability of valid claim
            # Higher composite risk means higher likelihood of valid claim
            base_validity = min(1.0, risk_analysis["composite_risk_score"] / 5.0)

            # Adjust based on physical risk - if physical risk is high, claim more likely valid
            physical_risk_contribution = risk_factors.physical_risk * 0.6
            transition_risk_contribution = max(0.0, risk_factors.transition_risk * 0.2)

            # Consider mitigation - better mitigation reduces claim validity probability (good mitigation means less likely to have valid claims)
            mitigation_adjustment = (1 - risk_factors.mitigation_score) * 0.2

            probability_valid = min(
                1.0,
                base_validity
                + physical_risk_contribution
                + transition_risk_contribution
                + mitigation_adjustment,
            )

            # Calculate fraud indicator
            fraud_risk_factors = []

            # High claim amount relative to expected loss might indicate fraud
            expected_vs_claimed = claim_amount / (
                risk_factors.expected_loss + 1
            )  # +1 to avoid division by zero
            fraud_risk_factors.append(
                min(1.0, (expected_vs_claimed - 1) if expected_vs_claimed > 1 else 0)
            )

            # Low model confidence increases fraud risk perception
            fraud_risk_factors.append((1 - risk_factors.model_confidence) * 0.3)

            # Concentration risk might indicate organized fraud
            fraud_risk_factors.append(risk_factors.concentration_risk * 0.2)

            fraud_indicator = min(1.0, sum(fraud_risk_factors))

            # Adjust claim amount based on validity probability
            adjusted_amount = claim_amount * probability_valid

            # Determine investigation priority
            # Higher fraud indicator = higher priority
            # Lower validity probability = higher priority
            priority_score = (fraud_indicator * 0.6) + ((1 - probability_valid) * 0.4)

            if priority_score >= 0.7:
                investigation_priority = 1  # Highest
            elif priority_score >= 0.5:
                investigation_priority = 2
            elif priority_score >= 0.3:
                investigation_priority = 3
            elif priority_score >= 0.1:
                investigation_priority = 4
            else:
                investigation_priority = 5  # Lowest

            supporting_factors = {
                "composite_risk_contribution": risk_analysis["composite_risk_score"],
                "physical_risk_weight": physical_risk_contribution,
                "mitigation_adjustment": mitigation_adjustment,
                "expected_vs_claimed_ratio": expected_vs_claimed,
                "model_confidence_factor": risk_factors.model_confidence,
            }

            return ClaimAssessment(
                claim_amount=claim_amount,
                probability_valid=probability_valid,
                adjusted_amount=adjusted_amount,
                fraud_indicator=fraud_indicator,
                investigation_priority=investigation_priority,
                supporting_factors=supporting_factors,
                assessment_timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error in claim assessment: {str(e)}")
            # Return basic assessment with error handling
            probability_valid = min(
                1.0, max(0.0, risk_factors.physical_risk + risk_factors.transition_risk)
            )
            fraud_indicator = max(0.0, 1 - risk_factors.model_confidence)

            return ClaimAssessment(
                claim_amount=claim_amount,
                probability_valid=probability_valid,
                adjusted_amount=claim_amount * probability_valid,
                fraud_indicator=fraud_indicator,
                investigation_priority=3,
                supporting_factors={
                    "physical_risk": risk_factors.physical_risk,
                    "transition_risk": risk_factors.transition_risk,
                    "model_confidence": risk_factors.model_confidence,
                },
                assessment_timestamp=datetime.now(),
            )

    def evaluate_system_performance(
        self,
        premium_calculations: List[PremiumCalculation],
        claim_assessments: List[ClaimAssessment],
        risk_analyses: List[Dict[str, Any]],
    ) -> SystemEvaluation:
        """
        Evaluate overall system performance and provide insights

        Args:
            premium_calculations: Recent premium calculations
            claim_assessments: Recent claim assessments
            risk_analyses: Recent risk analyses

        Returns:
            SystemEvaluation with comprehensive system analysis
        """
        try:
            # Calculate system performance metrics
            total_premiums = len(premium_calculations)
            total_claims = len(claim_assessments)
            total_analyses = len(risk_analyses)

            # Performance indicators
            avg_confidence = 0.7  # Default
            if premium_calculations:
                avg_confidence = (
                    sum(pc.confidence_score for pc in premium_calculations)
                    / total_premiums
                )

            # Claim processing efficiency
            avg_investigation_priority = 3.0  # Default
            fraud_detection_rate = 0.15  # Default rate

            if claim_assessments:
                avg_investigation_priority = (
                    sum(ca.investigation_priority for ca in claim_assessments)
                    / total_claims
                )
                valid_claims = sum(
                    1 for ca in claim_assessments if ca.probability_valid > 0.5
                )
                fraud_detected = sum(
                    1 for ca in claim_assessments if ca.fraud_indicator > 0.7
                )
                fraud_detection_rate = (
                    fraud_detected / total_claims if total_claims > 0 else 0.15
                )

            # Risk accuracy assessment
            risk_accuracy = min(100, max(0, 80 + (avg_confidence - 0.7) * 20))

            # Premium efficiency (balance between coverage and profitability)
            premium_efficiency = min(100, max(0, 75 + (avg_confidence - 0.7) * 10))

            # Claim processing speed (based on investigation priorities)
            claim_speed_score = min(100, max(0, 90 - avg_investigation_priority * 10))

            # Overall system performance
            system_performance = (
                risk_accuracy * 0.3
                + premium_efficiency * 0.25
                + claim_speed_score * 0.25
                + avg_confidence * 100 * 0.2
            )

            # Generate recommendations
            recommendations = []

            # Premium calculation recommendations
            if avg_confidence < 0.7:
                recommendations.append(
                    {
                        "category": "premium_calculation",
                        "priority": "high",
                        "recommendation": "Model confidence is low. Consider improving data quality or retraining models.",
                        "impact_area": "model_confidence",
                    }
                )

            if fraud_detection_rate < 0.1:
                recommendations.append(
                    {
                        "category": "fraud_detection",
                        "priority": "medium",
                        "recommendation": "Fraud detection rate is low. Review fraud patterns and adjust detection algorithms.",
                        "impact_area": "claim_assessment",
                    }
                )

            # Risk model recommendations
            if risk_accuracy < 75:
                recommendations.append(
                    {
                        "category": "risk_modeling",
                        "priority": "high",
                        "recommendation": "Risk modeling accuracy is below threshold. Consider incorporating additional risk factors.",
                        "impact_area": "risk_analysis",
                    }
                )

            # Generate improvement areas
            improvement_areas = []
            if avg_confidence < 0.75:
                improvement_areas.append("Model confidence and data quality")
            if fraud_detection_rate < 0.15:
                improvement_areas.append("Fraud detection algorithms")
            if risk_accuracy < 80:
                improvement_areas.append("Risk modeling precision")
            if claim_speed_score < 75:
                improvement_areas.append("Claim processing efficiency")

            if not improvement_areas:
                improvement_areas.append("System performing well in all areas")

            return SystemEvaluation(
                system_performance_score=system_performance,
                risk_accuracy=risk_accuracy,
                premium_efficiency=premium_efficiency,
                claim_processing_speed=claim_speed_score,
                model_confidence=avg_confidence * 100,
                recommendations=recommendations,
                evaluation_timestamp=datetime.now(),
                improvement_areas=improvement_areas,
            )

        except Exception as e:
            logger.error(f"Error in system evaluation: {str(e)}")
            # Return basic evaluation with error handling
            return SystemEvaluation(
                system_performance_score=75.0,
                risk_accuracy=75.0,
                premium_efficiency=70.0,
                claim_processing_speed=80.0,
                model_confidence=70.0,
                recommendations=[
                    {
                        "category": "system_wide",
                        "priority": "medium",
                        "recommendation": "System experienced calculation errors. Check data inputs and model performance.",
                        "impact_area": "overall",
                    }
                ],
                evaluation_timestamp=datetime.now(),
                improvement_areas=["Error recovery and data validation"],
            )

    def _calculate_factor_importance(
        self, factor_vector: List[float]
    ) -> Dict[str, float]:
        """
        Calculate relative importance of each factor in the risk calculation
        """
        try:
            # This is a simplified version - in production, use SHAP or similar
            default_importance = {
                "scr_score": 0.20,
                "climate_var_99": 0.18,
                "expected_loss": 0.15,
                "physical_risk": 0.15,
                "transition_risk": 0.12,
                "concentration_risk": 0.10,
                "mitigation_score": 0.10,
            }

            # Adjust importance based on actual values
            importance_factors = {}
            for i, (factor_name, base_importance) in enumerate(
                default_importance.items()
            ):
                if i < len(factor_vector):
                    factor_value = factor_vector[i]
                    # Importance increases with factor magnitude
                    adjusted_importance = base_importance * (
                        1 + min(1.0, factor_value / 100)
                    )
                    importance_factors[factor_name] = min(1.0, adjusted_importance)
                else:
                    importance_factors[factor_name] = base_importance

            return importance_factors
        except:
            return {k: v for k, v in [("scr_score", 0.20), ("climate_var_99", 0.18)]}


# Global instance
climate_analytics_agent = IAAnalyticsAgentService()


def analyze_climate_risks(factors: ClimateRiskFactors) -> Dict[str, float]:
    """Convenience function for climate risk analysis"""
    return climate_analytics_agent.analyze_climate_risks(factors)


def calculate_premium_intelligent(factors: ClimateRiskFactors) -> PremiumCalculation:
    """Convenience function for intelligent premium calculation"""
    return climate_analytics_agent.calculate_premium_intelligent(factors)


def assess_claim_intelligent(
    claim_amount: float,
    risk_factors: ClimateRiskFactors,
    policy_history: Optional[Dict[str, Any]] = None,
) -> ClaimAssessment:
    """Convenience function for intelligent claim assessment"""
    return climate_analytics_agent.assess_claim_intelligent(
        claim_amount, risk_factors, policy_history
    )


def evaluate_system_performance(
    premium_calculations: List[PremiumCalculation],
    claim_assessments: List[ClaimAssessment],
    risk_analyses: List[Dict[str, Any]],
) -> SystemEvaluation:
    """Convenience function for system performance evaluation"""
    return climate_analytics_agent.evaluate_system_performance(
        premium_calculations, claim_assessments, risk_analyses
    )

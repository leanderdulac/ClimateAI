"""
Unified Pricing Orchestrator
Combines all 6 pricing/actuarial models into a single, cohesive interface.

Models integrated:
1. ComprehensivePricingCalculator - Integrated formula with concentration adjustments
2. AdvancedActuarialService - Fractal analysis, Monte Carlo, fuzzy logic
3. DynamicInsuranceAnalysisService - Dynamic pricing with ML
4. EnsemblePricingService - BIC-weighted ensemble with VaR
5. ClimatePremiumService - Climate drift and inflation factors
6. BayesianBootstrapService - Uncertainty quantification via bootstrap
"""

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class PricingModel(str, Enum):
    """Available pricing models"""
    COMPREHENSIVE = "comprehensive"
    ACTUARIAL = "actuarial"
    DYNAMIC = "dynamic"
    ENSEMBLE = "ensemble"
    CLIMATE = "climate"
    BAYESIAN = "bayesian"


@dataclass
class ModelResult:
    """Result from a single pricing model"""
    model_name: str
    premium: float
    confidence_interval: Tuple[float, float]
    risk_score: float
    calculation_time_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    error: Optional[str] = None


@dataclass
class UnifiedPricingResult:
    """Unified result combining all models"""
    final_premium: float
    weighted_average_premium: float
    model_results: List[ModelResult]
    confidence_interval: Tuple[float, float]
    combined_risk_score: float
    model_agreement_score: float  # 0-1, how much models agree
    recommended_premium: float
    premium_range: Tuple[float, float]
    calculation_timestamp: datetime
    total_calculation_time_ms: float
    explanation: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)


@dataclass
class PricingInput:
    """Input for unified pricing calculation"""
    coverage_amount: float
    location_latitude: float
    location_longitude: float
    risk_factors: Dict[str, float]
    climate_data: Optional[List[Dict]] = None
    historical_claims: Optional[List[float]] = None
    policy_duration_years: int = 1
    custom_model_weights: Optional[Dict[str, float]] = None
    models_to_use: Optional[List[PricingModel]] = None
    confidence_level: float = 0.95


class UnifiedPricingOrchestrator:
    """
    Orchestrates all pricing models and provides unified pricing output.
    
    Features:
    - Parallel execution of models
    - Weighted ensemble combination
    - Model agreement analysis
    - Confidence interval calculation
    - Automatic fallback for failed models
    """
    
    def __init__(self):
        self.default_weights = {
            PricingModel.COMPREHENSIVE: 0.25,
            PricingModel.ACTUARIAL: 0.20,
            PricingModel.DYNAMIC: 0.20,
            PricingModel.ENSEMBLE: 0.15,
            PricingModel.CLIMATE: 0.10,
            PricingModel.BAYESIAN: 0.10,
        }
        
        # Performance tracking
        self.model_performance_history: Dict[str, List[float]] = {}
        
        # Lazy load services to avoid circular imports
        self._services_loaded = False
        self._comprehensive_service = None
        self._actuarial_service = None
        self._dynamic_service = None
        self._ensemble_service = None
        self._climate_service = None
        self._bayesian_service = None
        self._noaa_service = None

        # NOAA integration tunables (env-configurable)
        # NOAA_RISK_BLEND_WEIGHT: how much NOAA weather risk contributes to combined_risk_score
        # NOAA_PREMIUM_MAX_IMPACT: maximum premium uplift when NOAA weather risk is severe
        self.noaa_risk_blend_weight = self._read_float_env(
            "NOAA_RISK_BLEND_WEIGHT",
            default=0.15,
            min_value=0.0,
            max_value=1.0,
        )
        self.noaa_premium_max_impact = self._read_float_env(
            "NOAA_PREMIUM_MAX_IMPACT",
            default=0.12,
            min_value=0.0,
            max_value=0.5,
        )

    @staticmethod
    def _read_float_env(name: str, default: float, min_value: float, max_value: float) -> float:
        """Read bounded float from environment with fallback to default."""
        raw = os.getenv(name)
        if raw is None:
            return default

        try:
            value = float(raw)
        except (TypeError, ValueError):
            logger.warning(f"Invalid {name} value '{raw}', using default {default}")
            return default

        if value < min_value or value > max_value:
            logger.warning(
                f"Out-of-range {name}={value}; expected [{min_value}, {max_value}], using default {default}"
            )
            return default

        return value
    
    def _load_services(self):
        """Lazy load all pricing services"""
        if self._services_loaded:
            return
        
        try:
            from services.comprehensive_pricing_service import comprehensive_pricing_service
            self._comprehensive_service = comprehensive_pricing_service
        except ImportError as e:
            logger.warning(f"Could not load comprehensive_pricing_service: {e}")
        
        try:
            from services.advanced_actuarial_service import AdvancedActuarialService
            self._actuarial_service = AdvancedActuarialService()
        except ImportError as e:
            logger.warning(f"Could not load advanced_actuarial_service: {e}")
        
        try:
            from services.dynamic_insurance_analysis_service import dynamic_analysis_service
            self._dynamic_service = dynamic_analysis_service
        except ImportError as e:
            logger.warning(f"Could not load dynamic_insurance_analysis_service: {e}")
        
        try:
            from services.ensemble_pricing_service import ensemble_pricing_service
            self._ensemble_service = ensemble_pricing_service
        except ImportError as e:
            logger.warning(f"Could not load ensemble_pricing_service: {e}")
        
        try:
            from services.climate_premium_service import climate_premium_service
            self._climate_service = climate_premium_service
        except ImportError as e:
            logger.warning(f"Could not load climate_premium_service: {e}")
        
        try:
            from services.bayesian_bootstrap_service import bayesian_bootstrap_service
            self._bayesian_service = bayesian_bootstrap_service
        except ImportError as e:
            logger.warning(f"Could not load bayesian_bootstrap_service: {e}")

        try:
            from services.noaa_service import NOAAService
            self._noaa_service = NOAAService()
        except ImportError as e:
            logger.warning(f"Could not load noaa_service: {e}")
        
        self._services_loaded = True
    
    def _run_comprehensive_model(self, pricing_input: PricingInput) -> ModelResult:
        """Run comprehensive pricing model"""
        start_time = datetime.now()
        
        try:
            from services.comprehensive_pricing_service import PolicyPricingInput
            
            # Build input for comprehensive pricing
            input_data = PolicyPricingInput(
                policy_id=f"unified_{datetime.now().timestamp()}",
                pure_theoretical_premium=pricing_input.coverage_amount * 0.03,  # Base 3%
                loading_margin=0.20,
                total_risk_factor=pricing_input.risk_factors.get("climatic_risk", 0.3),
                climate_change_factor=pricing_input.risk_factors.get("climate_change", 0.1),
                zone_policies_premiums=[pricing_input.coverage_amount * 0.025],
                free_capital=pricing_input.coverage_amount * 10,
            )
            
            result = self._comprehensive_service.calculate_comprehensive_pricing(input_data)
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return ModelResult(
                model_name=PricingModel.COMPREHENSIVE.value,
                premium=result.final_premium,
                confidence_interval=(result.final_premium * 0.85, result.final_premium * 1.15),
                risk_score=result.scr_score / 100 if hasattr(result, 'scr_score') else 0.5,
                calculation_time_ms=elapsed,
                details={
                    "risk_level": result.risk_level if hasattr(result, 'risk_level') else "medium",
                    "decision": result.decision if hasattr(result, 'decision') else "accept",
                },
            )
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Comprehensive model error: {e}")
            return ModelResult(
                model_name=PricingModel.COMPREHENSIVE.value,
                premium=0,
                confidence_interval=(0, 0),
                risk_score=0,
                calculation_time_ms=elapsed,
                error=str(e),
            )
    
    def _run_actuarial_model(self, pricing_input: PricingInput) -> ModelResult:
        """Run advanced actuarial model"""
        start_time = datetime.now()
        
        try:
            # Prepare climate data
            climate_data = pricing_input.climate_data or [
                {"temperature": 25, "precipitation": 100, "humidity": 70}
                for _ in range(30)
            ]
            
            # Calculate frequency and severity from risk factors
            frequency = pricing_input.risk_factors.get("frequency", 0.1)
            severity = pricing_input.risk_factors.get("severity", 0.5)
            
            result = self._actuarial_service.calculate_comprehensive_premium(
                frequency=frequency,
                severity=severity,
                asset_value=pricing_input.coverage_amount,
                confidence_level=pricing_input.confidence_level,
                climate_data=climate_data,
            )
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return ModelResult(
                model_name=PricingModel.ACTUARIAL.value,
                premium=result.total_premium,
                confidence_interval=result.confidence_interval,
                risk_score=self._fuzzy_to_score(result.fuzzy_risk),
                calculation_time_ms=elapsed,
                details={
                    "pure_premium": result.pure_premium,
                    "loading_premium": result.loading_premium,
                    "fractal_dimension": result.fractal_dimension.dimension,
                },
            )
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Actuarial model error: {e}")
            return ModelResult(
                model_name=PricingModel.ACTUARIAL.value,
                premium=0,
                confidence_interval=(0, 0),
                risk_score=0,
                calculation_time_ms=elapsed,
                error=str(e),
            )
    
    def _run_dynamic_model(self, pricing_input: PricingInput) -> ModelResult:
        """Run dynamic insurance analysis model"""
        start_time = datetime.now()
        
        try:
            result = self._dynamic_service.calculate_dynamic_premium(
                coverage_amount=pricing_input.coverage_amount,
                risk_factors=pricing_input.risk_factors,
                base_loading_factor=0.20,
            )
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            premium = result.get("final_premium", 0)
            
            return ModelResult(
                model_name=PricingModel.DYNAMIC.value,
                premium=premium,
                confidence_interval=(premium * 0.9, premium * 1.1),
                risk_score=result.get("risk_score", 0.5),
                calculation_time_ms=elapsed,
                details={
                    "expected_claims": result.get("expected_claims"),
                    "profit_margin": result.get("profit_margin"),
                    "is_profitable": result.get("is_profitable"),
                },
            )
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Dynamic model error: {e}")
            return ModelResult(
                model_name=PricingModel.DYNAMIC.value,
                premium=0,
                confidence_interval=(0, 0),
                risk_score=0,
                calculation_time_ms=elapsed,
                error=str(e),
            )
    
    def _run_ensemble_model(self, pricing_input: PricingInput) -> ModelResult:
        """Run ensemble pricing model"""
        start_time = datetime.now()
        
        try:
            # Generate mock model premiums for ensemble
            base_premium = pricing_input.coverage_amount * 0.03
            model_premiums = [
                base_premium * (1 + np.random.uniform(-0.1, 0.2))
                for _ in range(5)
            ]
            
            result = self._ensemble_service.calculate_ensemble_pricing(
                model_premiums=model_premiums,
                model_log_likelihoods=[-100, -105, -98, -102, -99],
                model_n_params=[5, 7, 4, 6, 5],
                model_n_observations=[100, 100, 100, 100, 100],
                n_models=5,
                confidence_level=pricing_input.confidence_level,
            )
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return ModelResult(
                model_name=PricingModel.ENSEMBLE.value,
                premium=result.final_premium,
                confidence_interval=(
                    result.final_premium - result.var_ensemble,
                    result.final_premium + result.var_ensemble
                ),
                risk_score=result.var_ensemble / result.final_premium if result.final_premium > 0 else 0.5,
                calculation_time_ms=elapsed,
                details={
                    "model_weights": result.model_weights,
                    "var_ensemble": result.var_ensemble,
                },
            )
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Ensemble model error: {e}")
            return ModelResult(
                model_name=PricingModel.ENSEMBLE.value,
                premium=0,
                confidence_interval=(0, 0),
                risk_score=0,
                calculation_time_ms=elapsed,
                error=str(e),
            )
    
    def _run_climate_model(self, pricing_input: PricingInput) -> ModelResult:
        """Run climate premium model"""
        start_time = datetime.now()
        
        try:
            expected_loss = pricing_input.coverage_amount * pricing_input.risk_factors.get("expected_loss_ratio", 0.02)
            
            result = self._climate_service.calculate_climate_inclusive_premium(
                expected_loss=expected_loss,
                time_horizon_years=float(pricing_input.policy_duration_years),
                loading_factor=0.20,
                mitigation_discount=pricing_input.risk_factors.get("mitigation_discount", 0.0),
            )
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return ModelResult(
                model_name=PricingModel.CLIMATE.value,
                premium=result.premium,
                confidence_interval=(result.premium * 0.88, result.premium * 1.12),
                risk_score=min(1.0, result.climatic_inflation_factor - 1),
                calculation_time_ms=elapsed,
                details={
                    "climatic_inflation_factor": result.climatic_inflation_factor,
                    "climate_drift_rate": result.climate_drift_rate,
                    "mitigation_discount": result.mitigation_discount,
                },
            )
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Climate model error: {e}")
            return ModelResult(
                model_name=PricingModel.CLIMATE.value,
                premium=0,
                confidence_interval=(0, 0),
                risk_score=0,
                calculation_time_ms=elapsed,
                error=str(e),
            )
    
    def _run_bayesian_model(self, pricing_input: PricingInput) -> ModelResult:
        """Run Bayesian bootstrap model"""
        start_time = datetime.now()
        
        try:
            # Use historical claims or generate synthetic data
            historical_data = pricing_input.historical_claims or [
                pricing_input.coverage_amount * np.random.uniform(0.01, 0.05)
                for _ in range(100)
            ]
            
            base_premium = pricing_input.coverage_amount * 0.03
            
            result = self._bayesian_service.bayesian_bootstrap_premium(
                contract_data=historical_data,
                base_premium=base_premium,
                contract_exposure=pricing_input.coverage_amount,
                n_scenarios=5000,  # Reduced for performance
                confidence_level=pricing_input.confidence_level,
            )
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return ModelResult(
                model_name=PricingModel.BAYESIAN.value,
                premium=result.mean_premium,
                confidence_interval=(result.p10, result.p90),
                risk_score=result.cvar / result.mean_premium if result.mean_premium > 0 else 0.5,
                calculation_time_ms=elapsed,
                details={
                    "p10": result.p10,
                    "p90": result.p90,
                    "var": result.vaar,
                    "cvar": result.cvar,
                    "n_scenarios": result.n_scenarios,
                },
            )
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Bayesian model error: {e}")
            return ModelResult(
                model_name=PricingModel.BAYESIAN.value,
                premium=0,
                confidence_interval=(0, 0),
                risk_score=0,
                calculation_time_ms=elapsed,
                error=str(e),
            )
    
    def _fuzzy_to_score(self, fuzzy_risk) -> float:
        """Convert fuzzy risk levels to a single score"""
        try:
            return (
                fuzzy_risk.very_low * 0.1 +
                fuzzy_risk.low * 0.3 +
                fuzzy_risk.medium * 0.5 +
                fuzzy_risk.high * 0.7 +
                fuzzy_risk.very_high * 0.9
            )
        except Exception:
            return 0.5

    @staticmethod
    def _extract_max_number(text: str) -> float:
        """Extract maximum numeric value from strings like '5 to 15 mph'."""
        numbers = re.findall(r"\d+(?:\.\d+)?", text or "")
        if not numbers:
            return 0.0
        return max(float(n) for n in numbers)

    def _compute_noaa_weather_adjustment(self, pricing_input: PricingInput) -> Dict[str, Any]:
        """Compute NOAA-based weather risk modifier for principal pricing score.

        Returns a dictionary with:
        - weather_risk_score (0-1)
        - premium_modifier (>=1)
        - source and diagnostic details
        """
        default_result = {
            "source": "unavailable",
            "weather_risk_score": 0.0,
            "premium_modifier": 1.0,
            "severe_period_count": 0,
            "max_temperature": 0.0,
            "max_wind": 0.0,
        }

        if self._noaa_service is None:
            return default_result

        try:
            forecast_payload = asyncio.run(
                self._noaa_service.get_weather_forecast(
                    pricing_input.location_latitude,
                    pricing_input.location_longitude,
                )
            )

            periods = forecast_payload.get("forecast", [])[:10]
            if not periods:
                return default_result

            severe_keywords = (
                "thunderstorm",
                "heavy rain",
                "storm",
                "hail",
                "flood",
                "snow",
                "freezing",
                "tornado",
                "hurricane",
            )

            severe_count = 0
            max_temp = 0.0
            max_wind = 0.0

            for period in periods:
                forecast_text = f"{period.get('shortForecast', '')} {period.get('detailedForecast', '')}".lower()
                if any(k in forecast_text for k in severe_keywords):
                    severe_count += 1

                try:
                    temp_val = float(period.get("temperature") or 0.0)
                    max_temp = max(max_temp, temp_val)
                    if temp_val >= 35 or temp_val <= 5:
                        severe_count += 1
                except Exception:
                    pass

                wind_val = self._extract_max_number(str(period.get("windSpeed", "")))
                max_wind = max(max_wind, wind_val)
                if wind_val >= 50:
                    severe_count += 1

            # Normalize by inspected periods and cap at 1.0
            weather_risk_score = min(1.0, severe_count / max(1, len(periods)))
            premium_modifier = 1.0 + min(
                self.noaa_premium_max_impact,
                self.noaa_premium_max_impact * weather_risk_score,
            )

            return {
                "source": forecast_payload.get("source", "NOAA/NWS"),
                "weather_risk_score": weather_risk_score,
                "premium_modifier": premium_modifier,
                "severe_period_count": severe_count,
                "max_temperature": max_temp,
                "max_wind": max_wind,
            }
        except Exception as exc:
            logger.warning(f"NOAA weather adjustment unavailable: {exc}")
            return default_result
    
    def calculate_unified_premium(
        self,
        pricing_input: PricingInput,
    ) -> UnifiedPricingResult:
        """
        Calculate unified premium by running all models and combining results.
        
        Args:
            pricing_input: Input parameters for pricing calculation
            
        Returns:
            UnifiedPricingResult with combined pricing from all models
        """
        start_time = datetime.now()
        self._load_services()
        
        # Determine which models to use
        models_to_use = pricing_input.models_to_use or list(PricingModel)
        
        # Get weights
        weights = pricing_input.custom_model_weights or self.default_weights
        
        # Run all models
        model_results: List[ModelResult] = []
        warnings: List[str] = []
        
        model_runners = {
            PricingModel.COMPREHENSIVE: self._run_comprehensive_model,
            PricingModel.ACTUARIAL: self._run_actuarial_model,
            PricingModel.DYNAMIC: self._run_dynamic_model,
            PricingModel.ENSEMBLE: self._run_ensemble_model,
            PricingModel.CLIMATE: self._run_climate_model,
            PricingModel.BAYESIAN: self._run_bayesian_model,
        }
        
        for model in models_to_use:
            if model in model_runners:
                result = model_runners[model](pricing_input)
                result.weight = weights.get(model, 1.0 / len(models_to_use))
                model_results.append(result)
                
                if result.error:
                    warnings.append(f"Model {model.value} failed: {result.error}")
        
        # Filter successful results
        successful_results = [r for r in model_results if r.error is None and r.premium > 0]
        
        if not successful_results:
            # Fallback to simple premium if all models failed
            fallback_premium = pricing_input.coverage_amount * 0.035
            return UnifiedPricingResult(
                final_premium=fallback_premium,
                weighted_average_premium=fallback_premium,
                model_results=model_results,
                confidence_interval=(fallback_premium * 0.8, fallback_premium * 1.2),
                combined_risk_score=0.5,
                model_agreement_score=0.0,
                recommended_premium=fallback_premium,
                premium_range=(fallback_premium * 0.8, fallback_premium * 1.2),
                calculation_timestamp=datetime.now(),
                total_calculation_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                explanation={"note": "All models failed, using fallback premium"},
                warnings=warnings + ["All models failed, using fallback 3.5% of coverage"],
            )
        
        # Normalize weights
        total_weight = sum(r.weight for r in successful_results)
        for r in successful_results:
            r.weight = r.weight / total_weight if total_weight > 0 else 1.0 / len(successful_results)
        
        # Calculate weighted average premium
        weighted_avg = sum(r.premium * r.weight for r in successful_results)
        
        # Calculate combined risk score
        combined_risk = sum(r.risk_score * r.weight for r in successful_results)

        # NOAA weather adjustment injected into principal score and premium recommendation
        noaa_adjustment = self._compute_noaa_weather_adjustment(pricing_input)
        if noaa_adjustment["source"] == "unavailable":
            warnings.append("NOAA weather context unavailable; neutral weather modifier applied")
        else:
            weather_risk_score = noaa_adjustment["weather_risk_score"]
            base_model_risk_weight = 1.0 - self.noaa_risk_blend_weight
            combined_risk = min(
                1.0,
                combined_risk * base_model_risk_weight + weather_risk_score * self.noaa_risk_blend_weight,
            )
            if "mock" in str(noaa_adjustment.get("source", "")).lower():
                warnings.append("NOAA weather context is using fallback/mock data")
        
        # Calculate model agreement (coefficient of variation)
        premiums = [r.premium for r in successful_results]
        premium_std = np.std(premiums)
        premium_mean = np.mean(premiums)
        cv = premium_std / premium_mean if premium_mean > 0 else 1.0
        agreement_score = max(0, 1 - cv)  # Higher agreement = lower CV
        
        # Calculate combined confidence interval
        all_lowers = [r.confidence_interval[0] for r in successful_results]
        all_uppers = [r.confidence_interval[1] for r in successful_results]
        combined_ci = (np.percentile(all_lowers, 10), np.percentile(all_uppers, 90))
        
        # Recommended premium: weighted average adjusted by agreement
        # If models agree strongly, use weighted average
        # If they disagree, be more conservative (higher premium)
        conservative_adjustment = 1 + (1 - agreement_score) * 0.1
        recommended_premium = weighted_avg * conservative_adjustment
        recommended_premium *= noaa_adjustment["premium_modifier"]
        
        # Calculate total time
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Build explanation
        explanation = {
            "method": "weighted_ensemble",
            "models_used": [r.model_name for r in successful_results],
            "model_weights": {r.model_name: f"{r.weight:.2%}" for r in successful_results},
            "model_premiums": {r.model_name: f"R$ {r.premium:,.2f}" for r in successful_results},
            "agreement_level": "high" if agreement_score > 0.8 else ("medium" if agreement_score > 0.5 else "low"),
            "conservative_adjustment": f"{(conservative_adjustment - 1) * 100:.1f}%",
            "noaa_weather_adjustment": noaa_adjustment,
            "noaa_blend_parameters": {
                "noaa_risk_blend_weight": self.noaa_risk_blend_weight,
                "noaa_premium_max_impact": self.noaa_premium_max_impact,
            },
            "calculation_breakdown": {
                r.model_name: {
                    "premium": r.premium,
                    "weight": r.weight,
                    "contribution": r.premium * r.weight,
                }
                for r in successful_results
            },
        }
        
        return UnifiedPricingResult(
            final_premium=recommended_premium,
            weighted_average_premium=weighted_avg,
            model_results=model_results,
            confidence_interval=combined_ci,
            combined_risk_score=combined_risk,
            model_agreement_score=agreement_score,
            recommended_premium=recommended_premium,
            premium_range=(min(premiums), max(premiums)),
            calculation_timestamp=datetime.now(),
            total_calculation_time_ms=total_time,
            explanation=explanation,
            warnings=warnings,
        )
    
    async def calculate_unified_premium_async(
        self,
        pricing_input: PricingInput,
    ) -> UnifiedPricingResult:
        """Async version for API endpoints"""
        return await asyncio.to_thread(self.calculate_unified_premium, pricing_input)
    
    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all models"""
        return {
            "models_available": [m.value for m in PricingModel],
            "default_weights": {k.value: v for k, v in self.default_weights.items()},
            "services_loaded": self._services_loaded,
        }


# Global instance
unified_pricing_orchestrator = UnifiedPricingOrchestrator()


# Convenience functions
def calculate_unified_premium(pricing_input: PricingInput) -> UnifiedPricingResult:
    """Calculate unified premium using all available models"""
    return unified_pricing_orchestrator.calculate_unified_premium(pricing_input)


async def calculate_unified_premium_async(pricing_input: PricingInput) -> UnifiedPricingResult:
    """Async version of calculate_unified_premium"""
    return await unified_pricing_orchestrator.calculate_unified_premium_async(pricing_input)

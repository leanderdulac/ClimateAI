"""
Agricultural strategy service focused on climate adaptation for ENSO extremes.

This module translates ENSO + short-term weather context into practical
operational and financial actions for farmers.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.sqlalchemy_models import ClimateEnsoSignal
from services.enso_service import ENSOService
from services.noaa_service import NOAAService

logger = logging.getLogger(__name__)


class AgriculturalStrategyService:
    def __init__(self) -> None:
        self.enso_service = ENSOService()
        self.noaa_service = NOAAService()

        self.supported_crops = [
            "soybean",
            "corn",
            "coffee",
            "sugarcane",
            "cotton",
            "rice",
            "beans",
            "wheat",
            "pasture",
        ]
        self.supported_stages = [
            "planning",
            "planting",
            "vegetative",
            "flowering",
            "grain_fill",
            "harvest",
        ]

    @staticmethod
    def _clip01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @staticmethod
    def _extract_max_number(text: str) -> float:
        values = re.findall(r"\d+(?:\.\d+)?", text or "")
        if not values:
            return 0.0
        return max(float(v) for v in values)

    @staticmethod
    def _normalize_regime(regime_label: Optional[str]) -> str:
        label = (regime_label or "neutral").lower()
        if "nino" in label and "la_" not in label and "la-" not in label:
            return "el_nino"
        if "la_nina" in label or "la-nina" in label or "cooling" in label:
            return "la_nina"
        if "warming" in label:
            return "el_nino"
        return "neutral"

    async def _get_latest_enso_context(self, db: Optional[AsyncSession]) -> Dict[str, Any]:
        if db is not None:
            try:
                stmt = select(ClimateEnsoSignal).order_by(ClimateEnsoSignal.reference_date.desc()).limit(1)
                result = await db.execute(stmt)
                row = result.scalar_one_or_none()

                if row:
                    return {
                        "source": "database",
                        "regime_label": self._normalize_regime(row.regime_label),
                        "regime_confidence": row.regime_confidence or "medium",
                        "impact_risk_modifier": float(row.impact_risk_modifier or 1.0),
                        "reference_date": row.reference_date.isoformat() if row.reference_date else None,
                    }
            except Exception as exc:
                logger.warning("Failed to read persisted ENSO context, falling back to live snapshot: %s", exc)

        snapshot = await self.enso_service.get_latest_snapshot()
        return {
            "source": "live_cpc",
            "regime_label": self._normalize_regime(snapshot.get("regime_label")),
            "regime_confidence": snapshot.get("regime_confidence") or "medium",
            "impact_risk_modifier": float(snapshot.get("impact_risk_modifier") or 1.0),
            "reference_date": snapshot.get("reference_date").isoformat() if snapshot.get("reference_date") else None,
        }

    def _base_regime_exposure(self, regime: str) -> Dict[str, float]:
        if regime == "el_nino":
            return {
                "heat": 0.75,
                "drought": 0.80,
                "excess_rain": 0.35,
                "flood": 0.25,
                "wind": 0.45,
                "disease": 0.40,
            }
        if regime == "la_nina":
            return {
                "heat": 0.35,
                "drought": 0.30,
                "excess_rain": 0.80,
                "flood": 0.75,
                "wind": 0.50,
                "disease": 0.70,
            }
        return {
            "heat": 0.45,
            "drought": 0.45,
            "excess_rain": 0.45,
            "flood": 0.40,
            "wind": 0.40,
            "disease": 0.45,
        }

    def _weather_exposure_from_forecast(self, periods: List[Dict[str, Any]]) -> Dict[str, float]:
        if not periods:
            return {
                "heat": 0.0,
                "drought": 0.0,
                "excess_rain": 0.0,
                "flood": 0.0,
                "wind": 0.0,
                "disease": 0.0,
            }

        totals = {
            "heat": 0.0,
            "drought": 0.0,
            "excess_rain": 0.0,
            "flood": 0.0,
            "wind": 0.0,
            "disease": 0.0,
        }

        for p in periods[:10]:
            text = f"{p.get('shortForecast', '')} {p.get('detailedForecast', '')}".lower()
            temp = float(p.get("temperature") or 0.0)
            wind = self._extract_max_number(str(p.get("windSpeed", "")))

            if temp >= 34:
                totals["heat"] += 0.25
                totals["drought"] += 0.10
            if temp <= 6:
                totals["disease"] += 0.05

            if wind >= 45:
                totals["wind"] += 0.30

            if any(k in text for k in ["heavy rain", "thunderstorm", "storm", "flood", "showers"]):
                totals["excess_rain"] += 0.25
                totals["flood"] += 0.20
                totals["disease"] += 0.12

            if any(k in text for k in ["dry", "sunny", "hot", "clear"]):
                totals["drought"] += 0.08

        return {k: self._clip01(v) for k, v in totals.items()}

    def _crop_stage_multipliers(self, crop: str, stage: str) -> Dict[str, float]:
        crop = crop.lower()
        stage = stage.lower()

        crop_map = {
            "soybean": {"heat": 1.05, "drought": 1.10, "excess_rain": 1.00, "flood": 1.00, "wind": 0.95, "disease": 1.05},
            "corn": {"heat": 1.10, "drought": 1.10, "excess_rain": 0.95, "flood": 0.95, "wind": 1.00, "disease": 1.00},
            "coffee": {"heat": 1.00, "drought": 1.05, "excess_rain": 1.05, "flood": 1.00, "wind": 1.00, "disease": 1.10},
            "rice": {"heat": 0.95, "drought": 0.85, "excess_rain": 1.15, "flood": 1.15, "wind": 0.95, "disease": 1.10},
        }

        stage_map = {
            "planning": {"heat": 0.90, "drought": 0.90, "excess_rain": 0.90, "flood": 0.90, "wind": 0.90, "disease": 0.90},
            "planting": {"heat": 1.00, "drought": 1.05, "excess_rain": 1.10, "flood": 1.10, "wind": 0.95, "disease": 1.00},
            "vegetative": {"heat": 1.05, "drought": 1.05, "excess_rain": 1.00, "flood": 1.00, "wind": 1.00, "disease": 1.05},
            "flowering": {"heat": 1.20, "drought": 1.20, "excess_rain": 1.05, "flood": 1.00, "wind": 1.05, "disease": 1.15},
            "grain_fill": {"heat": 1.10, "drought": 1.15, "excess_rain": 1.00, "flood": 1.00, "wind": 1.00, "disease": 1.10},
            "harvest": {"heat": 0.95, "drought": 0.95, "excess_rain": 1.15, "flood": 1.10, "wind": 1.05, "disease": 1.00},
        }

        crop_mult = crop_map.get(crop, {k: 1.0 for k in ["heat", "drought", "excess_rain", "flood", "wind", "disease"]})
        stage_mult = stage_map.get(stage, {k: 1.0 for k in ["heat", "drought", "excess_rain", "flood", "wind", "disease"]})
        return {k: crop_mult[k] * stage_mult[k] for k in crop_mult}

    def _combined_exposure(
        self,
        base: Dict[str, float],
        weather: Dict[str, float],
        multipliers: Dict[str, float],
        enso_modifier: float,
    ) -> Dict[str, float]:
        combined = {}
        for k in base:
            value = (base[k] * 0.65 + weather.get(k, 0.0) * 0.35) * multipliers.get(k, 1.0)
            if k in {"heat", "drought", "excess_rain", "flood"}:
                value *= max(0.9, min(1.2, enso_modifier))
            combined[k] = self._clip01(value)
        return combined

    def _priority(self, score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.50:
            return "medium"
        return "low"

    def _build_operational_actions(
        self,
        exposures: Dict[str, float],
        regime: str,
        farm_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        irrigation = bool(farm_profile.get("irrigation_available", False))
        drainage_level = (farm_profile.get("drainage_level") or "medium").lower()

        top_risks = sorted(exposures.items(), key=lambda x: x[1], reverse=True)[:3]

        for risk, score in top_risks:
            if risk == "drought":
                actions.append({
                    "horizon": "0-14d",
                    "category": "water_management",
                    "priority": self._priority(score),
                    "action": "Implement irrigation scheduling and soil moisture monitoring",
                    "rationale": "High drought exposure can reduce stand and grain set during sensitive phases.",
                })
                if not irrigation:
                    actions.append({
                        "horizon": "15-60d",
                        "category": "resilience_investment",
                        "priority": "high",
                        "action": "Deploy emergency irrigation backup or shared water access agreement",
                        "rationale": "Farm has no irrigation and drought risk is elevated.",
                    })
            elif risk == "heat":
                actions.append({
                    "horizon": "0-14d",
                    "category": "crop_management",
                    "priority": self._priority(score),
                    "action": "Shift critical field operations to cooler windows and reduce thermal stress",
                    "rationale": "Heat spikes increase flowering and pollination losses.",
                })
            elif risk in {"excess_rain", "flood"}:
                actions.append({
                    "horizon": "0-14d",
                    "category": "drainage",
                    "priority": self._priority(score),
                    "action": "Clear drainage channels and prepare runoff diversion",
                    "rationale": "Excess water and flooding risk can damage root systems and delay operations.",
                })
                if drainage_level == "low":
                    actions.append({
                        "horizon": "15-60d",
                        "category": "resilience_investment",
                        "priority": "high",
                        "action": "Upgrade drainage infrastructure in vulnerable plots",
                        "rationale": "Current drainage level is low for projected precipitation exposure.",
                    })
            elif risk == "disease":
                actions.append({
                    "horizon": "0-14d",
                    "category": "phytosanitary",
                    "priority": self._priority(score),
                    "action": "Increase disease scouting frequency and preventive control readiness",
                    "rationale": "Humid and unstable conditions elevate disease pressure.",
                })
            elif risk == "wind":
                actions.append({
                    "horizon": "0-14d",
                    "category": "field_operations",
                    "priority": self._priority(score),
                    "action": "Protect exposed structures and avoid sensitive spray windows",
                    "rationale": "Strong winds increase lodging and operation risk.",
                })

        if regime == "el_nino":
            actions.append({
                "horizon": "30-120d",
                "category": "seasonal_planning",
                "priority": "medium",
                "action": "Prioritize drought-tolerant cultivars and stagger planting dates",
                "rationale": "El Nino pattern is associated with warmer and drier stress in sensitive regions.",
            })
        elif regime == "la_nina":
            actions.append({
                "horizon": "30-120d",
                "category": "seasonal_planning",
                "priority": "medium",
                "action": "Prioritize drainage-ready fields and strengthen fungal disease prevention",
                "rationale": "La Nina pattern is associated with excess rain in sensitive regions.",
            })

        return actions

    def _build_financial_actions(
        self,
        exposures: Dict[str, float],
        risk_tolerance: str,
    ) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []

        if exposures["drought"] >= 0.60 or exposures["heat"] >= 0.60:
            actions.append({
                "type": "parametric_insurance",
                "priority": "high",
                "strategy": "Use rainfall deficit and heat-degree triggers",
                "expected_benefit": "Protect margin against drought/heat shocks",
            })

        if exposures["excess_rain"] >= 0.60 or exposures["flood"] >= 0.60:
            actions.append({
                "type": "parametric_insurance",
                "priority": "high",
                "strategy": "Use cumulative rainfall and flood-day triggers",
                "expected_benefit": "Protect revenue against excess-rain events",
            })

        if risk_tolerance == "low":
            actions.append({
                "type": "cashflow_protection",
                "priority": "high",
                "strategy": "Increase contingency liquidity coverage for 90 days",
                "expected_benefit": "Reduce forced selling and distress financing",
            })
        else:
            actions.append({
                "type": "hedge",
                "priority": "medium",
                "strategy": "Use partial hedge for input/output price volatility",
                "expected_benefit": "Reduce earnings volatility under climate shocks",
            })

        return actions

    def _build_triggers(self, exposures: Dict[str, float]) -> List[Dict[str, Any]]:
        triggers: List[Dict[str, Any]] = []

        if exposures["drought"] >= 0.55:
            triggers.append({
                "name": "rainfall_deficit_30d",
                "condition": "accumulated_rainfall_30d < climatology_p20",
                "recommended_response": "Escalate irrigation and activate drought contingency",
            })

        if exposures["heat"] >= 0.55:
            triggers.append({
                "name": "heatwave_alert",
                "condition": "forecast_max_temp >= 34C for 3+ consecutive days",
                "recommended_response": "Protect flowering windows and shift field operations",
            })

        if exposures["excess_rain"] >= 0.55 or exposures["flood"] >= 0.55:
            triggers.append({
                "name": "excess_rain_7d",
                "condition": "accumulated_rainfall_7d > climatology_p80",
                "recommended_response": "Activate drainage protocol and disease prevention",
            })

        return triggers

    async def generate_plan(
        self,
        *,
        crop_type: str,
        phenological_stage: str,
        latitude: float,
        longitude: float,
        planning_horizon_days: int,
        risk_tolerance: str,
        farm_profile: Optional[Dict[str, Any]],
        db: Optional[AsyncSession],
    ) -> Dict[str, Any]:
        profile = farm_profile or {}

        enso_context = await self._get_latest_enso_context(db)
        regime = enso_context["regime_label"]
        enso_modifier = float(enso_context["impact_risk_modifier"])

        forecast_source = "unavailable"
        forecast_periods: List[Dict[str, Any]] = []

        try:
            forecast = await self.noaa_service.get_weather_forecast(latitude, longitude)
            forecast_periods = forecast.get("forecast", []) or []
            forecast_source = forecast.get("source", "NOAA/NWS")
        except Exception as exc:
            logger.warning("Weather forecast unavailable in agri strategy: %s", exc)

        base = self._base_regime_exposure(regime)
        weather = self._weather_exposure_from_forecast(forecast_periods)
        multipliers = self._crop_stage_multipliers(crop_type, phenological_stage)
        exposures = self._combined_exposure(base, weather, multipliers, enso_modifier)

        operational_actions = self._build_operational_actions(exposures, regime, profile)
        financial_actions = self._build_financial_actions(exposures, risk_tolerance)
        triggers = self._build_triggers(exposures)

        return {
            "crop_type": crop_type,
            "phenological_stage": phenological_stage,
            "planning_horizon_days": planning_horizon_days,
            "risk_tolerance": risk_tolerance,
            "climate_outlook": {
                "enso": enso_context,
                "forecast_source": forecast_source,
            },
            "exposure_scores": exposures,
            "operational_actions": operational_actions,
            "financial_actions": financial_actions,
            "alert_triggers": triggers,
            "supported_crops": self.supported_crops,
            "supported_stages": self.supported_stages,
        }


agri_strategy_service = AgriculturalStrategyService()

"""
Router for Climate Risk Push Notification Service
Implements: Notificação_push = I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}
Triggers:
- Immediate mitigation recommendation
- Temporary complementary coverage offer
- Customer alert for preventive actions
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import numpy as np

from services.climate_alert_service import (
    climate_alert_service,
    calculate_premium_change,
    calculate_severe_event_probability,
    should_trigger_notification,
    generate_recommendations,
    create_climate_alert,
    generate_complementary_coverage_offer,
    process_climate_notifications
)

class SevereEventProbabilityRequest(BaseModel):
    """Request model for severe event probability calculation"""
    weather_forecast: List[Dict[str, Any]]
    event_thresholds: Optional[Dict[str, float]] = None

class GenerateRecommendationsRequest(BaseModel):
    """Request model for generating recommendations"""
    event_type: str  # 'severe_weather', 'climate_risk_increase', 'premium_change'
    location: Dict[str, float]  # {latitude, longitude}
    severity: int = 3

class CreateClimateAlertRequest(BaseModel):
    """Request model for creating climate alerts"""
    customer_id: str
    contract_id: str
    location: Dict[str, float]  # {latitude, longitude}
    event_type: str
    severity_level: int
    probability: float
    impact_estimate: float
    triggered_condition: str

class ComplementaryCoverageRequest(BaseModel):
    """Request model for generating complementary coverage offers"""
    customer_id: str
    contract_id: str
    event_type: str
    severity: int

class ProcessNotificationsRequest(BaseModel):
    """Request model for processing climate notifications"""
    customer_data: Dict[str, Any]  # {customer_id, contract_id, location}
    premium_history: List[float]
    current_premium: float
    weather_forecast: List[Dict[str, Any]]
    event_thresholds: Optional[Dict[str, float]] = None

router = APIRouter()

@router.post("/climate-alert/premium-change")
async def calculate_premium_change_endpoint(
    historic_premiums: List[float] = Query(..., description="Historical premium values (most recent first)"),
    current_premium: float = Query(..., description="Current premium value"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back")
):
    """
    Calculate percentage change in premium over the specified period
    """
    try:
        change = calculate_premium_change(historic_premiums, current_premium, days)
        return {
            "premium_change_percentage": change,
            "premium_change_proportion": change,
            "current_premium": current_premium,
            "reference_premium": historic_premiums[min(days-1, len(historic_premiums)-1)],
            "days_back": days,
            "historic_premiums_count": len(historic_premiums)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Premium change calculation failed: {str(e)}")

@router.post("/climate-alert/severe-event-probability")
async def calculate_severe_event_probability_endpoint(
    request: SevereEventProbabilityRequest
):
    """
    Calculate probability of severe climate events in the next 72 hours
    """
    try:
        probability = calculate_severe_event_probability(
            request.weather_forecast, request.event_thresholds
        )
        return {
            "severe_event_probability": probability,
            "weather_forecast_periods": len(request.weather_forecast),
            "event_thresholds_used": request.event_thresholds or {
                'precipitation': 50.0, 'wind_speed': 25.0, 'temperature': 35.0, 'pressure': 980.0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Severe event probability calculation failed: {str(e)}")

@router.post("/climate-alert/should-trigger")
async def should_trigger_notification_endpoint(
    premium_change: float = Query(..., description="Percentage change in premium"),
    severe_event_probability: float = Query(..., description="Probability of severe event"),
    premium_threshold: float = Query(0.20, description="Premium change threshold (default 20%)"),
    event_probability_threshold: float = Query(0.05, description="Event probability threshold (default 5%)")
):
    """
    Determine if notification should be triggered:
    Notificação_push = I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}
    """
    try:
        should_trigger, condition = should_trigger_notification(
            premium_change, severe_event_probability, 
            premium_threshold, event_probability_threshold
        )
        return {
            "should_trigger_notification": should_trigger,
            "triggering_condition": condition,
            "premium_change": premium_change,
            "severe_event_probability": severe_event_probability,
            "premium_threshold": premium_threshold,
            "event_probability_threshold": event_probability_threshold,
            "formula_applied": "I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification trigger check failed: {str(e)}")

@router.post("/climate-alert/generate-recommendations")
async def generate_recommendations_endpoint(
    request: GenerateRecommendationsRequest
):
    """
    Generate appropriate recommendations based on event type and severity
    """
    try:
        recommendations = generate_recommendations(
            request.event_type, request.location, request.severity
        )
        return {
            "recommendations": recommendations,
            "event_type": request.event_type,
            "location": request.location,
            "severity_level": request.severity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations generation failed: {str(e)}")

@router.post("/climate-alert/create-alert")
async def create_climate_alert_endpoint(
    request: CreateClimateAlertRequest
):
    """
    Create a climate alert with recommendations
    """
    try:
        alert = create_climate_alert(
            request.customer_id, request.contract_id, request.location, request.event_type,
            request.severity_level, request.probability, request.impact_estimate, request.triggered_condition
        )
        return {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type.value,
            "event_type": alert.event_type.value,
            "triggered_condition": alert.triggered_condition,
            "severity_level": alert.severity_level,
            "customer_id": alert.customer_id,
            "contract_id": alert.contract_id,
            "location": alert.location,
            "probability": alert.probability,
            "impact_estimate": alert.impact_estimate,
            "timestamp": alert.timestamp.isoformat(),
            "recommendations": alert.recommendations,
            "notification_sent": alert.notification_sent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Climate alert creation failed: {str(e)}")

@router.post("/climate-alert/complementary-coverage")
async def generate_complementary_coverage_offer_endpoint(
    request: ComplementaryCoverageRequest
):
    """
    Generate temporary complementary coverage offer
    """
    try:
        offer = generate_complementary_coverage_offer(
            request.customer_id, request.contract_id, request.event_type, request.severity
        )
        return {
            "offer_details": offer,
            "customer_id": request.customer_id,
            "contract_id": request.contract_id,
            "event_type": request.event_type,
            "severity": request.severity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complementary coverage offer generation failed: {str(e)}")

@router.post("/climate-alert/process-notifications")
async def process_climate_notifications_endpoint(
    request: ProcessNotificationsRequest
):
    """
    Complete climate notification processing:
    Notificação_push = I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}
    Triggers mitigation recommendations, complementary coverage offers, and customer alerts
    """
    try:
        actions = process_climate_notifications(
            request.customer_data, request.premium_history, request.current_premium,
            request.weather_forecast, request.event_thresholds
        )
        return {
            "actions_taken": actions,
            "n_customers_affected": len(actions),
            "formula_applied": "I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}",
            "processing_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Climate notification processing failed: {str(e)}")

@router.get("/climate-alert/status")
async def climate_alert_status():
    """
    Get the status of the climate alert service
    """
    return {
        "service_available": True,
        "n_active_alerts": len(getattr(climate_alert_service, 'active_alerts', [])),
        "premium_change_threshold": 0.20,  # 20%
        "severe_event_probability_threshold": 0.05,  # 5%
        "formula_implemented": "Notificação_push = I{ΔPrêmio_7d > 20% OU P(evento_severo_72h) > 5%}",
        "triggered_actions": [
            "Immediate mitigation recommendation",
            "Temporary complementary coverage offer", 
            "Customer alert for preventive actions"
        ],
        "timestamp": datetime.now().isoformat()
    }
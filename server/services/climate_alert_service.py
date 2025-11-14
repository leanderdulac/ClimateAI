"""
Climate Risk Push Notification Service
Implements: Notificação_push = I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}
Triggers:
- Immediate mitigation recommendation
- Temporary complementary coverage offer
- Customer alert for preventive actions
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class AlertType(Enum):
    MITIGATION_RECOMMENDATION = "mitigation_recommendation"
    COMPLEMENTARY_COVERAGE = "complementary_coverage"
    CUSTOMER_PREVENTIVE_ALERT = "customer_preventive_alert"

class EventType(Enum):
    SEVERE_WEATHER = "severe_weather"
    CLIMATE_RISK_INCREASE = "climate_risk_increase"
    PREMIUM_CHANGE = "premium_change"

@dataclass
class ClimateAlert:
    """Structure for climate risk alerts"""
    alert_id: str
    alert_type: AlertType
    event_type: EventType
    triggered_condition: str
    severity_level: int  # 1-5, 5 being most severe
    customer_id: str
    contract_id: str
    location: Dict[str, float]  # Latitude, longitude
    probability: float
    impact_estimate: float
    timestamp: datetime
    recommendations: List[str]
    notification_sent: bool = False

class ClimateAlertService:
    """
    Service implementing climate risk push notifications:
    Notificação_push = I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}
    Triggers mitigation recommendations, complementary coverage offers, and customer preventive alerts
    """
    
    def __init__(self):
        self.active_alerts = []
        self.customer_preferences = {}  # Customer ID -> notification preferences
        self.risk_thresholds = {
            'premium_change_threshold': 0.20,  # 20% premium change triggers alert
            'severe_event_probability': 0.05,  # 5% event probability triggers alert
            'notification_delay_hours': 1,     # Delay before sending notification
        }
        self.mitigation_recommendations = {
            'severe_weather': [
                "Review property protection measures",
                "Secure outdoor equipment",
                "Prepare emergency supplies",
                "Check insurance coverage adequacy"
            ],
            'climate_risk_increase': [
                "Consider additional climate coverage",
                "Schedule property inspection",
                "Update risk mitigation strategies",
                "Review policy limits"
            ]
        }
    
    def calculate_premium_change(self, 
                               historic_premiums: List[float],
                               current_premium: float,
                               days: int = 7) -> float:
        """
        Calculate percentage change in premium over the specified period
        
        Args:
            historic_premiums: List of historical premium values (most recent first)
            current_premium: Current premium value
            days: Number of days to look back (default 7)
            
        Returns:
            Percentage change in premium
        """
        if len(historic_premiums) < 2:
            return 0.0
        
        # Take the premium from 'days' ago (assuming daily data)
        reference_premium = historic_premiums[min(days-1, len(historic_premiums)-1)]
        
        if reference_premium <= 0:
            return 0.0
        
        change_percentage = (current_premium - reference_premium) / reference_premium
        return change_percentage
    
    def calculate_severe_event_probability(self,
                                         weather_forecast: List[Dict[str, Any]],
                                         event_thresholds: Dict[str, float] = None) -> float:
        """
        Calculate probability of severe climate events in the next 72 hours
        
        Args:
            weather_forecast: List of forecast data for next 72 hours
            event_thresholds: Dictionary of thresholds for different severe events
                              Example: {'precipitation': 50, 'wind': 25, 'temperature': 35}
        
        Returns:
            Probability of severe event (0.0 to 1.0)
        """
        if not weather_forecast:
            return 0.0
        
        if event_thresholds is None:
            event_thresholds = {
                'precipitation': 50.0,  # mm in 24h
                'wind_speed': 25.0,     # m/s
                'temperature': 35.0,    # Celsius
                'pressure': 980.0       # hPa
            }
        
        severe_events_count = 0
        total_time_periods = len(weather_forecast)
        
        for forecast_item in weather_forecast:
            is_severe = False
            
            # Check precipitation threshold
            if 'precipitation' in forecast_item and forecast_item['precipitation'] > event_thresholds['precipitation']:
                is_severe = True
            # Check wind speed threshold
            elif 'wind_speed' in forecast_item and forecast_item['wind_speed'] > event_thresholds['wind_speed']:
                is_severe = True
            # Check temperature threshold
            elif 'temperature' in forecast_item and forecast_item['temperature'] > event_thresholds['temperature']:
                is_severe = True
            # Check pressure threshold
            elif 'pressure' in forecast_item and forecast_item['pressure'] < event_thresholds['pressure']:
                is_severe = True
            
            if is_severe:
                severe_events_count += 1
        
        # Calculate probability as ratio of severe periods to total periods
        probability = severe_events_count / total_time_periods if total_time_periods > 0 else 0.0
        
        return min(1.0, probability)  # Ensure probability doesn't exceed 1.0
    
    def should_trigger_notification(self,
                                  premium_change: float,
                                  severe_event_probability: float,
                                  premium_threshold: float = 0.20,
                                  event_probability_threshold: float = 0.05) -> Tuple[bool, str]:
        """
        Determine if notification should be triggered:
        Notificação_push = I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}
        
        Args:
            premium_change: Percentage change in premium over 7 days
            severe_event_probability: Probability of severe event in next 72 hours
            premium_threshold: Threshold for premium change (default 20%)
            event_probability_threshold: Threshold for severe event probability (default 5%)
            
        Returns:
            Tuple of (should_trigger, triggering_condition)
        """
        trigger = False
        condition = "none"
        
        if abs(premium_change) > premium_threshold:
            trigger = True
            condition = f"Premium change {premium_change*100:.1f}% exceeds threshold {premium_threshold*100:.1f}%"
        elif severe_event_probability > event_probability_threshold:
            trigger = True
            condition = f"Severe event probability {severe_event_probability*100:.1f}% exceeds threshold {event_probability_threshold*100:.1f}%"
        
        return trigger, condition
    
    def generate_recommendations(self, 
                               event_type: EventType,
                               location: Dict[str, float],
                               severity: int) -> List[str]:
        """
        Generate appropriate recommendations based on event type and severity
        
        Args:
            event_type: Type of climate event
            location: Location coordinates
            severity: Severity level (1-5)
            
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        if event_type == EventType.SEVERE_WEATHER:
            base_recommendations = self.mitigation_recommendations['severe_weather'].copy()
            # Add severity-specific recommendations
            if severity >= 4:
                base_recommendations.extend([
                    "Evacuation may be necessary",
                    "Contact emergency services",
                    "Activate emergency protocols"
                ])
            elif severity >= 3:
                base_recommendations.append("Monitor weather alerts closely")
            recommendations = base_recommendations
            
        elif event_type == EventType.CLIMATE_RISK_INCREASE:
            base_recommendations = self.mitigation_recommendations['climate_risk_increase'].copy()
            # Add severity-specific recommendations
            if severity >= 4:
                base_recommendations.extend([
                    "Consider policy upgrade",
                    "Contact underwriter for review",
                    "Review risk management strategy"
                ])
            recommendations = base_recommendations
        
        elif event_type == EventType.PREMIUM_CHANGE:
            recommendations = [
                "Review policy coverage adequacy",
                "Check for bundling opportunities",
                "Consider risk mitigation improvements",
                "Contact agent for policy review"
            ]
        
        return recommendations
    
    def create_climate_alert(self,
                           customer_id: str,
                           contract_id: str,
                           location: Dict[str, float],
                           event_type: EventType,
                           severity_level: int,
                           probability: float,
                           impact_estimate: float,
                           triggered_condition: str,
                           custom_recommendations: Optional[List[str]] = None) -> ClimateAlert:
        """
        Create a climate alert with recommendations
        
        Args:
            customer_id: Customer identifier
            contract_id: Contract identifier
            location: Location coordinates
            event_type: Type of climate event
            severity_level: Severity level (1-5)
            probability: Probability of the event
            impact_estimate: Estimated impact value
            triggered_condition: Condition that triggered the alert
            custom_recommendations: Optional custom recommendations
            
        Returns:
            ClimateAlert object
        """
        alert_id = f"CLIMATE_ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_id[:8]}"
        
        if custom_recommendations is None:
            recommendations = self.generate_recommendations(event_type, location, severity_level)
        else:
            recommendations = custom_recommendations
        
        alert = ClimateAlert(
            alert_id=alert_id,
            alert_type=self._determine_alert_type(event_type),
            event_type=event_type,
            triggered_condition=triggered_condition,
            severity_level=min(5, max(1, severity_level)),  # Clamp to 1-5
            customer_id=customer_id,
            contract_id=contract_id,
            location=location,
            probability=probability,
            impact_estimate=impact_estimate,
            timestamp=datetime.now(),
            recommendations=recommendations
        )
        
        self.active_alerts.append(alert)
        return alert
    
    def _determine_alert_type(self, event_type: EventType) -> AlertType:
        """Determine the appropriate alert type based on event type"""
        if event_type == EventType.SEVERE_WEATHER:
            return AlertType.CUSTOMER_PREVENTIVE_ALERT
        elif event_type == EventType.CLIMATE_RISK_INCREASE:
            return AlertType.MITIGATION_RECOMMENDATION
        else:
            return AlertType.MITIGATION_RECOMMENDATION
    
    def generate_complementary_coverage_offer(self,
                                            customer_id: str,
                                            contract_id: str,
                                            event_type: EventType,
                                            severity: int) -> Dict[str, Any]:
        """
        Generate temporary complementary coverage offer
        
        Args:
            customer_id: Customer identifier
            contract_id: Contract identifier
            event_type: Type of climate event
            severity: Severity level (1-5)
            
        Returns:
            Dictionary with coverage offer details
        """
        base_coverage_amount = 10000  # Base amount for temporary coverage
        
        # Adjust coverage based on severity
        coverage_multiplier = 1.0 + (severity - 1) * 0.5  # 1.0x for level 1, 3.0x for level 5
        coverage_amount = base_coverage_amount * coverage_multiplier
        
        # Determine coverage type based on event
        coverage_type = "all_risks"
        if event_type == EventType.SEVERE_WEATHER:
            coverage_type = "weather_related_damage"
        elif event_type == EventType.CLIMATE_RISK_INCREASE:
            coverage_type = "climate_risk_exposure"
        
        # Set validity period based on severity
        validity_days = min(30, 5 + (severity * 3))  # 5-20 days depending on severity
        
        offer = {
            "offer_id": f"COV_OFFER_{customer_id[:8]}_{datetime.now().strftime('%Y%m%d')}",
            "customer_id": customer_id,
            "contract_id": contract_id,
            "coverage_type": coverage_type,
            "coverage_amount": coverage_amount,
            "validity_period_days": validity_days,
            "discount_rate": 0.20 if severity >= 4 else 0.10,  # Higher discount for severe risks
            "activation_required": True,
            "special_terms": [
                "Valid for temporary protection during elevated risk period",
                "Subject to standard exclusions and limitations",
                f"Coverage active for {validity_days} days from activation"
            ]
        }
        
        return offer
    
    def process_climate_notifications(self,
                                    customer_data: Dict[str, Any],
                                    premium_history: List[float],
                                    current_premium: float,
                                    weather_forecast: List[Dict[str, Any]],
                                    event_thresholds: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        Complete climate notification processing:
        Notificação_push = I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}
        Triggers mitigation recommendations, complementary coverage offers, and customer alerts
        
        Args:
            customer_data: Dictionary containing customer information
            premium_history: List of historical premium values
            current_premium: Current premium value
            weather_forecast: Weather forecast for next 72 hours
            event_thresholds: Custom event thresholds
            
        Returns:
            List of notification actions to be taken
        """
        if event_thresholds is None:
            event_thresholds = {
                'precipitation': 50.0,
                'wind_speed': 25.0,
                'temperature': 35.0,
                'pressure': 980.0
            }
        
        # Calculate premium change
        premium_change = self.calculate_premium_change(premium_history, current_premium)
        
        # Calculate severe event probability
        severe_probability = self.calculate_severe_event_probability(weather_forecast, event_thresholds)
        
        # Check if notification should be triggered
        should_notify, triggering_condition = self.should_trigger_notification(
            premium_change, severe_probability
        )
        
        actions = []
        
        if should_notify:
            # Determine event type based on triggering condition
            if "Premium change" in triggering_condition:
                event_type = EventType.PREMIUM_CHANGE
                severity = 3 if abs(premium_change) > 0.30 else 2  # Higher severity for larger changes
                probability = abs(premium_change)
            else:  # Severe event probability
                event_type = EventType.SEVERE_WEATHER
                severity = 4 if severe_probability > 0.15 else 3 if severe_probability > 0.10 else 2
                probability = severe_probability
            
            # Create climate alert
            climate_alert = self.create_climate_alert(
                customer_id=customer_data['customer_id'],
                contract_id=customer_data['contract_id'],
                location=customer_data['location'],
                event_type=event_type,
                severity_level=severity,
                probability=probability,
                impact_estimate=customer_data.get('exposure', 100000),
                triggered_condition=triggering_condition
            )
            
            # Generate complementary coverage offer
            coverage_offer = self.generate_complementary_coverage_offer(
                customer_data['customer_id'],
                customer_data['contract_id'],
                event_type,
                severity
            )
            
            # Create action record
            action = {
                "customer_id": customer_data['customer_id'],
                "contract_id": customer_data['contract_id'],
                "trigger_reason": triggering_condition,
                "alert_created": {
                    "alert_id": climate_alert.alert_id,
                    "severity": climate_alert.severity_level,
                    "timestamp": climate_alert.timestamp.isoformat(),
                    "recommendations": climate_alert.recommendations
                },
                "complementary_coverage_offered": coverage_offer,
                "preventive_actions_sent": climate_alert.recommendations,
                "notification_priority": "high" if severity > 3 else "medium"
            }
            
            actions.append(action)
        
        return actions

# Global instance
climate_alert_service = ClimateAlertService()

# Convenience functions for API integration
def calculate_premium_change(historic_premiums: List[float],
                           current_premium: float,
                           days: int = 7) -> float:
    """Calculate percentage change in premium over the specified period"""
    return climate_alert_service.calculate_premium_change(historic_premiums, current_premium, days)

def calculate_severe_event_probability(weather_forecast: List[Dict[str, Any]],
                                   event_thresholds: Dict[str, float] = None) -> float:
    """Calculate probability of severe climate events in the next 72 hours"""
    return climate_alert_service.calculate_severe_event_probability(weather_forecast, event_thresholds)

def should_trigger_notification(premium_change: float,
                             severe_event_probability: float,
                             premium_threshold: float = 0.20,
                             event_probability_threshold: float = 0.05) -> Tuple[bool, str]:
    """Determine if notification should be triggered: I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}"""
    return climate_alert_service.should_trigger_notification(
        premium_change, severe_event_probability, premium_threshold, event_probability_threshold
    )

def generate_recommendations(event_type: str,
                           location: Dict[str, float],
                           severity: int) -> List[str]:
    """Generate appropriate recommendations based on event type and severity"""
    from services.climate_alert_service import EventType
    event_enum = EventType(event_type)
    return climate_alert_service.generate_recommendations(event_enum, location, severity)

def create_climate_alert(customer_id: str,
                       contract_id: str,
                       location: Dict[str, float],
                       event_type: str,
                       severity_level: int,
                       probability: float,
                       impact_estimate: float,
                       triggered_condition: str) -> ClimateAlert:
    """Create a climate alert with recommendations"""
    from services.climate_alert_service import EventType
    event_enum = EventType(event_type)
    return climate_alert_service.create_climate_alert(
        customer_id, contract_id, location, event_enum, 
        severity_level, probability, impact_estimate, triggered_condition
    )

def generate_complementary_coverage_offer(customer_id: str,
                                        contract_id: str,
                                        event_type: str,
                                        severity: int) -> Dict[str, Any]:
    """Generate temporary complementary coverage offer"""
    from services.climate_alert_service import EventType
    event_enum = EventType(event_type)
    return climate_alert_service.generate_complementary_coverage_offer(
        customer_id, contract_id, event_enum, severity
    )

def process_climate_notifications(customer_data: Dict[str, Any],
                               premium_history: List[float],
                               current_premium: float,
                               weather_forecast: List[Dict[str, Any]],
                               event_thresholds: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """Complete climate notification processing: Notificação_push = I{ΔPrêmio_7d > 20% OR P(evento_severo_72h) > 5%}"""
    return climate_alert_service.process_climate_notifications(
        customer_data, premium_history, current_premium, 
        weather_forecast, event_thresholds
    )
"""
Score Climático de Risco (SCR) - Climate Risk Scoring Module
Implements comprehensive climate risk assessment using multiple data sources and methodologies.
"""
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ClimateRiskType(Enum):
    """Types of climate risks to assess"""
    TEMPERATURE_EXTREMES = "temperature_extremes"
    PRECIPITATION_ANOMALIES = "precipitation_anomalies"
    WIND_STORMS = "wind_storms"
    FLOOD_RISK = "flood_risk"
    DROUGHT_RISK = "drought_risk"
    FIRE_RISK = "fire_risk"

@dataclass
class ClimateRiskScore:
    """Complete climate risk score with all components"""
    overall_score: float  # 0-1 scale (1 = highest risk)
    risk_breakdown: Dict[str, float]  # Individual risk component scores
    temporal_trend: float  # -1 to 1 (negative = decreasing, positive = increasing)
    confidence_level: float  # 0-1 scale
    risk_assessment_date: datetime
    contributing_factors: List[str]
    location_risk_profile: Dict[str, float]
    climate_indices: Dict[str, float]  # Various climate indices

@dataclass
class ClimateData:
    """Input data structure for climate risk assessment"""
    temperature_data: List[Dict[str, float]]  # [{'date': '2023-01-01', 'value': 25.0}]
    precipitation_data: List[Dict[str, float]]  # [{'date': '2023-01-01', 'value': 10.0}]
    wind_data: List[Dict[str, float]]  # [{'date': '2023-01-01', 'value': 15.0}]
    historical_extremes: Dict[str, List[float]]  # {'max_temp': [35, 38, 42], 'max_precip': [50, 60, 100]}
    climate_projections: Dict[str, List[float]]  # Future projections
    location_coordinates: Tuple[float, float]  # (latitude, longitude)
    coverage_period_months: int
    asset_value: float

class SCRRiskScoringEngine:
    """
    Core engine for calculating climate risk scores based on multiple factors:
    - Historical climate data analysis
    - Climate projections 
    - Extreme event patterns
    - Geographic vulnerability factors
    """
    
    def __init__(self):
        self.base_weights = {
            ClimateRiskType.TEMPERATURE_EXTREMES: 0.20,
            ClimateRiskType.PRECIPITATION_ANOMALIES: 0.20,
            ClimateRiskType.WIND_STORMS: 0.15,
            ClimateRiskType.FLOOD_RISK: 0.15,
            ClimateRiskType.DROUGHT_RISK: 0.15,
            ClimateRiskType.FIRE_RISK: 0.15
        }
        self.risk_thresholds = {
            'low': (0.0, 0.3),
            'medium': (0.3, 0.6),
            'high': (0.6, 0.8),
            'very_high': (0.8, 1.0)
        }
        self.temporal_decay_factor = 0.95  # For weighting recent data more heavily

    def calculate_climate_risk_score(self, climate_data: ClimateData) -> ClimateRiskScore:
        """
        Main method to calculate comprehensive climate risk score.
        
        Args:
            climate_data: Input climate data for assessment
            
        Returns:
            ClimateRiskScore with complete risk assessment
        """
        # Calculate individual risk components
        risk_components = {}
        
        # Temperature extremes risk
        risk_components[ClimateRiskType.TEMPERATURE_EXTREMES.value] = \
            self._calculate_temperature_risk(climate_data.temperature_data)
        
        # Precipitation anomalies risk
        risk_components[ClimateRiskType.PRECIPITATION_ANOMALIES.value] = \
            self._calculate_precipitation_risk(climate_data.precipitation_data)
        
        # Wind storms risk
        risk_components[ClimateRiskType.WIND_STORMS.value] = \
            self._calculate_wind_risk(climate_data.wind_data)
        
        # Flood risk based on precipitation and location
        risk_components[ClimateRiskType.FLOOD_RISK.value] = \
            self._calculate_flood_risk(climate_data.precipitation_data, climate_data.location_coordinates)
        
        # Drought risk
        risk_components[ClimateRiskType.DROUGHT_RISK.value] = \
            self._calculate_drought_risk(climate_data.precipitation_data)
        
        # Fire risk based on temperature and precipitation
        risk_components[ClimateRiskType.FIRE_RISK.value] = \
            self._calculate_fire_risk(climate_data.temperature_data, climate_data.precipitation_data)
        
        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(risk_components)
        
        # Determine temporal trend
        temporal_trend = self._calculate_temporal_trend(climate_data)
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence(climate_data)
        
        # Identify contributing factors
        contributing_factors = self._identify_contributing_factors(risk_components)
        
        # Calculate location risk profile
        location_profile = self._calculate_location_risk_profile(climate_data.location_coordinates)
        
        # Calculate climate indices
        climate_indices = self._calculate_climate_indices(climate_data)
        
        return ClimateRiskScore(
            overall_score=overall_score,
            risk_breakdown=risk_components,
            temporal_trend=temporal_trend,
            confidence_level=confidence_level,
            risk_assessment_date=datetime.now(),
            contributing_factors=contributing_factors,
            location_risk_profile=location_profile,
            climate_indices=climate_indices
        )

    def _calculate_temperature_risk(self, temp_data: List[Dict[str, float]]) -> float:
        """Calculate risk from temperature extremes"""
        if not temp_data:
            return 0.3  # Default medium risk if no data

        temps = [item['value'] for item in temp_data]
        if not temps:
            return 0.3

        # Calculate extreme temperature events
        mean_temp = np.mean(temps)
        std_temp = np.std(temps)
        
        # Count extreme events (3+ standard deviations)
        extreme_events = sum(1 for t in temps if abs(t - mean_temp) > 3 * std_temp)
        extreme_event_rate = extreme_events / len(temps)
        
        # Calculate temperature trend
        if len(temps) > 1:
            recent_temps = temps[-min(365, len(temps)):]  # Last year
            if len(recent_temps) > 10:
                trend = np.polyfit(range(len(recent_temps)), recent_temps, 1)[0]
            else:
                trend = 0
        else:
            trend = 0
        
        # Combine metrics into risk score
        # Higher extreme event rate and increasing trend increase risk
        base_risk = min(1.0, extreme_event_rate * 10 + abs(trend) * 2)
        return min(1.0, base_risk)

    def _calculate_precipitation_risk(self, precip_data: List[Dict[str, float]]) -> float:
        """Calculate risk from precipitation anomalies"""
        if not precip_data:
            return 0.3

        precip_values = [item['value'] for item in precip_data]
        if not precip_values:
            return 0.3

        # Calculate coefficient of variation (variability)
        mean_precip = np.mean(precip_values)
        std_precip = np.std(precip_values)
        coef_var = std_precip / mean_precip if mean_precip != 0 else 0
        
        # Count extreme precipitation events (>95th percentile)
        p95_threshold = np.percentile(precip_values, 95) if len(precip_values) > 10 else np.max(precip_values)
        extreme_precip_events = sum(1 for p in precip_values if p > p95_threshold)
        extreme_rate = extreme_precip_events / len(precip_values)
        
        # Combine metrics
        risk = min(1.0, coef_var * 0.5 + extreme_rate * 2.0)
        return risk

    def _calculate_wind_risk(self, wind_data: List[Dict[str, float]]) -> float:
        """Calculate risk from wind-related events"""
        if not wind_data:
            return 0.2

        wind_values = [item['value'] for item in wind_data]
        if not wind_values:
            return 0.2

        # Calculate high wind events (>90th percentile)
        p90_threshold = np.percentile(wind_values, 90) if len(wind_values) > 10 else np.max(wind_values)
        high_wind_events = sum(1 for w in wind_values if w > p90_threshold)
        high_wind_rate = high_wind_events / len(wind_values)
        
        # Calculate wind variability
        mean_wind = np.mean(wind_values)
        std_wind = np.std(wind_values)
        wind_variability = std_wind / mean_wind if mean_wind != 0 else 0
        
        # Combine metrics
        risk = min(1.0, high_wind_rate * 3.0 + wind_variability)
        return risk

    def _calculate_flood_risk(self, precip_data: List[Dict[str, float]], 
                            coordinates: Tuple[float, float]) -> float:
        """Calculate flood risk based on precipitation and geographic factors"""
        if not precip_data:
            return 0.3

        # Start with precipitation-based risk
        precip_risk = self._calculate_precipitation_risk(precip_data)
        
        # Adjust based on geographic factors
        latitude, longitude = coordinates
        base_flood_risk = precip_risk
        
        # Geographic factors that increase flood risk
        # This would typically use real geographic data
        geographic_factor = 1.0  # Simplified for now
        
        # Near-equatorial regions might have higher flood risk
        if abs(latitude) < 23.5:  # Within tropics
            geographic_factor *= 1.2
        
        # Coastal areas might have higher flood risk
        # (In a real system, this would check proximity to water)
        
        return min(1.0, base_flood_risk * geographic_factor)

    def _calculate_drought_risk(self, precip_data: List[Dict[str, float]]) -> float:
        """Calculate drought risk based on precipitation patterns"""
        if not precip_data:
            return 0.3

        precip_values = [item['value'] for item in precip_data]
        if not precip_values:
            return 0.3

        # Calculate low precipitation events (<25th percentile)
        p25_threshold = np.percentile(precip_values, 25) if len(precip_values) > 10 else np.min(precip_values)
        low_precip_events = sum(1 for p in precip_values if p < p25_threshold)
        low_precip_rate = low_precip_events / len(precip_values)
        
        # Check for consecutive low precipitation periods
        consecutive_dry_days = 0
        max_consecutive_dry = 0
        for p in precip_values:
            if p < p25_threshold:
                consecutive_dry_days += 1
                max_consecutive_dry = max(max_consecutive_dry, consecutive_dry_days)
            else:
                consecutive_dry_days = 0
        
        # Combine metrics
        # Longer dry spells increase risk more significantly
        drought_severity = max_consecutive_dry / len(precip_values) if len(precip_values) > 0 else 0
        risk = min(1.0, low_precip_rate + drought_severity * 0.5)
        return risk

    def _calculate_fire_risk(self, temp_data: List[Dict[str, float]], 
                           precip_data: List[Dict[str, float]]) -> float:
        """Calculate fire risk based on temperature and precipitation"""
        temp_risk = self._calculate_temperature_risk(temp_data)
        precip_risk = self._calculate_drought_risk(precip_data)
        
        # Fire risk is high when it's hot AND dry
        # Use weighted combination of temperature and drought factors
        fire_risk = (temp_risk * 0.4) + (precip_risk * 0.6)
        
        return fire_risk

    def _calculate_weighted_score(self, risk_components: Dict[str, float]) -> float:
        """Calculate overall risk score using weighted average of components"""
        total_weight = sum(self.base_weights.values())
        weighted_sum = 0.0
        
        for risk_type, score in risk_components.items():
            weight = self.base_weights.get(ClimateRiskType(risk_type), 0.16)  # Default equal weight
            weighted_sum += score * weight
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.3
        return overall_score

    def _calculate_temporal_trend(self, climate_data: ClimateData) -> float:
        """Calculate temporal trend of risk factors"""
        # For temperature data, calculate recent trend
        temps = [item['value'] for item in climate_data.temperature_data]
        if len(temps) > 365:  # At least 1 year of data
            # Compare last year to first year
            recent_period = temps[-365:]  # Last year
            earlier_period = temps[:365]   # First year
            
            recent_avg = np.mean(recent_period)
            earlier_avg = np.mean(earlier_period)
            
            # Calculate normalized trend
            if earlier_avg != 0:
                trend = (recent_avg - earlier_avg) / abs(earlier_avg)
            else:
                trend = 0.0
                
            # Clamp to reasonable range
            trend = max(-1.0, min(1.0, trend))
        else:
            trend = 0.0  # Default neutral if insufficient data
            
        return trend

    def _calculate_confidence(self, climate_data: ClimateData) -> float:
        """Calculate confidence in the risk assessment"""
        # Confidence based on data completeness and recency
        data_points = [
            len(climate_data.temperature_data),
            len(climate_data.precipitation_data),
            len(climate_data.wind_data)
        ]
        
        # More data points = higher confidence
        avg_data_points = np.mean(data_points) if data_points else 0
        
        # Calculate data recency (how recent is the latest data point)
        if climate_data.temperature_data:
            latest_date = datetime.fromisoformat(
                climate_data.temperature_data[-1]['date']
            ) if 'date' in climate_data.temperature_data[-1] else datetime.now()
            days_since_last = (datetime.now() - latest_date).days
        else:
            days_since_last = 365  # Default if no data
        
        # Higher confidence with more data and more recent data
        confidence = min(1.0, (min(1.0, avg_data_points / 730) + min(1.0, 30 / max(1, days_since_last))) / 2)
        return confidence

    def _identify_contributing_factors(self, risk_components: Dict[str, float]) -> List[str]:
        """Identify the most significant risk factors"""
        significant_factors = []
        for risk_type, score in risk_components.items():
            if score > 0.6:  # Above medium risk
                significant_factors.append(f"{risk_type}: {score:.2f}")
        
        return significant_factors

    def _calculate_location_risk_profile(self, coordinates: Tuple[float, float]) -> Dict[str, float]:
        """Calculate risk profile based on geographic location"""
        latitude, longitude = coordinates
        
        profile = {
            'latitude_factor': float(abs(latitude) / 90.0),  # Polar regions have different risks
            'proximity_tropical': 1.0 if abs(latitude) < 23.5 else 0.0,  # Tropical regions
            'seasonal_variation': float(1.0 if abs(latitude) > 23.5 else 0.5)  # Seasonal variation factor
        }
        
        return profile

    def _calculate_climate_indices(self, climate_data: ClimateData) -> Dict[str, float]:
        """Calculate standard climate indices"""
        indices = {}
        
        # Calculate SPI (Standardized Precipitation Index) equivalent 
        if climate_data.precipitation_data:
            precip_values = [item['value'] for item in climate_data.precipitation_data]
            if len(precip_values) > 30:
                # Simple SPI calculation (30-day period)
                mean_precip = np.mean(precip_values)
                std_precip = np.std(precip_values)
                current_precip = np.mean(precip_values[-30:])  # Last 30 days
                
                if std_precip != 0:
                    spi = (current_precip - mean_precip) / std_precip
                    indices['spi'] = float(spi)
                else:
                    indices['spi'] = 0.0
        
        # Calculate temperature anomaly
        if climate_data.temperature_data:
            temp_values = [item['value'] for item in climate_data.temperature_data]
            if len(temp_values) > 30:
                mean_temp = np.mean(temp_values)
                current_temp = np.mean(temp_values[-30:])  # Last 30 days
                temp_anomaly = current_temp - mean_temp
                indices['temperature_anomaly'] = float(temp_anomaly)
        
        # Default values if calculations couldn't be made
        if 'spi' not in indices:
            indices['spi'] = 0.0
        if 'temperature_anomaly' not in indices:
            indices['temperature_anomaly'] = 0.0
            
        return indices

# Global instance
scr_engine = SCRRiskScoringEngine()

def calculate_climate_risk_score(climate_data: ClimateData) -> ClimateRiskScore:
    """Convenience function to calculate climate risk score"""
    return scr_engine.calculate_climate_risk_score(climate_data)
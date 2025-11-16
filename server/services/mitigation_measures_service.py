"""
Mitigation Measures Calculation Service
Implements: M_mitigação = Σ_k w_k·log(1 + efetividade_k)

Weighted measures:
- Drainage system: 0.25 × ln(1 + drainage_capacity/area)  
- Structural resistance: 0.30 × ln(1 + wind_resistance_class)
- Monitoring system: 0.20 × ln(1 + IoT_sensors)
- Vegetation cover: 0.15 × ln(1 + local_NDVI)
- Refuge distance: 0.10 × ln(1 + d_refuge)

Final Score: SCR = max(0, 1000 × (R_físico + R_transição + R_concentração) × (1 - M_mitigação))
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class MitigationMeasures:
    """Information about implemented mitigation measures"""
    drainage_capacity: float  # m³/s per m² of area
    area_drained: float  # Total area served by drainage system (m²)
    structural_resistance_class: float  # Resistance class for wind/flood (1-10 scale)
    iot_sensors_count: int  # Number of IoT sensors and monitoring devices
    local_ndvi: float  # Normalized Difference Vegetation Index (0-1 scale)
    refuge_distance_km: float  # Distance to nearest refuge in km
    implementation_date: datetime
    effectiveness_rating: float  # Overall effectiveness rating (0-1 scale)
    maintenance_schedule: str  # Maintenance schedule

@dataclass
class ClimateRiskComponents:
    """Input climate risk components for final score calculation"""
    physical_risk: float  # R_físico
    transition_risk: float  # R_transição  
    concentration_risk: float  # R_concentração
    calculation_method: str = "combined_framework"

@dataclass
class MitigationResult:
    """Result of mitigation calculation"""
    mitigation_score: float  # M_mitigação
    mitigation_components: Dict[str, float]  # Individual mitigation factors
    weighted_measure_factors: Dict[str, float]  # Weighted calculation factors
    final_scr_score: float  # Final SCR score
    risk_reduction_percentage: float  # Percentage of risk reduction
    original_total_risk: float  # Original total risk before mitigation
    mitigated_total_risk: float  # Total risk after mitigation
    calculation_timestamp: datetime
    risk_classification: Optional[str] = None  # Risk classification (risco_baixo, risco_moderado, etc.)

class MitigationCalculator:
    """
    Calculates mitigation effectiveness and final climate risk score:
    M_mitigação = Σ_k w_k·log(1 + efetividade_k)
    Final Score: SCR = max(0, 1000 × (R_físico + R_transição + R_concentração) × (1 - M_mitigação))
    """

    def __init__(self):
        # Define weights for mitigation measures (w_k values)
        self.measure_weights = {
            'drainage_system': 0.25,      # 25% weight
            'structural_resistance': 0.30, # 30% weight
            'monitoring_system': 0.20,     # 20% weight
            'vegetation_cover': 0.15,      # 15% weight
            'refuge_distance': 0.10        # 10% weight
        }

        # Define scale factors for different measures
        self.scale_factors = {
            'drainage_capacity': 100,  # Capacity typically measured per 100 m²
            'wind_resistance': 10,     # Resistance class scale
            'iot_sensors': 1,          # Per sensor count
            'ndvi': 1,                 # NDVI scale (0-1)
            'refuge_distance': 1       # Distance in km scale
        }

        # Define SCR thresholds for risk classification
        self.scr_risk_thresholds = {
            'low': (0, 300),
            'moderate': (300, 600),
            'high': (600, 800),
            'critical': (800, float('inf'))
        }
        
        # Define scale factors for different measures
        self.scale_factors = {
            'drainage_capacity': 100,  # Capacity typically measured per 100 m²
            'wind_resistance': 10,     # Resistance class scale
            'iot_sensors': 1,          # Per sensor count
            'ndvi': 1,                 # NDVI scale (0-1)
            'refuge_distance': 1       # Distance in km scale
        }

    def calculate_mitigation_score(self, mitigation_measures: MitigationMeasures) -> MitigationResult:
        """
        Calculate mitigation score based on implemented measures
        
        Args:
            mitigation_measures: Information about implemented mitigation measures
            
        Returns:
            MitigationResult with complete calculation
        """
        # Calculate individual mitigation components
        drainage_factor = np.log(1 + (mitigation_measures.drainage_capacity * mitigation_measures.area_drained) / 10000) 
        drainage_component = self.measure_weights['drainage_system'] * drainage_factor
        
        resistance_factor = np.log(1 + mitigation_measures.structural_resistance_class / 5.0)  # Normalize resistance class
        resistance_component = self.measure_weights['structural_resistance'] * resistance_factor
        
        monitoring_factor = np.log(1 + mitigation_measures.iot_sensors_count / 10.0)  # Normalize sensor count
        monitoring_component = self.measure_weights['monitoring_system'] * monitoring_factor
        
        vegetation_factor = np.log(1 + mitigation_measures.local_ndvi)  # NDVI already in 0-1 range
        vegetation_component = self.measure_weights['vegetation_cover'] * vegetation_factor
        
        refuge_factor = np.log(1 + (1.0 / max(0.1, mitigation_measures.refuge_distance_km)))  # Inverse distance
        refuge_component = self.measure_weights['refuge_distance'] * refuge_factor
        
        # Calculate total mitigation score
        total_mitigation_score = drainage_component + resistance_component + monitoring_component + \
                                vegetation_component + refuge_component
        
        # Normalize to 0-1 scale (theoretical maximum depends on individual factors)
        # For typical implementations, we'll cap at reasonable values
        normalized_mitigation = min(1.0, total_mitigation_score / 2.0)  # Normalize based on expected max
        
        # Store components and weighted factors
        mitigation_components = {
            'drainage_component': drainage_component,
            'resistance_component': resistance_component,
            'monitoring_component': monitoring_component,
            'vegetation_component': vegetation_component,
            'refuge_component': refuge_component
        }
        
        weighted_factors = {
            'drainage_factor': drainage_factor,
            'resistance_factor': resistance_factor,
            'monitoring_factor': monitoring_factor,
            'vegetation_factor': vegetation_factor,
            'refuge_factor': refuge_factor
        }
        
        return MitigationResult(
            mitigation_score=normalized_mitigation,
            mitigation_components=mitigation_components,
            weighted_measure_factors=weighted_factors,
            final_scr_score=0.0,  # Will be calculated in combined method
            risk_reduction_percentage=normalized_mitigation * 100,
            original_total_risk=0.0,  # Will be calculated in combined method
            mitigated_total_risk=0.0,  # Will be calculated in combined method
            calculation_timestamp=datetime.now()
        )

    def calculate_final_scr_score(self, 
                                 risk_components: ClimateRiskComponents,
                                 mitigation_measures: MitigationMeasures) -> MitigationResult:
        """
        Calculate final climate risk score incorporating mitigation measures:
        SCR = max(0, 1000 × (R_físico + R_transição + R_concentração) × (1 - M_mitigação))
        
        Args:
            risk_components: Climate risk components (physical, transition, concentration)
            mitigation_measures: Implemented mitigation measures
            
        Returns:
            MitigationResult with final SCR score
        """
        # Calculate mitigation score first
        mitigation_result = self.calculate_mitigation_score(mitigation_measures)
        
        # Calculate total original risk
        original_total_risk = risk_components.physical_risk + risk_components.transition_risk + risk_components.concentration_risk
        
        # Calculate final SCR score
        mitigated_risk = original_total_risk * (1 - mitigation_result.mitigation_score)
        final_scr_score = max(0, 1000 * mitigated_risk)
        
        # Calculate risk reduction percentage
        risk_reduction_percentage = mitigation_result.mitigation_score * 100
        
        # Calculate risk reduction amount
        risk_reduction_amount = original_total_risk - mitigated_risk
        
        # Calculate risk classification
        risk_classification = self.classify_scr_risk(final_scr_score)

        # Update the result with final calculations and risk classification
        mitigation_result.final_scr_score = final_scr_score
        mitigation_result.original_total_risk = original_total_risk
        mitigation_result.mitigated_total_risk = mitigated_risk
        mitigation_result.risk_reduction_percentage = risk_reduction_percentage
        mitigation_result.risk_classification = risk_classification

        return mitigation_result

    def classify_scr_risk(self, scr_score: float) -> str:
        """
        Classify risk level based on SCR score according to defined thresholds:
        SCR < 300: Risco Baixo
        300 ≤ SCR < 600: Risco Moderado
        600 ≤ SCR < 800: Risco Alto
        SCR ≥ 800: Risco Crítico

        Args:
            scr_score: The calculated SCR score

        Returns:
            Risk level classification as string
        """
        if scr_score < self.scr_risk_thresholds['low'][1]:  # < 300
            return 'risco_baixo'
        elif self.scr_risk_thresholds['moderate'][0] <= scr_score < self.scr_risk_thresholds['moderate'][1]:  # 300 <= SCR < 600
            return 'risco_moderado'
        elif self.scr_risk_thresholds['high'][0] <= scr_score < self.scr_risk_thresholds['high'][1]:  # 600 <= SCR < 800
            return 'risco_alto'
        elif scr_score >= self.scr_risk_thresholds['critical'][0]:  # SCR >= 800
            return 'risco_critico'
        else:
            return 'risco_undefined'  # Should not happen with the current thresholds

    def get_scr_risk_info(self, scr_score: float) -> Dict[str, Any]:
        """
        Get detailed risk classification information based on SCR score

        Args:
            scr_score: The calculated SCR score

        Returns:
            Dictionary with risk classification details
        """
        risk_level = self.classify_scr_risk(scr_score)

        # Determine the Portuguese description
        risk_description = {
            'risco_baixo': 'Baixo',
            'risco_moderado': 'Moderado',
            'risco_alto': 'Alto',
            'risco_critico': 'Crítico'
        }.get(risk_level, 'Undefined')

        # Map Portuguese risk level to English key for threshold lookup
        risk_mapping = {
            'risco_baixo': 'low',
            'risco_moderado': 'moderate',
            'risco_alto': 'high',
            'risco_critico': 'critical'
        }

        english_key = risk_mapping.get(risk_level, 'low')
        risk_range = self.scr_risk_thresholds.get(english_key, (0, float('inf')))

        return {
            'scr_score': scr_score,
            'risk_level': risk_level,
            'risk_description': risk_description,
            'risk_range_min': risk_range[0],
            'risk_range_max': risk_range[1],
            'classification_timestamp': datetime.now().isoformat()
        }

    def evaluate_mitigation_portfolio(self,
                                    mitigation_measures: MitigationMeasures,
                                    desired_risk_reduction: float = 0.30) -> Dict[str, Any]:
        """
        Evaluate a portfolio of mitigation measures against desired risk reduction
        
        Args:
            mitigation_measures: Implemented mitigation measures
            desired_risk_reduction: Target risk reduction percentage (0.0-1.0)
            
        Returns:
            Dictionary with portfolio evaluation results
        """
        # Calculate current mitigation score
        mitigation_result = self.calculate_mitigation_score(mitigation_measures)
        
        # Evaluate effectiveness of each measure
        component_weights = {
            'drainage_system': self.measure_weights['drainage_system'],
            'structural_resistance': self.measure_weights['structural_resistance'],
            'monitoring_system': self.measure_weights['monitoring_system'],
            'vegetation_cover': self.measure_weights['vegetation_cover'],
            'refuge_distance': self.measure_weights['refuge_distance']
        }
        
        # Calculate each component's effectiveness percentage
        total_weight = sum(component_weights.values())
        effectiveness_per_component = {}
        
        for comp_name, weight in component_weights.items():
            comp_key = comp_name.replace('_', '') + '_component'
            component_value = mitigation_result.mitigation_components.get(comp_key, 0)
            effectiveness_per_component[comp_name] = {
                'weight': weight,
                'raw_value': component_value,
                'effectiveness_percentage': (component_value / total_weight) * 100 if total_weight > 0 else 0
            }
        
        # Calculate gap to desired risk reduction
        gap_to_target = max(0, desired_risk_reduction - mitigation_result.mitigation_score)
        
        # Recommendations for improvement
        recommendations = self._generate_recommendations(mitigation_measures, gap_to_target)
        
        return {
            'current_mitigation_score': mitigation_result.mitigation_score,
            'achieved_risk_reduction': mitigation_result.risk_reduction_percentage,
            'desired_risk_reduction': desired_risk_reduction * 100,
            'gap_to_target': gap_to_target,
            'effectiveness_per_component': effectiveness_per_component,
            'current_mitigation_components': mitigation_result.mitigation_components,
            'recommendations': recommendations,
            'portfolio_balance_score': self._calculate_portfolio_balance(mitigation_measures),
            'evaluation_timestamp': datetime.now().isoformat()
        }

    def _generate_recommendations(self, measures: MitigationMeasures, gap_to_target: float) -> List[Dict[str, Any]]:
        """
        Generate recommendations to improve mitigation score
        """
        recommendations = []
        
        # High-impact recommendations based on gaps
        if measures.drainage_capacity < 0.5:
            recommendations.append({
                'measure': 'drainage_system',
                'priority': 'HIGH',
                'action': 'Increase drainage capacity',
                'estimated_impact': 'High improvement in flood risk mitigation',
                'implementation_timeframe': '6-12 months',
                'cost_estimate': 'Medium to High'
            })
        
        if measures.structural_resistance_class < 6.0:
            recommendations.append({
                'measure': 'structural_resistance',
                'priority': 'HIGH',
                'action': 'Enhance structural resistance to wind/flood',
                'estimated_impact': 'Significant improvement in physical risk mitigation',
                'implementation_timeframe': '3-24 months',
                'cost_estimate': 'High'
            })
        
        if measures.iot_sensors_count < 5:
            recommendations.append({
                'measure': 'monitoring_system',
                'priority': 'MEDIUM',
                'action': 'Deploy more IoT sensors for monitoring',
                'estimated_impact': 'Moderate improvement in early warning capability',
                'implementation_timeframe': '1-6 months',
                'cost_estimate': 'Low to Medium'
            })
        
        if measures.local_ndvi < 0.3:
            recommendations.append({
                'measure': 'vegetation_cover',
                'priority': 'MEDIUM',
                'action': 'Increase vegetation coverage',
                'estimated_impact': 'Moderate improvement in local climate regulation',
                'implementation_timeframe': '6-24 months',
                'cost_estimate': 'Low'
            })
        
        if measures.refuge_distance_km > 5.0:
            recommendations.append({
                'measure': 'refuge_distance',
                'priority': 'MEDIUM',
                'action': 'Establish closer emergency refuge facilities',
                'estimated_impact': 'Moderate improvement in safety response capability',
                'implementation_timeframe': '12-24 months',
                'cost_estimate': 'Medium'
            })
        
        return recommendations

    def _calculate_portfolio_balance(self, measures: MitigationMeasures) -> float:
        """
        Calculate how balanced the mitigation portfolio is across different measures
        """
        # Calculate normalized values for each measure (0-1 scale)
        drain_norm = min(1.0, measures.drainage_capacity * measures.area_drained / 50000)  # Normalize drainage
        struct_norm = measures.structural_resistance_class / 10.0  # Wind resistance (1-10)
        sensor_norm = min(1.0, measures.iot_sensors_count / 20.0)  # Normalized sensor count
        veg_norm = measures.local_ndvi  # NDVI already normalized
        refuge_norm = max(0.0, 1.0 - (measures.refuge_distance_km / 10.0))  # Inverse of distance
        
        components = [drain_norm, struct_norm, sensor_norm, veg_norm, refuge_norm]
        component_variance = np.var(components)
        
        # Lower variance means more balanced portfolio
        # Convert to score where higher is better balance (1.0 - variance)
        balance_score = max(0.0, 1.0 - component_variance)
        
        return balance_score

    def calculate_cost_benefit_ratio(self,
                                   mitigation_measures: MitigationMeasures,
                                   risk_components: ClimateRiskComponents,
                                   mitigation_cost: float) -> Dict[str, float]:
        """
        Calculate cost-benefit ratio of mitigation measures
        
        Args:
            mitigation_measures: Implemented mitigation measures
            risk_components: Climate risk components before mitigation
            mitigation_cost: Total cost of implementing mitigation measures
            
        Returns:
            Dictionary with cost-benefit analysis
        """
        # Calculate benefits (risk reduction value)
        mitigation_result = self.calculate_final_scr_score(risk_components, mitigation_measures)
        
        original_risk_value = mitigation_result.original_total_risk
        mitigated_risk_value = mitigation_result.mitigated_total_risk
        risk_reduction_value = original_risk_value - mitigated_risk_value
        
        # Cost-benefit ratio (benefits / costs)
        if mitigation_cost > 0:
            cost_benefit_ratio = risk_reduction_value / mitigation_cost
            benefit_multiple = risk_reduction_value / mitigation_cost if mitigation_cost > 0 else 0
        else:
            cost_benefit_ratio = float('inf')
            benefit_multiple = float('inf')
        
        # Calculate return on investment percentage
        roi_percentage = (risk_reduction_value / mitigation_cost) * 100 if mitigation_cost > 0 else 0
        
        return {
            'mitigation_cost': mitigation_cost,
            'original_risk_value': original_risk_value,
            'mitigated_risk_value': mitigated_risk_value,
            'risk_reduction_value': risk_reduction_value,
            'cost_benefit_ratio': cost_benefit_ratio,
            'roi_percentage': roi_percentage,
            'benefit_multiple': benefit_multiple,
            'net_present_value': risk_reduction_value - mitigation_cost if mitigation_cost > 0 else risk_reduction_value,
            'analysis_timestamp': datetime.now().isoformat()
        }

# Global instance
mitigation_service = MitigationCalculator()

def calculate_mitigation_score(mitigation_measures: MitigationMeasures) -> MitigationResult:
    """Convenience function to calculate mitigation score"""
    return mitigation_service.calculate_mitigation_score(mitigation_measures)

def calculate_final_scr_score(risk_components: ClimateRiskComponents,
                            mitigation_measures: MitigationMeasures) -> MitigationResult:
    """Convenience function to calculate final SCR score"""
    return mitigation_service.calculate_final_scr_score(risk_components, mitigation_measures)

def evaluate_mitigation_portfolio(mitigation_measures: MitigationMeasures,
                               desired_risk_reduction: float = 0.30) -> Dict[str, Any]:
    """Convenience function to evaluate mitigation portfolio"""
    return mitigation_service.evaluate_mitigation_portfolio(mitigation_measures, desired_risk_reduction)

def calculate_cost_benefit_ratio(mitigation_measures: MitigationMeasures,
                               risk_components: ClimateRiskComponents,
                               mitigation_cost: float) -> Dict[str, float]:
    """Convenience function to calculate cost-benefit ratio"""
    return mitigation_service.calculate_cost_benefit_ratio(mitigation_measures, risk_components, mitigation_cost)

def classify_scr_risk(scr_score: float) -> str:
    """Convenience function to classify risk based on SCR score"""
    return mitigation_service.classify_scr_risk(scr_score)

def get_scr_risk_info(scr_score: float) -> Dict[str, Any]:
    """Convenience function to get risk classification info"""
    return mitigation_service.get_scr_risk_info(scr_score)
"""
Physical Risk Calculation Service
Implements: R_físico = Σ_{perigo∈{inundação, vento, fogo, granizo}} p_perigo · λ_perigo · v_perigo

Where:
- p_perigo = P(evento | ΔT, precip, cenário) [from GEV engine]
- λ_perigo = climate-adjusted annual occurrence rate
- v_perigo = vulnerability = f(coef_fragilidade, idade_imóvel, material)

Based on: GEV (Generalized Extreme Value) model approach
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class PhysicalRiskResult:
    """Result of physical risk calculation"""
    total_physical_risk: float  # R_físico
    risk_breakdown: Dict[str, float]  # Individual risk components
    scenario: str
    climate_anomaly: Dict[str, float]  # ΔT, precip changes
    property_vulnerability: Dict[str, float]
    occurrence_rates: Dict[str, float]
    calculation_timestamp: datetime

@dataclass
class PropertyCharacteristics:
    """Property characteristics for vulnerability assessment"""
    age_years: int
    construction_material: str  # 'concrete', 'wood', 'steel', 'masonry'
    elevation_meters: float  # Relative to flood reference
    location_coordinates: Tuple[float, float]  # (lat, lon)
    building_type: str  # 'residential', 'commercial', 'industrial', 'agricultural'
    value: float  # Asset value

@dataclass
class ClimateScenario:
    """Climate scenario inputs"""
    delta_temperature: float  # ΔT in °C
    precipitation_change: float  # Precipitation change in mm
    sea_level_rise: float  # Sea level rise in meters
    climate_model: str  # 'rcp45', 'rcp85', 'ssp126', 'ssp585'
    scenario_year: int
    baseline_year: int = 2020

class PhysicalRiskCalculator:
    """
    Calculates physical risk using GEV model approach:
    R_físico = Σ_{perigo∈{inundação, vento, fogo, granizo}} p_perigo · λ_perigo · v_perigo
    """
    
    def __init__(self):
        # Default parameters for the GEV model
        self.gev_parameters = {
            'flood': {
                'mu_0': 0.5,  # Baseline location parameter
                'sigma': 0.15,  # Scale parameter
                'xi': 0.05,    # Shape parameter (for Gumbel distribution, xi ~ 0)
            },
            'wind': {
                'mu_0': 0.3,
                'sigma': 0.12,
                'xi': 0.03,
            },
            'fire': {
                'mu_0': 0.4,
                'sigma': 0.10,
                'xi': 0.02,
            },
            'hail': {
                'mu_0': 0.2,
                'sigma': 0.08,
                'xi': 0.01,
            }
        }
        
        # Vulnerability coefficients by material
        self.vulnerability_coefs = {
            'concrete': {'flood': 0.2, 'wind': 0.15, 'fire': 0.3, 'hail': 0.1},
            'wood': {'flood': 0.6, 'wind': 0.7, 'fire': 0.8, 'hail': 0.4},
            'steel': {'flood': 0.25, 'wind': 0.1, 'fire': 0.4, 'hail': 0.15},
            'masonry': {'flood': 0.4, 'wind': 0.3, 'fire': 0.5, 'hail': 0.25}
        }
        
        # Occurrence rate multipliers by climate sensitivity
        self.rate_multipliers = {
            'flood': 0.08,  # 8% increase per °C warming
            'wind': 0.05,   # 5% increase per °C warming
            'fire': 0.12,   # 12% increase per °C warming
            'hail': 0.03    # 3% increase per °C warming
        }
        
        # Age-related vulnerability multipliers (older = more vulnerable)
        self.age_vulnerability_curve = lambda age: min(1.5, 1 + 0.01 * age)  # Max 50% increase at 50 years

    def calculate_physical_risk(self, 
                              property_char: PropertyCharacteristics,
                              climate_scenario: ClimateScenario,
                              scenario_name: str = "base") -> PhysicalRiskResult:
        """
        Calculate physical risk using the GEV approach
        
        Args:
            property_char: Property characteristics
            climate_scenario: Climate scenario with temperature/precip changes
            scenario_name: Name of the scenario for tracking
            
        Returns:
            PhysicalRiskResult with complete risk calculation
        """
        # Calculate individual risk components
        risk_components = {}
        
        # Flood risk calculation
        flood_p_event = self._calculate_event_probability(
            'flood', 
            climate_scenario.delta_temperature,
            climate_scenario.precipitation_change,
            property_char.elevation_meters
        )
        flood_lambda = self._calculate_occurrence_rate('flood', climate_scenario.delta_temperature)
        flood_vulnerability = self._calculate_vulnerability('flood', property_char)
        
        risk_components['flood'] = flood_p_event * flood_lambda * flood_vulnerability
        
        # Wind risk calculation
        wind_p_event = self._calculate_event_probability(
            'wind', 
            climate_scenario.delta_temperature,
            climate_scenario.precipitation_change,
            property_char.elevation_meters  # Using elevation as proxy for exposure
        )
        wind_lambda = self._calculate_occurrence_rate('wind', climate_scenario.delta_temperature)
        wind_vulnerability = self._calculate_vulnerability('wind', property_char)
        
        risk_components['wind'] = wind_p_event * wind_lambda * wind_vulnerability
        
        # Fire risk calculation
        fire_p_event = self._calculate_event_probability(
            'fire', 
            climate_scenario.delta_temperature,
            climate_scenario.precipitation_change,
            property_char.elevation_meters  # Less relevant but included for completeness
        )
        fire_lambda = self._calculate_occurrence_rate('fire', climate_scenario.delta_temperature)
        fire_vulnerability = self._calculate_vulnerability('fire', property_char)
        
        risk_components['fire'] = fire_p_event * fire_lambda * fire_vulnerability
        
        # Hail risk calculation
        hail_p_event = self._calculate_event_probability(
            'hail', 
            climate_scenario.delta_temperature,
            climate_scenario.precipitation_change,
            property_char.elevation_meters
        )
        hail_lambda = self._calculate_occurrence_rate('hail', climate_scenario.delta_temperature)
        hail_vulnerability = self._calculate_vulnerability('hail', property_char)
        
        risk_components['hail'] = hail_p_event * hail_lambda * hail_vulnerability
        
        # Total physical risk is the sum of all components
        total_physical_risk = sum(risk_components.values())
        
        # Store additional parameters for transparency
        occurrence_rates = {
            'flood': flood_lambda,
            'wind': wind_lambda, 
            'fire': fire_lambda,
            'hail': hail_lambda
        }
        
        property_vulnerability = {
            'flood': flood_vulnerability,
            'wind': wind_vulnerability,
            'fire': fire_vulnerability, 
            'hail': hail_vulnerability,
            'material_factor': self.vulnerability_coefs[property_char.construction_material],
            'age_factor': self.age_vulnerability_curve(property_char.age_years)
        }
        
        climate_anomaly = {
            'delta_temperature': climate_scenario.delta_temperature,
            'precipitation_change': climate_scenario.precipitation_change,
            'sea_level_rise': climate_scenario.sea_level_rise
        }
        
        return PhysicalRiskResult(
            total_physical_risk=total_physical_risk,
            risk_breakdown=risk_components,
            scenario=scenario_name,
            climate_anomaly=climate_anomaly,
            property_vulnerability=property_vulnerability,
            occurrence_rates=occurrence_rates,
            calculation_timestamp=datetime.now()
        )

    def _calculate_event_probability(self, peril: str, delta_temp: float, 
                                   precip_change: float, elevation: float) -> float:
        """
        Calculate event probability using GEV model approach
        
        Example for flood: p_inundação = 1 - exp(-exp( (h - μ(ΔT)) / σ ))
        μ(ΔT) = μ₀ · (1 + 0.08·ΔT)  [aumento 8% por °C - IPCC AR6]
        h = elevação relativa ao nível de 100 anos
        """
        params = self.gev_parameters[peril]
        
        # Calculate location parameter adjusted for temperature
        # Using IPCC AR6 suggested 8% increase per °C for flood risk (adapted)
        temp_sensitivity = self.rate_multipliers[peril]
        mu_adjusted = params['mu_0'] * (1 + temp_sensitivity * delta_temp)
        
        # Calculate probability using Gumbel distribution (xi ~ 0)
        # P(X <= x) = exp(-exp(-(x - mu) / sigma))
        # But we want the complementary probability of exceedance
        # For simplicity, we'll use: p = 1 - exp(-exp((elevation - mu_adjusted) / sigma))
        
        # Normalize elevation effect (higher elevation = less flood risk)
        if peril == 'flood':
            elevation_effect = max(0.01, min(2.0, 1.0 - elevation / 100.0))  # Scaled effect
        else:
            elevation_effect = 1.0  # Elevation primarily affects flood risk
        
        # Calculate the probability based on the GEV approach
        standardized_value = (elevation - mu_adjusted) / params['sigma']
        # Using Gumbel CDF for exceedance probability
        # For extreme events, we use: P(X > x) = 1 - F(x)
        gev_cdf = np.exp(-np.exp(-standardized_value))
        
        # The base probability adjusted by elevation
        base_prob = max(0.001, min(0.999, 1.0 - gev_cdf)) * elevation_effect
        
        # Adjust for precipitation change (wetter = more risk)
        precip_effect = 1 + (precip_change / 1000) * 0.5  # 50% sensitivity to precipitation
        final_prob = max(0.001, min(0.999, base_prob * precip_effect))
        
        return final_prob

    def _calculate_occurrence_rate(self, peril: str, delta_temp: float) -> float:
        """
        Calculate climate-adjusted annual occurrence rate
        
        λ_perigo = λ_0 * (1 + climate_sensitivity * ΔT)
        """
        # Base occurrence rates (per year)
        base_rates = {
            'flood': 0.02,  # 2% annual chance
            'wind': 0.01,   # 1% annual chance
            'fire': 0.005,  # 0.5% annual chance
            'hail': 0.03    # 3% annual chance
        }
        
        base_rate = base_rates[peril]
        climate_sensitivity = self.rate_multipliers[peril]
        
        # Calculate climate-adjusted rate
        adjusted_rate = base_rate * (1 + climate_sensitivity * delta_temp)
        
        # Prevent negative rates
        return max(0.0001, adjusted_rate)  # Minimum 0.01% annual rate

    def _calculate_vulnerability(self, peril: str, property_char: PropertyCharacteristics) -> float:
        """
        Calculate vulnerability based on property characteristics
        
        v_perigo = f(coef_fragilidade, idade_imóvel, material)
        """
        # Base vulnerability from material
        material_vuln = self.vulnerability_coefs[property_char.construction_material][peril]
        
        # Age-related vulnerability (older properties more vulnerable)
        age_vuln_multiplier = self.age_vulnerability_curve(property_char.age_years)
        
        # Calculate final vulnerability
        vulnerability = min(0.95, material_vuln * age_vuln_multiplier)
        
        return vulnerability

    def calculate_scenario_comparison(self, 
                                    property_char: PropertyCharacteristics,
                                    baseline_scenario: ClimateScenario,
                                    future_scenario: ClimateScenario) -> Dict[str, Any]:
        """
        Compare risk between baseline and future climate scenarios
        
        Args:
            property_char: Property characteristics
            baseline_scenario: Current climate conditions
            future_scenario: Future climate conditions
            
        Returns:
            Dictionary with risk comparison results
        """
        # Calculate risks for both scenarios
        baseline_risk = self.calculate_physical_risk(
            property_char, baseline_scenario, "baseline"
        )
        
        future_risk = self.calculate_physical_risk(
            property_char, future_scenario, "future"
        )
        
        # Calculate changes
        risk_increase = future_risk.total_physical_risk - baseline_risk.total_physical_risk
        risk_ratio = future_risk.total_physical_risk / baseline_risk.total_physical_risk if baseline_risk.total_physical_risk > 0 else 1.0
        
        return {
            'baseline_risk': baseline_risk.total_physical_risk,
            'future_risk': future_risk.total_physical_risk,
            'risk_increase': risk_increase,
            'risk_ratio': risk_ratio,
            'risk_percentage_increase': (risk_ratio - 1) * 100,
            'baseline_breakdown': baseline_risk.risk_breakdown,
            'future_breakdown': future_risk.risk_breakdown,
            'comparison_date': datetime.now().isoformat()
        }

    def integrate_with_climate_risk(self, 
                                  climate_risk_score: float,
                                  physical_risk_result: PhysicalRiskResult) -> Dict[str, float]:
        """
        Integrate physical risk with broader climate risk scoring
        
        Args:
            climate_risk_score: Overall climate risk from upstream module
            physical_risk_result: Physical risk calculation result
            
        Returns:
            Dictionary with integrated risk metrics
        """
        # Weight physical risk components based on overall climate risk
        weighted_physical_risk = climate_risk_score * physical_risk_result.total_physical_risk
        
        # Calculate amplification factor
        amplification = physical_risk_result.total_physical_risk / max(0.01, climate_risk_score) if climate_risk_score > 0 else 1.0
        
        return {
            'integrated_risk_score': weighted_physical_risk,
            'amplification_factor': amplification,
            'physical_risk_contribution': physical_risk_result.total_physical_risk,
            'climate_risk_base': climate_risk_score
        }

# Global instance
physical_risk_service = PhysicalRiskCalculator()

def calculate_physical_risk(property_char: PropertyCharacteristics,
                          climate_scenario: ClimateScenario,
                          scenario_name: str = "base") -> PhysicalRiskResult:
    """Convenience function to calculate physical risk"""
    return physical_risk_service.calculate_physical_risk(property_char, climate_scenario, scenario_name)

def calculate_scenario_comparison(property_char: PropertyCharacteristics,
                               baseline_scenario: ClimateScenario,
                               future_scenario: ClimateScenario) -> Dict[str, Any]:
    """Convenience function to calculate scenario comparison"""
    return physical_risk_service.calculate_scenario_comparison(property_char, baseline_scenario, future_scenario)

def integrate_with_climate_risk(climate_risk_score: float,
                              physical_risk_result: PhysicalRiskResult) -> Dict[str, float]:
    """Convenience function to integrate with climate risk"""
    return physical_risk_service.integrate_with_climate_risk(climate_risk_score, physical_risk_result)
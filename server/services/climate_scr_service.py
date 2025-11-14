"""
Climate Solvency Capital Requirement (SCR) Service with Uncertainty Coefficient
Implements Margem = SCR_climatico · √(1 + Ψ²) where Ψ = uncertainty coefficient
Ψ = f(prazo_projecao, qualidade_dados) with different values for different time horizons
"""
import numpy as np
from scipy.stats import norm, chi2
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ProjectionHorizon(Enum):
    SHORT_TERM = "short_term"      # 1-3 years
    MEDIUM_TERM = "medium_term"    # 3-10 years
    LONG_TERM = "long_term"        # >10 years

@dataclass
class ClimateSCRResult:
    """Result of climate SCR calculation"""
    base_scr: float
    uncertainty_coefficient: float
    margin: float
    projection_horizon: ProjectionHorizon
    data_quality_score: float
    time_horizon_years: float

class ClimateSCRService:
    """
    Service implementing Climate Solvency Capital Requirement with uncertainty coefficient
    Margem = SCR_climatico · √(1 + Ψ²)
    where Ψ = uncertainty coefficient = f(prazo_projecao, qualidade_dados)
    """
    
    def __init__(self):
        self.uncertainty_defaults = {
            ProjectionHorizon.SHORT_TERM: 0.15,  # 15%
            ProjectionHorizon.MEDIUM_TERM: 0.35,  # 35%
            ProjectionHorizon.LONG_TERM: 0.60     # 60%
        }
        self.data_quality_weights = {
            'excellent': 1.0,
            'good': 0.8,
            'fair': 0.6,
            'poor': 0.3,
            'unknown': 0.5
        }
    
    def calculate_basic_scr(self, 
                           climate_risk_factors: Dict[str, float],
                           portfolio_exposure: float,
                           confidence_level: float = 0.995) -> float:
        """
        Calculate basic climate Solvency Capital Requirement (SCR)
        
        Args:
            climate_risk_factors: Climate risk factors {factor_name: sensitivity}
            portfolio_exposure: Portfolio exposure value
            confidence_level: Confidence level for SCR calculation (default 99.5%)
            
        Returns:
            Basic SCR value
        """
        # Calculate basic SCR based on climate risk factors
        # This is a simplified calculation - in practice this would be much more complex
        base_scr = portfolio_exposure * confidence_level  # Placeholder calculation
        
        # Apply climate risk factor multipliers
        for factor_name, sensitivity in climate_risk_factors.items():
            # Different climate factors contribute differently to risk
            factor_multiplier = 1.0 + sensitivity
            base_scr *= factor_multiplier
        
        # Apply regulatory standard formula factors
        # This is where the complex correlation structures would be applied
        base_scr *= 0.1  # Simplified regulatory multiplier
        
        return base_scr
    
    def determine_uncertainty_coefficient(self, 
                                        projection_horizon: ProjectionHorizon,
                                        data_quality: str = 'good',
                                        additional_uncertainty: float = 0.0) -> float:
        """
        Determine uncertainty coefficient Ψ based on:
        - projection horizon (prazo_projecao) 
        - data quality (qualidade_dados)
        - additional uncertainty sources
        
        Args:
            projection_horizon: Time horizon for projection
            data_quality: Quality of underlying data ('excellent', 'good', 'fair', 'poor', 'unknown')
            additional_uncertainty: Additional uncertainty from model or data sources
            
        Returns:
            Uncertainty coefficient Ψ
        """
        # Base uncertainty based on time horizon
        base_uncertainty = self.uncertainty_defaults[projection_horizon]
        
        # Data quality adjustment
        quality_weight = self.data_quality_weights.get(data_quality, self.data_quality_weights['unknown'])
        
        # Calculate final uncertainty coefficient
        uncertainty_coeff = base_uncertainty * quality_weight + additional_uncertainty
        
        # Ensure reasonable bounds
        return min(2.0, max(0.01, uncertainty_coeff))  # Clamp between 0.01 and 2.0
    
    def calculate_climate_scr_margin(self,
                                   base_scr: float,
                                   uncertainty_coefficient: float) -> float:
        """
        Calculate climate SCR margin: Margem = SCR_climatico · √(1 + Ψ²)
        
        Args:
            base_scr: Basic climate SCR value
            uncertainty_coefficient: Uncertainty coefficient Ψ
            
        Returns:
            Climate SCR margin
        """
        margin = base_scr * np.sqrt(1 + uncertainty_coefficient**2)
        return margin
    
    def calculate_climate_scr_with_uncertainty(self,
                                             climate_risk_factors: Dict[str, float],
                                             portfolio_exposure: float,
                                             projection_horizon: ProjectionHorizon,
                                             data_quality: str = 'good',
                                             confidence_level: float = 0.995,
                                             additional_uncertainty: float = 0.0,
                                             time_horizon_years: float = 5.0) -> ClimateSCRResult:
        """
        Complete climate SCR calculation with uncertainty:
        Margem = SCR_climatico · √(1 + Ψ²)
        
        Args:
            climate_risk_factors: Climate risk factors {factor_name: sensitivity}
            portfolio_exposure: Portfolio exposure value
            projection_horizon: Time horizon category (SHORT_TERM, MEDIUM_TERM, LONG_TERM)
            data_quality: Quality of underlying data
            confidence_level: Confidence level for SCR calculation
            additional_uncertainty: Additional uncertainty sources
            time_horizon_years: Exact time horizon in years
            
        Returns:
            ClimateSCRResult with complete calculation
        """
        # Calculate basic SCR
        base_scr = self.calculate_basic_scr(
            climate_risk_factors, portfolio_exposure, confidence_level
        )
        
        # Determine uncertainty coefficient
        psi = self.determine_uncertainty_coefficient(
            projection_horizon, data_quality, additional_uncertainty
        )
        
        # Calculate final margin
        margin = self.calculate_climate_scr_margin(base_scr, psi)
        
        return ClimateSCRResult(
            base_scr=base_scr,
            uncertainty_coefficient=psi,
            margin=margin,
            projection_horizon=projection_horizon,
            data_quality_score=self.data_quality_weights.get(data_quality, 0.5),
            time_horizon_years=time_horizon_years
        )
    
    def calculate_scr_with_dynamic_horizon(self,
                                         climate_risk_factors: Dict[str, float],
                                         portfolio_exposure: float,
                                         time_horizon_years: float,
                                         data_quality: str = 'good',
                                         confidence_level: float = 0.995) -> ClimateSCRResult:
        """
        Calculate climate SCR considering dynamic time horizon effects
        
        Args:
            climate_risk_factors: Climate risk factors {factor_name: sensitivity}
            portfolio_exposure: Portfolio exposure value
            time_horizon_years: Time horizon in years
            data_quality: Quality of underlying data
            confidence_level: Confidence level for SCR calculation
            
        Returns:
            ClimateSCRResult with time-sensitive calculation
        """
        # Determine appropriate horizon category based on years
        if 1 <= time_horizon_years <= 3:
            projection_horizon = ProjectionHorizon.SHORT_TERM
        elif 3 < time_horizon_years <= 10:
            projection_horizon = ProjectionHorizon.MEDIUM_TERM
        else:
            projection_horizon = ProjectionHorizon.LONG_TERM
        
        # Calculate base SCR
        base_scr = self.calculate_basic_scr(
            climate_risk_factors, portfolio_exposure, confidence_level
        )
        
        # Determine uncertainty coefficient with dynamic adjustment
        base_uncertainty = self.uncertainty_defaults[projection_horizon]
        
        # Additional adjustment based on exact time horizon
        if projection_horizon == ProjectionHorizon.LONG_TERM:
            # For long term, add additional uncertainty based on how far out the projection is
            extra_long_term_uncertainty = min(0.3, 0.02 * max(0, time_horizon_years - 10))
            base_uncertainty += extra_long_term_uncertainty
        
        # Apply data quality adjustment
        quality_weight = self.data_quality_weights.get(data_quality, self.data_quality_weights['unknown'])
        psi = base_uncertainty * quality_weight
        
        # Calculate final margin
        margin = self.calculate_climate_scr_margin(base_scr, psi)
        
        return ClimateSCRResult(
            base_scr=base_scr,
            uncertainty_coefficient=psi,
            margin=margin,
            projection_horizon=projection_horizon,
            data_quality_score=self.data_quality_weights.get(data_quality, 0.5),
            time_horizon_years=time_horizon_years
        )
    
    def calculate_regulatory_compliant_scr(self,
                                         climate_risk_factors: Dict[str, float],
                                         portfolio_exposure: float,
                                         time_horizon_years: float,
                                         data_quality: str = 'good',
                                         confidence_level: float = 0.995,
                                         stress_scenarios: Optional[List[Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Calculate regulatory-compliant climate SCR following insurance regulation standards
        
        Args:
            climate_risk_factors: Climate risk factors {factor_name: sensitivity}
            portfolio_exposure: Portfolio exposure value
            time_horizon_years: Time horizon in years
            data_quality: Quality of underlying data
            confidence_level: Confidence level for SCR calculation
            stress_scenarios: Additional stress scenarios to consider
            
        Returns:
            Dictionary with regulatory compliant SCR calculation
        """
        # Calculate base SCR with uncertainty
        result = self.calculate_scr_with_dynamic_horizon(
            climate_risk_factors, portfolio_exposure, time_horizon_years, 
            data_quality, confidence_level
        )
        
        # Apply regulatory calculations
        base_scr = result.base_scr
        uncertainty_coefficient = result.uncertainty_coefficient
        margin = result.margin
        
        # Calculate additional components that regulators might require
        diversification_credit = 0.0  # Simplified - in practice would consider correlations
        risk_aggregation = margin  # This is already aggregated
        
        # Apply stress scenario adjustments if provided
        stressed_margin = margin
        if stress_scenarios:
            stress_multipliers = []
            for scenario in stress_scenarios:
                # Apply each stress scenario
                scenario_risk_multiplier = 1.0
                for factor, stress_level in scenario.items():
                    if factor in climate_risk_factors:
                        # Increase risk based on stress level
                        scenario_risk_multiplier *= (1 + stress_level)
                
                stress_multipliers.append(scenario_risk_multiplier)
            
            # Use maximum stressed margin
            if stress_multipliers:
                max_stress_multiplier = max(stress_multipliers)
                stressed_margin = margin * max_stress_multiplier
        
        # Regulatory floor - minimum SCR requirements
        regulatory_floor = portfolio_exposure * 0.02  # 2% minimum (simplified)
        final_scr = max(regulatory_floor, stressed_margin)
        
        return {
            'final_scr': final_scr,
            'base_scr': base_scr,
            'uncertainty_coefficient': uncertainty_coefficient,
            'margin_before_stress': margin,
            'margin_after_stress': stressed_margin,
            'regulatory_floor_applied': final_scr != stressed_margin,
            'diversification_credit': diversification_credit,
            'risk_aggregation': risk_aggregation,
            'projection_horizon': result.projection_horizon.value,
            'data_quality_score': result.data_quality_score,
            'time_horizon_years': time_horizon_years,
            'confidence_level': confidence_level,
            'uncertainty_components': {
                'base_uncertainty': self.uncertainty_defaults[result.projection_horizon],
                'data_quality_factor': result.data_quality_score,
                'additional_uncertainty': max(0, uncertainty_coefficient - self.uncertainty_defaults[result.projection_horizon] * result.data_quality_score)
            },
            'formula_check': f"{base_scr:.2f} * sqrt(1 + {uncertainty_coefficient:.3f}²) = {margin:.2f}"
        }

# Global instance
climate_scr_service = ClimateSCRService()

# Convenience functions for API integration
def calculate_basic_scr(climate_risk_factors: Dict[str, float],
                      portfolio_exposure: float,
                      confidence_level: float = 0.995) -> float:
    """Calculate basic climate Solvency Capital Requirement (SCR)"""
    return climate_scr_service.calculate_basic_scr(
        climate_risk_factors, portfolio_exposure, confidence_level
    )

def determine_uncertainty_coefficient(projection_horizon: str,
                                   data_quality: str = 'good',
                                   additional_uncertainty: float = 0.0) -> float:
    """Determine uncertainty coefficient Ψ based on time horizon and data quality"""
    horizon_enum = ProjectionHorizon(projection_horizon)
    return climate_scr_service.determine_uncertainty_coefficient(
        horizon_enum, data_quality, additional_uncertainty
    )

def calculate_climate_scr_margin(base_scr: float,
                               uncertainty_coefficient: float) -> float:
    """Calculate climate SCR margin: Margem = SCR_climatico · √(1 + Ψ²)"""
    return climate_scr_service.calculate_climate_scr_margin(base_scr, uncertainty_coefficient)

def calculate_climate_scr_with_uncertainty(
    climate_risk_factors: Dict[str, float],
    portfolio_exposure: float,
    projection_horizon: str,
    data_quality: str = 'good',
    confidence_level: float = 0.995,
    additional_uncertainty: float = 0.0,
    time_horizon_years: float = 5.0
) -> ClimateSCRResult:
    """Complete climate SCR calculation with uncertainty"""
    horizon_enum = ProjectionHorizon(projection_horizon)
    return climate_scr_service.calculate_climate_scr_with_uncertainty(
        climate_risk_factors, portfolio_exposure, horizon_enum, 
        data_quality, confidence_level, additional_uncertainty, time_horizon_years
    )

def calculate_scr_with_dynamic_horizon(
    climate_risk_factors: Dict[str, float],
    portfolio_exposure: float,
    time_horizon_years: float,
    data_quality: str = 'good',
    confidence_level: float = 0.995
) -> ClimateSCRResult:
    """Climate SCR calculation with dynamic time horizon adjustment"""
    return climate_scr_service.calculate_scr_with_dynamic_horizon(
        climate_risk_factors, portfolio_exposure, time_horizon_years,
        data_quality, confidence_level
    )

def calculate_regulatory_compliant_scr(
    climate_risk_factors: Dict[str, float],
    portfolio_exposure: float,
    time_horizon_years: float,
    data_quality: str = 'good',
    confidence_level: float = 0.995,
    stress_scenarios: Optional[List[Dict[str, float]]] = None
) -> Dict[str, Any]:
    """Regulatory-compliant climate SCR calculation"""
    return climate_scr_service.calculate_regulatory_compliant_scr(
        climate_risk_factors, portfolio_exposure, time_horizon_years,
        data_quality, confidence_level, stress_scenarios
    )
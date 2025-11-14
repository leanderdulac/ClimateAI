"""
Advanced Extreme Value Analysis Service for Climate Risk Modeling
Implements Generalized Extreme Value (GEV) and Generalized Pareto Distribution (GPD) models
for modeling rare climate events and tail risk assessment
"""
import numpy as np
from scipy import stats
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GEVParameters:
    """Parameters for Generalized Extreme Value distribution"""
    location: float    # μ (mu)
    scale: float       # σ (sigma)
    shape: float       # ξ (xi)
    return_period: float
    confidence_interval: Tuple[float, float]

@dataclass
class GPDParameters:
    """Parameters for Generalized Pareto Distribution"""
    threshold: float   # u (threshold)
    scale: float       # σ (sigma)
    shape: float       # ξ (xi)
    exceedance_prob: float
    confidence_interval: Tuple[float, float]

class ExtremeValueService:
    """
    Service implementing extreme value theory for climate risk modeling
    with GEV (Generalized Extreme Value) and GPD (Generalized Pareto Distribution)
    """

    def __init__(self):
        self.gev_models = {}
        self.gpd_models = {}

    def fit_gev_distribution(self, data: List[float], return_period: float = 50.0) -> GEVParameters:
        """
        Fit Generalized Extreme Value distribution to block maxima data
        
        Args:
            data: Annual maxima or block maxima data
            return_period: Return period for risk assessment (years)
            
        Returns:
            GEVParameters with fitted parameters and return level estimates
        """
        if len(data) < 10:
            raise ValueError("Need at least 10 data points for GEV fitting")
        
        data_array = np.array(data)
        
        # Use maximum likelihood estimation for GEV parameters
        def gev_neg_log_likelihood(params):
            mu, sigma, xi = params
            if sigma <= 0:
                return np.inf
            return -np.sum(stats.genextreme.logpdf(data_array, -xi, loc=mu, scale=sigma))
        
        # Initial parameter estimates
        initial_params = [np.mean(data_array), np.std(data_array), 0.1]
        
        # Optimize parameters
        result = minimize(gev_neg_log_likelihood, initial_params, method='BFGS')
        
        if not result.success:
            # Fallback to method of moments if MLE fails
            mu = np.mean(data_array)
            sigma = np.std(data_array)
            xi = 0.1
        else:
            mu, sigma, xi = result.x
        
        # Calculate return level for specified return period
        # For GEV: x_T = μ - σ/ξ * [1 - (-log(1-1/T))^(-ξ)]
        if xi != 0:
            return_level = mu - (sigma / xi) * (1 - ((-np.log(1 - 1/return_period)) ** (-xi)))
        else:
            # Gumbel case (ξ = 0)
            return_level = mu - sigma * np.log(-np.log(1 - 1/return_period))
        
        # Calculate approximate confidence intervals using delta method
        # Simplified approach - in practice use bootstrap or profile likelihood
        se_return = sigma * np.sqrt(1.1) / np.sqrt(len(data))  # Rough approximation
        ci_lower = return_level - 1.96 * se_return
        ci_upper = return_level + 1.96 * se_return
        
        return GEVParameters(
            location=mu,
            scale=sigma,
            shape=xi,
            return_period=return_period,
            confidence_interval=(ci_lower, ci_upper)
        )

    def gev_distribution_cdf(self, z: float, mu: float, sigma: float, xi: float) -> float:
        """
        Calculate CDF of Generalized Extreme Value distribution using the formula:
        G(z) = exp{ -[1 + ξ((z-μ)/σ)]^(-1/ξ) }

        Args:
            z: Value at which to evaluate the CDF
            mu: Location parameter
            sigma: Scale parameter
            xi: Shape parameter

        Returns:
            CDF value at z
        """
        if sigma <= 0:
            raise ValueError("Scale parameter must be positive")

        # Handle different cases based on shape parameter
        if xi == 0:
            # Gumbel case
            standardized = (z - mu) / sigma
            cdf_val = np.exp(-np.exp(-standardized))
        else:
            # General case
            standardized = (z - mu) / sigma
            temp = 1 + xi * standardized

            # Check for valid domain
            if temp <= 0:
                # Return 0 if outside domain
                return 0.0

            cdf_val = np.exp(-np.power(temp, -1/xi))

        return min(1.0, max(0.0, cdf_val))

    def calculate_climate_adapted_gev_params(self, base_params: GEVParameters,
                                           delta_temperature: float,
                                           delta_precipitation: float,
                                           co2_level: float,
                                           alpha: float = 0.02,  # Temperature sensitivity
                                           beta: float = 0.01,   # Precipitation sensitivity
                                           gamma: float = 0.001) -> GEVParameters:
        """
        Calculate climate-adapted GEV parameters using the model:
        μ_t = μ_0 × (1 + α·ΔT_t + β·ΔPrecip_t)
        σ_t = σ_0 × exp(γ·CO2_t)

        Args:
            base_params: Base GEV parameters (μ_0, σ_0, ξ_0)
            delta_temperature: Change in temperature (ΔT_t)
            delta_precipitation: Change in precipitation (ΔPrecip_t)
            co2_level: CO2 concentration level
            alpha: Temperature sensitivity parameter
            beta: Precipitation sensitivity parameter
            gamma: CO2 sensitivity parameter

        Returns:
            Climate-adapted GEV parameters
        """
        # Update location parameter: μ_t = μ_0 × (1 + α·ΔT_t + β·ΔPrecip_t)
        mu_t = base_params.location * (1 + alpha * delta_temperature + beta * delta_precipitation)

        # Update scale parameter: σ_t = σ_0 × exp(γ·CO2_t)
        sigma_t = base_params.scale * np.exp(gamma * co2_level)

        # Shape parameter typically remains stable under climate change
        xi_t = base_params.shape

        return GEVParameters(
            location=mu_t,
            scale=sigma_t,
            shape=xi_t,
            return_period=base_params.return_period,
            confidence_interval=base_params.confidence_interval
        )

    def calculate_return_level_with_climate_adaptation(self, base_params: GEVParameters,
                                                     delta_temperature: float,
                                                     delta_precipitation: float,
                                                     co2_level: float,
                                                     return_period: float,
                                                     alpha: float = 0.02,
                                                     beta: float = 0.01,
                                                     gamma: float = 0.001) -> Dict[str, float]:
        """
        Calculate return level accounting for climate adaptation

        Args:
            base_params: Base GEV parameters
            delta_temperature: Change in temperature
            delta_precipitation: Change in precipitation
            co2_level: CO2 concentration level
            return_period: Return period for calculation
            alpha, beta, gamma: Climate sensitivity parameters

        Returns:
            Dictionary with return levels for base and adapted conditions
        """
        # Get adapted parameters
        adapted_params = self.calculate_climate_adapted_gev_params(
            base_params, delta_temperature, delta_precipitation, co2_level, alpha, beta, gamma
        )

        # Calculate return level for adapted parameters
        # For GEV: x_T = μ - σ/ξ * [1 - (-log(1-1/T))^(-ξ)]
        if adapted_params.shape != 0:
            adapted_return_level = (adapted_params.location -
                                  (adapted_params.scale / adapted_params.shape) *
                                  (1 - ((-np.log(1 - 1/return_period)) ** (-adapted_params.shape))))
        else:
            # Gumbel case (ξ = 0)
            adapted_return_level = (adapted_params.location -
                                  adapted_params.scale * np.log(-np.log(1 - 1/return_period)))

        # Also calculate for base parameters if needed for comparison
        if base_params.shape != 0:
            base_return_level = (base_params.location -
                               (base_params.scale / base_params.shape) *
                               (1 - ((-np.log(1 - 1/return_period)) ** (-base_params.shape))))
        else:
            base_return_level = (base_params.location -
                               base_params.scale * np.log(-np.log(1 - 1/return_period)))

        return {
            'base_return_level': base_return_level,
            'adapted_return_level': adapted_return_level,
            'difference': adapted_return_level - base_return_level,
            'adapted_parameters': {
                'location': adapted_params.location,
                'scale': adapted_params.scale,
                'shape': adapted_params.shape
            },
            'climate_factors': {
                'delta_temperature': delta_temperature,
                'delta_precipitation': delta_precipitation,
                'co2_level': co2_level,
                'alpha': alpha,
                'beta': beta,
                'gamma': gamma
            }
        }

    def fit_gpd_distribution(self, data: List[float], threshold: float) -> GPDParameters:
        """
        Fit Generalized Pareto Distribution to exceedances over threshold
        
        Args:
            data: Raw data series
            threshold: Threshold value for exceedance modeling
            
        Returns:
            GPDParameters with fitted parameters for tail modeling
        """
        data_array = np.array(data)
        exceedances = data_array[data_array > threshold] - threshold
        
        if len(exceedances) < 5:
            raise ValueError("Need at least 5 exceedances above threshold for GPD fitting")
        
        # Calculate exceedance probability
        exceedance_prob = len(exceedances) / len(data_array)
        
        # Maximum likelihood estimation for GPD
        def gpd_neg_log_likelihood(params):
            sigma, xi = params
            if sigma <= 0 or np.any(1 + xi * exceedances / sigma <= 0):
                return np.inf
            return -np.sum(stats.genpareto.logpdf(exceedances, xi, scale=sigma))
        
        # Initial parameter estimates using method of moments
        if np.var(exceedances) > 0:
            # Method of moments estimators
            mu_hat = np.mean(exceedances)
            var_hat = np.var(exceedances)
            xi_init = -0.5 * (mu_hat ** 2) / var_hat
            sigma_init = -mu_hat * xi_init
        else:
            xi_init = 0.1
            sigma_init = 1.0
        
        initial_params = [sigma_init, xi_init]
        
        # Optimize parameters
        result = minimize(gpd_neg_log_likelihood, initial_params, method='BFGS')
        
        if not result.success:
            # Fallback to method of moments if MLE fails
            xi = xi_init
            sigma = sigma_init
        else:
            sigma, xi = result.x
        
        # Calculate confidence intervals (simplified approach)
        n_exceed = len(exceedances)
        se_sigma = sigma / np.sqrt(n_exceed)
        se_xi = abs(xi) / np.sqrt(n_exceed)
        
        ci_lower = max(0, sigma - 1.96 * se_sigma)
        ci_upper = sigma + 1.96 * se_sigma
        
        return GPDParameters(
            threshold=threshold,
            scale=sigma,
            shape=xi,
            exceedance_prob=exceedance_prob,
            confidence_interval=(ci_lower, ci_upper)
        )

    def calculate_extreme_event_probability(self, data: List[float], threshold: float, 
                                          event_magnitude: float) -> Dict[str, float]:
        """
        Calculate probability of extreme events using GPD model
        
        Args:
            data: Historical data
            threshold: Threshold for extreme event definition
            event_magnitude: Magnitude of event to evaluate
            
        Returns:
            Dictionary with extreme event probabilities and return periods
        """
        if event_magnitude <= threshold:
            return {
                'probability': 0.0,
                'return_period': np.inf,
                'exceedance_probability': 0.0
            }
        
        # Fit GPD to get tail parameters
        gpd_params = self.fit_gpd_distribution(data, threshold)
        
        # Calculate probability of exceeding the event magnitude
        exceedance_prob = gpd_params.exceedance_prob
        excess = event_magnitude - threshold
        
        # GPD CDF: F(x) = 1 - (1 + ξ(x-u)/σ)^(-1/ξ)
        if gpd_params.shape != 0:
            gpd_prob = 1 - (1 + gpd_params.shape * excess / gpd_params.scale) ** (-1/gpd_params.shape)
        else:
            # Exponential case (ξ = 0)
            gpd_prob = 1 - np.exp(-excess / gpd_params.scale)
        
        # Overall probability of exceeding the threshold event
        overall_prob = exceedance_prob * gpd_prob
        
        # Return period
        return_period = 1 / overall_prob if overall_prob > 0 else np.inf
        
        return {
            'probability': overall_prob,
            'return_period': return_period,
            'exceedance_probability': exceedance_prob,
            'tail_probability': gpd_prob,
            'event_magnitude': event_magnitude,
            'threshold': threshold,
            'gpd_shape': gpd_params.shape,
            'gpd_scale': gpd_params.scale
        }

    def block_maxima_analysis(self, time_series: List[float], block_size: int = 365) -> Dict[str, Any]:
        """
        Perform block maxima analysis using GEV distribution
        
        Args:
            time_series: Time series of climate data
            block_size: Size of blocks (e.g., 365 for annual maxima)
            
        Returns:
            Dictionary with block maxima analysis results
        """
        if len(time_series) < block_size * 2:  # Need at least 2 blocks
            raise ValueError(f"Need at least {2 * block_size} data points for block maxima analysis")
        
        # Extract block maxima
        blocks = [time_series[i:i+block_size] for i in range(0, len(time_series), block_size)]
        block_maxima = [max(block) for block in blocks if len(block) == block_size]
        
        # Fit GEV distribution to block maxima
        gev_params = self.fit_gev_distribution(block_maxima)
        
        # Calculate return levels for different return periods
        return_periods = [10, 25, 50, 100, 200]
        return_levels = {}
        
        for t in return_periods:
            if gev_params.shape != 0:
                level = gev_params.location - (gev_params.scale / gev_params.shape) * (1 - ((-np.log(1 - 1/t)) ** (-gev_params.shape)))
            else:
                level = gev_params.location - gev_params.scale * np.log(-np.log(1 - 1/t))
            return_levels[t] = level
        
        return {
            'n_blocks': len(block_maxima),
            'block_maxima': block_maxima,
            'gev_parameters': {
                'location': gev_params.location,
                'scale': gev_params.scale,
                'shape': gev_params.shape
            },
            'return_levels': return_levels,
            'confidence_interval': {
                'lower': gev_params.confidence_interval[0],
                'upper': gev_params.confidence_interval[1]
            }
        }

    def peaks_over_threshold_analysis(self, data: List[float], threshold: float, 
                                    r: float = 0.25) -> Dict[str, Any]:
        """
        Perform Peaks Over Threshold analysis using GPD
        
        Args:
            data: Time series data
            threshold: Threshold for POT analysis
            r: Clustering parameter for declustering events
            
        Returns:
            Dictionary with POT analysis results
        """
        # Find exceedances
        data_array = np.array(data)
        exceed_indices = np.where(data_array > threshold)[0]
        
        # Cluster exceedances if r > 0 (declustering)
        if r > 0:
            clustered_exceeds = []
            if len(exceed_indices) > 0:
                clustered_exceeds.append(exceed_indices[0])
                for idx in exceed_indices[1:]:
                    if idx > clustered_exceeds[-1] + r * len(data_array):
                        clustered_exceeds.append(idx)
            exceedances = data_array[clustered_exceeds] - threshold
        else:
            exceedances = data_array[exceed_indices] - threshold
        
        # Fit GPD to exceedances
        gpd_params = self.fit_gpd_distribution(data, threshold)
        
        # Calculate mean excess function for threshold selection validation
        thresholds_for_validation = np.linspace(np.percentile(data, 70), np.percentile(data, 95), 10)
        mean_excess_values = []
        
        for t_val in thresholds_for_validation:
            excesses = data_array[data_array > t_val] - t_val
            if len(excesses) > 0:
                mean_excess_values.append(np.mean(excesses))
            else:
                mean_excess_values.append(0)
        
        return {
            'n_exceedances': len(exceedances),
            'gpd_parameters': {
                'threshold': gpd_params.threshold,
                'scale': gpd_params.scale,
                'shape': gpd_params.shape,
                'exceedance_prob': gpd_params.exceedance_prob
            },
            'confidence_interval': {
                'lower': gpd_params.confidence_interval[0],
                'upper': gpd_params.confidence_interval[1]
            },
            'mean_excess_validation': {
                'thresholds': thresholds_for_validation.tolist(),
                'mean_excess_values': mean_excess_values
            }
        }

    def combined_gev_gpd_analysis(self, time_series: List[float], threshold: float = None) -> Dict[str, Any]:
        """
        Combined GEV and GPD analysis for comprehensive extreme value modeling
        
        Args:
            time_series: Climate time series data
            threshold: Threshold for GPD analysis (if None, estimate from data)
            
        Returns:
            Combined analysis results using both GEV and GPD models
        """
        # Use 90th percentile as default threshold if not provided
        if threshold is None:
            threshold = np.percentile(time_series, 90)
        
        # Perform block maxima analysis
        block_size = min(365, len(time_series) // 10)  # Ensure at least 10 blocks
        gev_results = self.block_maxima_analysis(time_series, block_size)
        
        # Perform POT analysis
        pot_results = self.peaks_over_threshold_analysis(time_series, threshold)
        
        # Estimate Value at Risk (VaR) and Expected Shortfall (ES) using POT
        data_array = np.array(time_series)
        exceedance_prob = pot_results['gpd_parameters']['exceedance_prob']
        gpd_shape = pot_results['gpd_parameters']['shape']
        gpd_scale = pot_results['gpd_parameters']['scale']
        
        # VaR at 99.5% level (common in insurance)
        alpha = 0.995
        if gpd_shape != 0:
            var_995 = threshold + (gpd_scale / gpd_shape) * (((exceedance_prob / (1 - alpha)) ** gpd_shape) - 1)
        else:
            var_995 = threshold + gpd_scale * np.log(exceedance_prob / (1 - alpha))
        
        # Expected Shortfall estimate
        if gpd_shape < 1:
            es_995 = var_995 + (gpd_scale - gpd_shape * threshold) / (1 - gpd_shape)
        else:
            es_995 = np.inf  # Not finite when shape >= 1
        
        return {
            'block_maxima_analysis': gev_results,
            'peaks_over_threshold_analysis': pot_results,
            'risk_metrics': {
                'var_995': var_995,
                'es_995': es_995,
                'threshold_used': threshold,
                'exceedance_probability': exceedance_prob
            },
            'model_comparison': {
                'gev_applicable': len(gev_results['block_maxima']) >= 10,
                'gpd_applicable': len(data_array[data_array > threshold]) >= 5
            }
        }

    def get_extreme_event_return_period(self, data: List[float], event_value: float, 
                                      method: str = 'gpd') -> Dict[str, float]:
        """
        Calculate return period for a given extreme event value
        
        Args:
            data: Historical time series data
            event_value: Value of the extreme event
            method: 'gev' for block maxima or 'gpd' for peaks over threshold
            
        Returns:
            Dictionary with return period and probability information
        """
        if method == 'gev':
            # For GEV, we need block maxima data
            block_maxima = [max(data[i:i+365]) for i in range(0, len(data), 365) if i+365 <= len(data)]
            if len(block_maxima) < 10:
                raise ValueError("Insufficient block maxima data for GEV method")
            
            gev_params = self.fit_gev_distribution(block_maxima)
            
            # Calculate probability of exceeding event_value
            # P(X > x) = 1 - GEV_CDF(x)
            if gev_params.shape != 0:
                z = (event_value - gev_params.location) / gev_params.scale
                gev_cdf = np.exp(-((1 + gev_params.shape * z) ** (-1/gev_params.shape)))
            else:
                z = (event_value - gev_params.location) / gev_params.scale
                gev_cdf = np.exp(-np.exp(-z))
            
            exceedance_prob = 1 - gev_cdf
            return_period = 1 / exceedance_prob if exceedance_prob > 0 else np.inf
            
        else:  # GPD method
            # Determine threshold for POT analysis (use 90th percentile)
            threshold = np.percentile(data, 90)
            
            if event_value <= threshold:
                return {
                    'return_period': np.inf,
                    'probability': 0.0,
                    'method_used': method,
                    'event_value': event_value,
                    'threshold': threshold
                }
            
            gpd_params = self.fit_gpd_distribution(data, threshold)
            
            # Calculate probability using GPD
            excess = event_value - threshold
            if gpd_params.shape != 0:
                gpd_cdf = 1 - (1 + gpd_params.shape * excess / gpd_params.scale) ** (-1/gpd_params.shape)
            else:
                gpd_cdf = 1 - np.exp(-excess / gpd_params.scale)
            
            # Overall exceedance probability
            exceedance_prob = gpd_params.exceedance_prob * (1 - gpd_cdf)
            return_period = 1 / exceedance_prob if exceedance_prob > 0 else np.inf
        
        return {
            'return_period': return_period,
            'probability': exceedance_prob,
            'method_used': method,
            'event_value': event_value,
            'threshold': threshold if method == 'gpd' else None
        }

# Global instance
extreme_value_service = ExtremeValueService()

# Convenience functions for API integration
def calculate_extreme_event_probability(data: List[float], threshold: float, 
                                     event_magnitude: float) -> Dict[str, float]:
    """Calculate probability of extreme events using GPD model"""
    return extreme_value_service.calculate_extreme_event_probability(
        data, threshold, event_magnitude
    )

def block_maxima_analysis(time_series: List[float], block_size: int = 365) -> Dict[str, Any]:
    """Perform block maxima analysis using GEV distribution"""
    return extreme_value_service.block_maxima_analysis(time_series, block_size)

def peaks_over_threshold_analysis(data: List[float], threshold: float) -> Dict[str, Any]:
    """Perform Peaks Over Threshold analysis using GPD"""
    return extreme_value_service.peaks_over_threshold_analysis(data, threshold)

def combined_gev_gpd_analysis(time_series: List[float], threshold: float = None) -> Dict[str, Any]:
    """Combined GEV and GPD analysis for comprehensive extreme value modeling"""
    return extreme_value_service.combined_gev_gpd_analysis(time_series, threshold)
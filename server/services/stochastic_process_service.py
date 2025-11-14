"""
Stochastic Processes and Climate Modeling Service
Implements advanced stochastic processes for climate modeling:
- ARIMA models for time series forecasting
- Copula models for multivariate dependence
- Regime-switching models for climate state transitions
"""
import numpy as np
from scipy import stats
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

logger = logging.getLogger(__name__)

@dataclass
class ARIMAModelParams:
    """Parameters for ARIMA model"""
    p: int  # Auto-regressive order
    d: int  # Differencing order
    q: int  # Moving average order
    coefficients: List[float]
    aic: float
    bic: float

@dataclass
class CopulaParams:
    """Parameters for Copula model"""
    type: str  # 'gaussian', 'clayton', 'gumbel', 'frank'
    parameter: float
    kendall_tau: float

class StochasticProcessService:
    """
    Service implementing advanced stochastic processes for climate modeling:
    - ARIMA for time series modeling
    - Copula models for multivariate dependence
    - Stochastic volatility models
    - Regime-switching models
    """
    
    def __init__(self):
        self.arima_models = {}
        self.copula_models = {}
    
    def fit_arima_model(self, time_series: List[float], max_p: int = 5, 
                       max_d: int = 2, max_q: int = 5) -> ARIMAModelParams:
        """
        Fit ARIMA model using AIC/BIC criteria for order selection
        
        Args:
            time_series: Input time series data
            max_p: Maximum AR order to consider
            max_d: Maximum differencing order to consider
            max_q: Maximum MA order to consider
            
        Returns:
            ARIMAModelParams with optimal parameters
        """
        if len(time_series) < 10:
            raise ValueError("Time series must have at least 10 observations")
        
        best_aic = np.inf
        best_bic = np.inf
        best_params = (0, 0, 0)
        best_coeffs = []
        
        for p in range(max_p + 1):
            for d in range(max_d + 1):
                for q in range(max_q + 1):
                    if p + q == 0 and d == 0:  # Skip (0,0,0) case
                        continue
                    
                    try:
                        # Apply differencing
                        series = np.array(time_series)
                        for _ in range(d):
                            series = np.diff(series)
                        
                        if len(series) < max(p, q) + 1:
                            continue
                        
                        # Fit ARIMA(p,d,q) using Yule-Walker for AR and method of moments for MA
                        fitted_params, aic, bic = self._fit_arima_simple(series, p, q)
                        
                        if aic < best_aic:
                            best_aic = aic
                            best_bic = bic
                            best_params = (p, d, q)
                            best_coeffs = fitted_params
                    except Exception:
                        continue  # Skip if fitting fails
        
        return ARIMAModelParams(
            p=best_params[0], 
            d=best_params[1], 
            q=best_params[2],
            coefficients=best_coeffs,
            aic=best_aic,
            bic=best_bic
        )
    
    def _fit_arima_simple(self, series: np.ndarray, p: int, q: int) -> Tuple[List[float], float, float]:
        """
        Simple ARIMA fitting using least squares approach
        """
        n = len(series)
        
        if p == 0 and q == 0:  # Simple mean model
            mean_val = np.mean(series)
            residuals = series - mean_val
            mse = np.mean(residuals ** 2)
            aic = n * np.log(mse) + 2 * 1  # 1 parameter (mean)
            bic = n * np.log(mse) + np.log(n) * 1
            return [mean_val], aic, bic
        
        # Create design matrix for AR terms
        X = []
        y = []
        
        start_idx = max(p, q)
        
        for i in range(start_idx, n):
            row = []
            
            # AR terms
            for j in range(1, p + 1):
                if i - j >= 0:
                    row.append(series[i - j])
                else:
                    row.append(0)
            
            # MA terms (estimated from residuals of AR part)
            # For simplicity, we'll use a regression approach
            X.append(row)
            y.append(series[i])
        
        if len(X) < max(p, q) + 1:
            raise ValueError("Insufficient data points after differencing")
        
        X = np.array(X)
        y = np.array(y)
        
        # Fit using least squares
        if X.shape[0] > X.shape[1]:  # More samples than features
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
            fitted_values = X @ coeffs
            residuals = y - fitted_values
        else:
            # Simple mean if insufficient data
            mean_val = np.mean(y)
            coeffs = [mean_val] + [0] * (len(X[0]) - 1) if len(X[0]) > 0 else [mean_val]
            residuals = y - mean_val
        
        mse = np.mean(residuals ** 2)
        n_params = len(coeffs)
        aic = len(y) * np.log(mse) + 2 * n_params
        bic = len(y) * np.log(mse) + np.log(len(y)) * n_params
        
        return coeffs.tolist(), aic, bic
    
    def forecast_arima(self, time_series: List[float], steps: int, 
                      arima_params: ARIMAModelParams) -> List[float]:
        """
        Generate forecasts using fitted ARIMA model
        
        Args:
            time_series: Historical time series data
            steps: Number of steps to forecast
            arima_params: Fitted ARIMA model parameters
            
        Returns:
            List of forecasted values
        """
        series = np.array(time_series)
        
        # Apply differencing
        for _ in range(arima_params.d):
            series = np.diff(series)
        
        forecasts = []
        current_series = series.copy()
        
        for _ in range(steps):
            # Use fitted coefficients to make prediction
            if len(current_series) < max(arima_params.p, arima_params.q):
                # Use last value if insufficient data
                pred = current_series[-1] if len(current_series) > 0 else 0
            else:
                pred = 0
                # Add intercept
                if len(arima_params.coefficients) > 0:
                    pred += arima_params.coefficients[0]
                
                # Add AR terms
                for j in range(1, min(len(arima_params.coefficients), arima_params.p + 1)):
                    if len(current_series) >= j:
                        pred += arima_params.coefficients[j] * current_series[-j]
            
            forecasts.append(float(pred))
            
            # Update series with new prediction
            current_series = np.append(current_series, pred)
        
        # Reverse differencing to get original scale
        for _ in range(arima_params.d):
            if len(forecasts) > 0:
                # For differenced series, add last historical value to get original
                forecasts = [forecasts[0] + series[-1]] if len(forecasts) == 1 else forecasts
                for i in range(1, len(forecasts)):
                    forecasts[i] = forecasts[i] + forecasts[i-1]
        
        return forecasts
    
    def fit_copula_model(self, data1: List[float], data2: List[float], 
                        copula_type: str = 'gaussian') -> CopulaParams:
        """
        Fit copula model to capture dependence structure between two variables
        
        Args:
            data1: First variable time series
            data2: Second variable time series
            copula_type: Type of copula ('gaussian', 'clayton', 'gumbel', 'frank')
            
        Returns:
            CopulaParams with fitted parameters
        """
        if len(data1) != len(data2):
            raise ValueError("Both datasets must have same length")
        
        if len(data1) < 5:
            raise ValueError("Need at least 5 observations for copula fitting")
        
        # Calculate Kendall's tau for dependence measure
        tau = self._kendall_tau(data1, data2)
        
        # Estimate copula parameter based on tau
        if copula_type == 'gaussian':
            # For Gaussian copula: rho = sin(pi * tau / 2)
            param = np.sin(np.pi * tau / 2)
        elif copula_type == 'clayton':
            # For Clayton: tau = theta / (theta + 2)
            if abs(tau - 1.0) < 1e-10:  # tau approaching 1
                param = 100.0  # Maximum allowed theta
            else:
                param = max(0.1, 2 * tau / (1 - tau)) if tau != 1 else 100.0
        elif copula_type == 'gumbel':
            # For Gumbel: tau = (theta - 1) / theta
            if abs(tau - 1.0) < 1e-10:
                param = 100.0  # Maximum allowed theta
            else:
                param = max(1.0, 1 / (1 - tau)) if tau != 1 else 100.0
        elif copula_type == 'frank':
            # For Frank: more complex relationship, use approximation
            if tau == 0:
                param = 0.0
            else:
                # Simplified approximation
                param = 18 * tau / (np.pi**2 * tau - 6 * np.abs(tau))
        else:
            raise ValueError(f"Unsupported copula type: {copula_type}")
        
        return CopulaParams(
            type=copula_type,
            parameter=param,
            kendall_tau=tau
        )
    
    def _kendall_tau(self, x: List[float], y: List[float]) -> float:
        """
        Calculate Kendall's tau correlation coefficient
        """
        n = len(x)
        if n < 2:
            return 0.0
        
        concordant = 0
        discordant = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                if (x[i] - x[j]) * (y[i] - y[j]) > 0:
                    concordant += 1
                elif (x[i] - x[j]) * (y[i] - y[j]) < 0:
                    discordant += 1
        
        total_pairs = concordant + discordant
        if total_pairs == 0:
            return 0.0
        
        return (concordant - discordant) / total_pairs
    
    def generate_copula_samples(self, copula_params: CopulaParams, 
                              n_samples: int) -> Tuple[List[float], List[float]]:
        """
        Generate samples from fitted copula model
        
        Args:
            copula_params: Fitted copula parameters
            n_samples: Number of samples to generate
            
        Returns:
            Tuple of two marginal samples
        """
        if copula_params.type == 'gaussian':
            # For Gaussian copula
            rho = copula_params.parameter
            cov_matrix = [[1.0, rho], [rho, 1.0]]
            samples = np.random.multivariate_normal([0, 0], cov_matrix, n_samples)
            # Transform to uniform using normal CDF
            u1 = stats.norm.cdf(samples[:, 0])
            u2 = stats.norm.cdf(samples[:, 1])
        elif copula_params.type == 'clayton':
            # Simplified generation for Clayton copula
            theta = copula_params.parameter
            v = np.random.exponential(1.0, n_samples)
            u1 = np.random.uniform(0, 1, n_samples)
            # This is a simplified approach; full implementation is more complex
            u2 = ((1 - u1**(-theta)) * np.random.uniform(0, 1, n_samples)**(1/v) + 1)**(-1/theta)
        elif copula_params.type == 'gumbel':
            # Simplified generation for Gumbel copula
            theta = copula_params.parameter
            # This requires more complex implementation
            # Using approximation with normal copula for now
            rho = 1 - 1/theta if theta > 1 else 0.5
            cov_matrix = [[1.0, rho], [rho, 1.0]]
            samples = np.random.multivariate_normal([0, 0], cov_matrix, n_samples)
            u1 = stats.norm.cdf(samples[:, 0])
            u2 = stats.norm.cdf(samples[:, 1])
        else:  # 'frank'
            # Simplified approach for Frank copula
            rho = copula_params.parameter / (copula_params.parameter + 2)  # Approximate correlation
            cov_matrix = [[1.0, rho], [rho, 1.0]]
            samples = np.random.multivariate_normal([0, 0], cov_matrix, n_samples)
            u1 = stats.norm.cdf(samples[:, 0])
            u2 = stats.norm.cdf(samples[:, 1])
        
        # Ensure values are in [0,1] range
        u1 = np.clip(u1, 0.001, 0.999)
        u2 = np.clip(u2, 0.001, 0.999)
        
        return u1.tolist(), u2.tolist()
    
    def regime_switching_model(self, time_series: List[float], n_states: int = 2) -> Dict[str, Any]:
        """
        Fit a simple regime-switching model to identify climate states
        
        Args:
            time_series: Input time series data
            n_states: Number of regimes/states
            
        Returns:
            Dictionary with regime switching model results
        """
        if len(time_series) < 20:
            raise ValueError("Need at least 20 observations for regime switching model")
        
        series = np.array(time_series)
        
        # Use K-means clustering as a simple way to identify regimes
        from sklearn.cluster import KMeans
        
        # Create features for clustering (current value, trend, volatility)
        features = []
        for i in range(10, len(series)):
            # Current value
            current_val = series[i]
            
            # Recent trend (last 5 points vs prior 5)
            if i >= 15:
                recent_avg = np.mean(series[i-4:i+1])
                earlier_avg = np.mean(series[i-9:i-4])
                trend = recent_avg - earlier_avg
            else:
                trend = 0
            
            # Volatility (std of recent values)
            recent_std = np.std(series[max(0, i-10):i+1])
            
            features.append([current_val, trend, recent_std])
        
        if len(features) < n_states:
            n_states = len(features)
        
        if n_states < 2:
            n_states = 2
            
        kmeans = KMeans(n_clusters=n_states, random_state=42)
        regimes = kmeans.fit_predict(features)
        
        # Calculate regime statistics
        regime_stats = []
        for reg in range(n_states):
            mask = regimes == reg
            if np.any(mask):
                reg_values = series[10:][mask]  # Adjust for feature offset
                regime_info = {
                    'regime_id': int(reg),
                    'mean': float(np.mean(reg_values)),
                    'std': float(np.std(reg_values)),
                    'count': int(np.sum(mask)),
                    'probability': float(np.sum(mask) / len(mask))
                }
                regime_stats.append(regime_info)
            else:
                regime_info = {
                    'regime_id': int(reg),
                    'mean': 0.0,
                    'std': 0.0,
                    'count': 0,
                    'probability': 0.0
                }
                regime_stats.append(regime_info)
        
        # Calculate transition probabilities
        transition_matrix = np.zeros((n_states, n_states))
        for i in range(len(regimes) - 1):
            from_reg = regimes[i]
            to_reg = regimes[i + 1]
            transition_matrix[from_reg, to_reg] += 1
        
        # Normalize to probabilities
        for i in range(n_states):
            row_sum = np.sum(transition_matrix[i, :])
            if row_sum > 0:
                transition_matrix[i, :] /= row_sum
        
        return {
            'n_states': n_states,
            'regimes': regimes.tolist(),
            'regime_statistics': regime_stats,
            'transition_matrix': transition_matrix.tolist(),
            'regime_probabilities': [reg['probability'] for reg in regime_stats],
            'current_regime': int(regimes[-1]) if len(regimes) > 0 else 0
        }
    
    def stochastic_volatility_model(self, returns: List[float]) -> Dict[str, float]:
        """
        Fit a simple stochastic volatility model (log-normal) to return series
        
        Args:
            returns: Series of returns/changes
            
        Returns:
            Dictionary with volatility model parameters
        """
        if len(returns) < 10:
            raise ValueError("Need at least 10 observations for volatility modeling")
        
        log_returns = np.array(returns)
        
        # Fit log-normal volatility model
        # h(t) = α_0 + α_1 * h(t-1) + η(t) where h(t) = log(var(t))
        
        # For simplicity, use GARCH(1,1) type modeling approach
        squared_returns = log_returns ** 2
        
        # Estimate long-run average volatility
        long_run_vol = np.mean(squared_returns)
        
        # Estimate volatility persistence
        lagged_squared = squared_returns[:-1]
        current_squared = squared_returns[1:]
        
        if len(lagged_squared) > 0:
            # Estimate persistence parameter
            persistence = np.corrcoef(lagged_squared, current_squared)[0, 1] if len(lagged_squared) > 1 else 0.0
            persistence = max(0.01, min(0.99, persistence))  # Bound between 0.01 and 0.99
        else:
            persistence = 0.5
        
        # Calculate current volatility level
        current_vol = np.std(log_returns[-30:]) if len(log_returns) >= 30 else np.std(log_returns)
        
        return {
            'long_run_volatility': float(np.sqrt(long_run_vol)),
            'volatility_persistence': max(0.0, persistence),
            'current_volatility': float(current_vol),
            'volatility_clustering_parameter': max(0.0, 1 - persistence),
            'n_observations': len(returns)
        }
    
    def multivariate_climate_modeling(self, climate_vars: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Perform multivariate climate modeling using copulas and ARIMA
        
        Args:
            climate_vars: Dictionary with climate variable names as keys and time series as values
            
        Returns:
            Dictionary with multivariate model results
        """
        if len(climate_vars) < 2:
            raise ValueError("Need at least 2 variables for multivariate modeling")
        
        var_names = list(climate_vars.keys())
        series_list = list(climate_vars.values())
        
        # Verify all series have same length
        n = len(series_list[0])
        for series in series_list[1:]:
            if len(series) != n:
                raise ValueError("All climate variable series must have same length")
        
        results = {
            'variables': var_names,
            'n_observations': n,
            'univariate_models': {},
            'dependence_structure': {},
            'simulation_results': {}
        }
        
        # Fit ARIMA models for each variable
        for i, var_name in enumerate(var_names):
            try:
                arima_params = self.fit_arima_model(series_list[i])
                results['univariate_models'][var_name] = {
                    'arima_params': {
                        'p': arima_params.p,
                        'd': arima_params.d,
                        'q': arima_params.q,
                        'aic': arima_params.aic,
                        'bic': arima_params.bic
                    }
                }
            except Exception as e:
                logger.warning(f"Failed to fit ARIMA for {var_name}: {str(e)}")
                results['univariate_models'][var_name] = {'error': str(e)}
        
        # Calculate pairwise copula dependencies
        for i, var1 in enumerate(var_names):
            for j, var2 in enumerate(var_names):
                if i < j:  # Only compute each pair once
                    try:
                        copula_params = self.fit_copula_model(
                            series_list[i], series_list[j], copula_type='gaussian'
                        )
                        pair_key = f"{var1}_vs_{var2}"
                        results['dependence_structure'][pair_key] = {
                            'copula_params': {
                                'type': copula_params.type,
                                'parameter': copula_params.parameter,
                                'kendall_tau': copula_params.kendall_tau
                            }
                        }
                    except Exception as e:
                        logger.warning(f"Failed to calculate copula for {var1} vs {var2}: {str(e)}")
        
        # Generate simulation results for risk assessment
        try:
            # Use the first two variables for copula simulation as example
            if len(var_names) >= 2:
                copula_params = self.fit_copula_model(
                    series_list[0], series_list[1], copula_type='gaussian'
                )
                u1, u2 = self.generate_copula_samples(copula_params, min(100, n))
                
                # Transform back to original scale using empirical quantiles
                var1_sorted = np.sort(series_list[0])
                var2_sorted = np.sort(series_list[1])
                
                sim_var1 = [var1_sorted[int(u * len(var1_sorted))] for u in u1]
                sim_var2 = [var2_sorted[int(u * len(var2_sorted))] for u in u2]
                
                results['simulation_results'] = {
                    'n_simulations': len(sim_var1),
                    f'simulated_{var_names[0]}': sim_var1,
                    f'simulated_{var_names[1]}': sim_var2
                }
        except Exception as e:
            logger.warning(f"Failed to generate simulation results: {str(e)}")
            results['simulation_results']['error'] = str(e)
        
        return results

# Global instance
stochastic_process_service = StochasticProcessService()

# Convenience functions for API integration
def fit_arima_model(time_series: List[float], max_p: int = 5, 
                   max_d: int = 2, max_q: int = 5) -> ARIMAModelParams:
    """Fit ARIMA model using AIC/BIC criteria for order selection"""
    return stochastic_process_service.fit_arima_model(
        time_series, max_p, max_d, max_q
    )

def forecast_arima(time_series: List[float], steps: int, 
                  arima_params: ARIMAModelParams) -> List[float]:
    """Generate forecasts using fitted ARIMA model"""
    return stochastic_process_service.forecast_arima(
        time_series, steps, arima_params
    )

def fit_copula_model(data1: List[float], data2: List[float], 
                    copula_type: str = 'gaussian') -> CopulaParams:
    """Fit copula model to capture dependence structure between two variables"""
    return stochastic_process_service.fit_copula_model(
        data1, data2, copula_type
    )

def regime_switching_model(time_series: List[float], n_states: int = 2) -> Dict[str, Any]:
    """Fit a simple regime-switching model to identify climate states"""
    return stochastic_process_service.regime_switching_model(
        time_series, n_states
    )

def multivariate_climate_modeling(climate_vars: Dict[str, List[float]]) -> Dict[str, Any]:
    """Perform multivariate climate modeling using copulas and ARIMA"""
    return stochastic_process_service.multivariate_climate_modeling(
        climate_vars
    )
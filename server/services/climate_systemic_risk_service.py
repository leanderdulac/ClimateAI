"""
Climate Systemic Risk Service with Conditional Value at Risk (CoVaR)
Implements Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark) 
where CoVaR = VaR of portfolio conditional on extreme climate event
and Benchmark = hypothetical climate-neutral portfolio
"""
import numpy as np
from scipy.stats import norm, gumbel_r
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClimateCoVaRResult:
    """Result of climate CoVaR calculation"""
    covar_portfolio: float
    covar_benchmark: float
    loading_climate: float
    portfolio_vat: float
    benchmark_vat: float
    climate_scenario: str
    confidence_level: float

class ClimateSystemicRiskService:
    """
    Service implementing Climate Value at Risk (CoVaR) for systemic climate risk assessment
    Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark)
    where CoVaR = VaR of portfolio conditional on extreme climate event
    and Benchmark = hypothetical climate-neutral portfolio
    """
    
    def __init__(self):
        self.extreme_event_thresholds = {
            'temperature': 35.0,  # °C extreme heat threshold
            'precipitation': 100.0,  # mm/day extreme precipitation threshold
            'wind': 25.0,  # m/s extreme wind threshold
            'drought': 0.0  # SPI threshold for drought
        }
        self.portfolio_weights = {}
        self.asset_betas = {}  # Climate sensitivity betas for different assets
    
    def calculate_extreme_climate_event_probability(self, 
                                                   climate_data: Dict[str, List[float]],
                                                   event_type: str = 'compound') -> float:
        """
        Calculate probability of extreme climate events
        
        Args:
            climate_data: Dictionary of climate variables {var_name: [time_series]}
            event_type: Type of extreme event ('temperature', 'precipitation', 'wind', 'drought', 'compound')
            
        Returns:
            Probability of extreme climate event
        """
        if event_type == 'compound':
            # Combined probability of multiple extreme events
            probs = []
            for var, values in climate_data.items():
                if var in self.extreme_event_thresholds:
                    threshold = self.extreme_event_thresholds[var]
                    # Count extreme events above threshold
                    extreme_count = sum(1 for val in values if val > threshold)
                    prob = extreme_count / len(values) if values else 0.0
                    probs.append(prob)
            
            # Assume independence and calculate compound probability
            if probs:
                # Use intersection of probabilities (conservative estimate)
                compound_prob = min(probs) if probs else 0.0
            else:
                compound_prob = 0.0
        else:
            # Single variable extreme event probability
            if event_type not in climate_data:
                raise ValueError(f"Climate variable '{event_type}' not found in data")
            
            values = climate_data[event_type]
            threshold = self.extreme_event_thresholds.get(event_type, 0.0)
            extreme_count = sum(1 for val in values if val > threshold)
            compound_prob = extreme_count / len(values) if values else 0.0
        
        return min(1.0, max(0.0, compound_prob))
    
    def calculate_portfolio_vaR(self, 
                               portfolio_returns: List[float],
                               confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk for a portfolio
        
        Args:
            portfolio_returns: Portfolio returns time series
            confidence_level: Confidence level for VaR calculation
            
        Returns:
            Value at Risk at specified confidence level
        """
        if not portfolio_returns:
            return 0.0
        
        # Calculate VaR using historical method (quantile)
        var_percentile = 100 * (1 - confidence_level)
        var_value = np.percentile(portfolio_returns, var_percentile)
        
        # Alternative: parametric method assuming normal distribution
        mean_return = np.mean(portfolio_returns)
        std_return = np.std(portfolio_returns)
        z_score = norm.ppf(1 - confidence_level)
        var_parametric = mean_return - z_score * std_return
        
        # Use the more conservative estimate
        return max(var_value, var_parametric)
    
    def calculate_conditional_var(self,
                                portfolio_returns: List[float],
                                climate_data: Dict[str, List[float]],
                                event_type: str = 'compound',
                                confidence_level: float = 0.95,
                                n_bootstrap: int = 1000) -> float:
        """
        Calculate Conditional Value at Risk (CoVaR) of portfolio
        conditional on extreme climate event
        
        Args:
            portfolio_returns: Portfolio returns time series
            climate_data: Climate variables {var_name: [time_series]}
            event_type: Type of extreme event
            confidence_level: Confidence level for CoVaR calculation
            n_bootstrap: Number of bootstrap samples for estimation
            
        Returns:
            Conditional Value at Risk (CoVaR)
        """
        if len(portfolio_returns) != len(list(climate_data.values())[0]) if climate_data else 0:
            raise ValueError("Portfolio returns and climate data must have same length")
        
        # Identify periods with extreme climate events
        extreme_prob = self.calculate_extreme_climate_event_probability(climate_data, event_type)
        
        if extreme_prob == 0:
            # If no extreme events observed, use simulation
            # For demonstration, we'll simulate extreme conditions
            n_extreme_periods = max(1, int(len(portfolio_returns) * 0.1))  # Assume 10% extreme periods
            # Select worst performing periods as proxy for extreme climate conditions
            sorted_indices = np.argsort(portfolio_returns)
            extreme_indices = sorted_indices[:n_extreme_periods]
        else:
            # Find actual periods with extreme climate events
            extreme_indices = []
            for i in range(len(portfolio_returns)):
                is_extreme = False
                for var, values in climate_data.items():
                    if var in self.extreme_event_thresholds and i < len(values):
                        threshold = self.extreme_event_thresholds[var]
                        if values[i] > threshold:
                            is_extreme = True
                            break
                if is_extreme:
                    extreme_indices.append(i)
        
        if not extreme_indices:
            # If no extreme periods identified, return regular VaR
            return self.calculate_portfolio_vaR(portfolio_returns, confidence_level)
        
        # Calculate CoVaR using the extreme periods
        extreme_returns = [portfolio_returns[i] for i in extreme_indices]
        
        # Use bootstrap to improve estimation
        covar_estimates = []
        for _ in range(n_bootstrap):
            # Sample with replacement from extreme periods
            boot_sample = np.random.choice(extreme_returns, size=len(extreme_returns), replace=True)
            boot_var = self.calculate_portfolio_vaR(boot_sample.tolist(), confidence_level)
            covar_estimates.append(boot_var)
        
        # Return average CoVaR from bootstrap samples
        return np.mean(covar_estimates)
    
    def calculate_climate_neutral_benchmark(self,
                                          n_assets: int = 10,
                                          time_horizon: int = 252,  # Trading days in a year
                                          volatility_target: float = 0.15) -> List[float]:
        """
        Generate hypothetical climate-neutral portfolio returns
        
        Args:
            n_assets: Number of assets in benchmark
            time_horizon: Time horizon in days
            volatility_target: Target annual volatility
            
        Returns:
            Hypothetical climate-neutral portfolio returns
        """
        # Generate benchmark portfolio returns with:
        # - Low climate sensitivity (neutral to climate events)
        # - Target volatility
        # - Reasonable expected return
        
        # Daily volatility (annualized to daily: vol / sqrt(252))
        daily_vol = volatility_target / np.sqrt(252)
        
        # Generate normally distributed returns
        benchmark_returns = np.random.normal(
            loc=0.0005,  # Small positive drift (about 13% annualized)
            scale=daily_vol,
            size=time_horizon
        ).tolist()
        
        # Adjust to be climate-neutral (no systematic correlation with climate extremes)
        return benchmark_returns
    
    def calculate_climate_loading(self,
                                 portfolio_returns: List[float],
                                 climate_data: Dict[str, List[float]],
                                 confidence_level: float = 0.95,
                                 event_type: str = 'compound') -> ClimateCoVaRResult:
        """
        Calculate climate loading: Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark)
        
        Args:
            portfolio_returns: Portfolio returns time series
            climate_data: Climate variables {var_name: [time_series]}
            confidence_level: Confidence level for VaR/CoVaR calculation
            event_type: Type of extreme climate event to condition on
            
        Returns:
            ClimateCoVaRResult with all calculated values
        """
        # Calculate conditional VaR for the actual portfolio
        covar_portfolio = self.calculate_conditional_var(
            portfolio_returns, climate_data, event_type, confidence_level
        )
        
        # Generate climate-neutral benchmark
        benchmark_returns = self.calculate_climate_neutral_benchmark(
            time_horizon=len(portfolio_returns)
        )
        
        # Calculate conditional VaR for the benchmark portfolio
        # (using the same climate conditioning)
        covar_benchmark = self.calculate_conditional_var(
            benchmark_returns, climate_data, event_type, confidence_level
        )
        
        # Calculate climate loading
        loading_climate = max(0, covar_portfolio - covar_benchmark)
        
        # Also calculate unconditional VaRs for comparison
        portfolio_vat = self.calculate_portfolio_vaR(portfolio_returns, confidence_level)
        benchmark_vat = self.calculate_portfolio_vaR(benchmark_returns, confidence_level)
        
        return ClimateCoVaRResult(
            covar_portfolio=covar_portfolio,
            covar_benchmark=covar_benchmark,
            loading_climate=loading_climate,
            portfolio_vat=portfolio_vat,
            benchmark_vat=benchmark_vat,
            climate_scenario=event_type,
            confidence_level=confidence_level
        )
    
    def calculate_systemic_climate_risk(self,
                                      portfolios_data: Dict[str, List[float]],  # Multiple portfolios
                                      climate_data: Dict[str, List[float]],
                                      confidence_levels: List[float] = [0.95, 0.99],
                                      event_types: List[str] = ['compound', 'temperature', 'precipitation']) -> Dict[str, Any]:
        """
        Calculate systemic climate risk across multiple portfolios
        
        Args:
            portfolios_data: Dictionary of portfolios {portfolio_name: [returns]}
            climate_data: Climate variables {var_name: [time_series]}
            confidence_levels: List of confidence levels to calculate
            event_types: List of extreme event types to analyze
            
        Returns:
            Dictionary with systemic climate risk analysis
        """
        results = {
            'climate_event_probabilities': {},
            'portfolio_analysis': {},
            'systemic_metrics': {},
            'climate_loading_matrix': [],
            'overall_systemic_risk': 0.0
        }
        
        # Calculate climate event probabilities
        for event_type in event_types:
            prob = self.calculate_extreme_climate_event_probability(climate_data, event_type)
            results['climate_event_probabilities'][event_type] = prob
        
        # Calculate risk metrics for each portfolio
        portfolio_loadings = {}
        for portfolio_name, returns in portfolios_data.items():
            portfolio_results = {}
            
            for conf_level in confidence_levels:
                for event_type in event_types:
                    result = self.calculate_climate_loading(
                        returns, climate_data, conf_level, event_type
                    )
                    
                    key = f"conf_{conf_level}_event_{event_type}"
                    portfolio_results[key] = {
                        'covar_portfolio': result.covar_portfolio,
                        'covar_benchmark': result.covar_benchmark,
                        'loading_climate': result.loading_climate,
                        'portfolio_vat': result.portfolio_vat,
                        'benchmark_vat': result.benchmark_vat
                    }
            
            results['portfolio_analysis'][portfolio_name] = portfolio_results
            # Calculate average loading across scenarios for this portfolio
            avg_loadings = []
            for key, values in portfolio_results.items():
                avg_loadings.append(values['loading_climate'])
            portfolio_loadings[portfolio_name] = np.mean(avg_loadings) if avg_loadings else 0.0
        
        # Calculate systemic metrics
        results['systemic_metrics'] = {
            'portfolio_climate_loadings': portfolio_loadings,
            'max_portfolio_loading': max(portfolio_loadings.values()) if portfolio_loadings else 0.0,
            'avg_portfolio_loading': np.mean(list(portfolio_loadings.values())) if portfolio_loadings else 0.0,
            'total_systemic_exposure': sum(portfolio_loadings.values()) if portfolio_loadings else 0.0
        }
        
        # Create loading matrix
        for portfolio_name, loading in portfolio_loadings.items():
            results['climate_loading_matrix'].append({
                'portfolio': portfolio_name,
                'climate_loading': loading
            })
        
        # Overall systemic risk as the maximum loading across portfolios
        results['overall_systemic_risk'] = results['systemic_metrics']['max_portfolio_loading']
        
        return results

# Global instance
climate_systemic_risk_service = ClimateSystemicRiskService()

# Convenience functions for API integration
def calculate_extreme_climate_event_probability(climate_data: Dict[str, List[float]], 
                                             event_type: str = 'compound') -> float:
    """Calculate probability of extreme climate events"""
    return climate_systemic_risk_service.calculate_extreme_climate_event_probability(
        climate_data, event_type
    )

def calculate_portfolio_var(portfolio_returns: List[float],
                          confidence_level: float = 0.95) -> float:
    """Calculate Value at Risk for a portfolio"""
    return climate_systemic_risk_service.calculate_portfolio_var(
        portfolio_returns, confidence_level
    )

def calculate_conditional_var(portfolio_returns: List[float],
                            climate_data: Dict[str, List[float]],
                            event_type: str = 'compound',
                            confidence_level: float = 0.95) -> float:
    """Calculate Conditional Value at Risk (CoVaR) of portfolio conditional on extreme climate event"""
    return climate_systemic_risk_service.calculate_conditional_var(
        portfolio_returns, climate_data, event_type, confidence_level
    )

def calculate_climate_neutral_benchmark(n_assets: int = 10,
                                      time_horizon: int = 252,
                                      volatility_target: float = 0.15) -> List[float]:
    """Generate hypothetical climate-neutral portfolio returns"""
    return climate_systemic_risk_service.calculate_climate_neutral_benchmark(
        n_assets, time_horizon, volatility_target
    )

def calculate_climate_loading(portfolio_returns: List[float],
                            climate_data: Dict[str, List[float]],
                            confidence_level: float = 0.95,
                            event_type: str = 'compound') -> ClimateCoVaRResult:
    """Calculate climate loading: Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark)"""
    return climate_systemic_risk_service.calculate_climate_loading(
        portfolio_returns, climate_data, confidence_level, event_type
    )

def calculate_systemic_climate_risk(portfolios_data: Dict[str, List[float]],
                                  climate_data: Dict[str, List[float]],
                                  confidence_levels: List[float] = [0.95, 0.99],
                                  event_types: List[str] = ['compound', 'temperature', 'precipitation']) -> Dict[str, Any]:
    """Calculate systemic climate risk across multiple portfolios"""
    return climate_systemic_risk_service.calculate_systemic_climate_risk(
        portfolios_data, climate_data, confidence_levels, event_types
    )
"""
Bayesian Bootstrap Premium Calculation Service
Implements uncertainty quantification via Bayesian bootstrap:
- Parameter sampling from posterior
- Monte Carlo simulation of 10,000 scenarios
- VaR and CVaR calculation by contract
- Premium percentile calculation: Prêmio = R$ 1.200 ± [R$ 900 (P10) - R$ 2.100 (P90)]
"""
import numpy as np
from scipy import stats
from scipy.stats import beta, gamma, lognorm
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class BayesianBootstrapResult:
    """Result of Bayesian bootstrap premium calculation"""
    mean_premium: float
    p10: float
    p90: float
    lower_bound: float
    upper_bound: float
    n_scenarios: int
    vaar: float
    cvar: float
    contract_id: str
    scenario_results: List[float]

class BayesianBootstrapService:
    """
    Service implementing Bayesian bootstrap for premium uncertainty quantification
    - Parameter sampling from posterior
    - Monte Carlo simulation of 10,000 scenarios  
    - VaR and CVaR calculation by contract
    - Premium percentiles: Prêmio = R$ 1.200 ± [R$ 900 (P10) - R$ 2.100 (P90)]
    """
    
    def __init__(self):
        self.n_scenarios = 10000  # Default number of Monte Carlo scenarios
        
    def sample_posterior_parameters(self, 
                                  data: List[float],
                                  prior_alpha: float = 2.0,
                                  prior_beta: float = 2.0) -> Dict[str, Any]:
        """
        Sample parameters from posterior distribution using conjugate priors
        
        Args:
            data: Historical or observed data for the contract
            prior_alpha: Alpha parameter for Beta prior (default 2.0)
            prior_beta: Beta parameter for Beta prior (default 2.0)
            
        Returns:
            Dictionary with sampled posterior parameters
        """
        if not data:
            # Default values if no data provided
            return {
                'mean_rate': np.random.normal(1.0, 0.2),
                'variance': np.random.gamma(2.0, 2.0),
                'shape': np.random.gamma(2.0, 1.0),
                'scale': np.random.gamma(1.0, 2.0)
            }
        
        # Convert data to numpy array for calculations
        data_array = np.array(data)
        n_obs = len(data_array)
        
        # Sample from posterior for key parameters
        # For simplicity, using a normal-gamma conjugate prior setup
        sample_mean = np.mean(data_array) if len(data_array) > 0 else 1.0
        sample_var = np.var(data_array) if len(data_array) > 1 else 1.0
        
        # Posterior hyperparameters (simplified normal-gamma model)
        post_mean_precision = n_obs + prior_alpha
        post_mean = (n_obs * sample_mean + prior_alpha * 0.0) / post_mean_precision
        
        # Sample precision (inverse variance) from Gamma posterior
        post_precision_alpha = prior_alpha + n_obs / 2.0
        post_precision_beta = prior_beta + 0.5 * np.sum((data_array - sample_mean)**2) + \
                              (n_obs * prior_alpha) / (n_obs + prior_alpha) * \
                              (sample_mean - 0.0)**2 / 2.0
        
        # Sample from posterior
        precision = np.random.gamma(post_precision_alpha, 1.0 / post_precision_beta)
        sampled_mean = np.random.normal(post_mean, 1.0 / np.sqrt(post_mean_precision * precision))
        
        # Sample other parameters
        sampled_variance = 1.0 / precision if precision > 0 else sample_var
        sampled_shape = max(0.1, np.random.gamma(2.0, 1.0))  # Shape parameter for lognormal
        sampled_scale = max(0.01, np.random.gamma(1.0, 2.0))  # Scale parameter
        
        return {
            'mean_rate': sampled_mean,
            'variance': sampled_variance,
            'shape': sampled_shape,
            'scale': sampled_scale
        }
    
    def monte_carlo_simulation(self, 
                             n_scenarios: int,
                             param_samples: Dict[str, Any],
                             base_premium: float,
                             contract_exposure: float) -> List[float]:
        """
        Run Monte Carlo simulation for premium estimation
        
        Args:
            n_scenarios: Number of simulation scenarios
            param_samples: Parameters sampled from posterior
            base_premium: Base premium to start with
            contract_exposure: Contract exposure amount
            
        Returns:
            List of simulated premium values
        """
        premiums = []
        
        for _ in range(n_scenarios):
            # Simulate premium based on posterior parameters
            # Adding some randomness based on uncertainty
            parameter_factor = np.random.normal(
                param_samples['mean_rate'], 
                np.sqrt(param_samples['variance'])
            )
            
            # Apply lognormal simulation for multiplicative uncertainty
            uncertainty_factor = np.random.lognormal(
                mean=0.0, 
                sigma=max(0.01, param_samples['shape'] * 0.1)
            )
            
            # Calculate premium incorporating exposure and parameter uncertainty
            simulated_premium = base_premium * parameter_factor * uncertainty_factor
            
            # Ensure premium is positive
            simulated_premium = max(0.0, simulated_premium)
            
            premiums.append(simulated_premium)
        
        return premiums
    
    def calculate_percentiles(self, 
                            scenario_results: List[float],
                            percentiles: List[float] = [10, 50, 90]) -> Dict[float, float]:
        """
        Calculate percentiles from Monte Carlo results
        
        Args:
            scenario_results: List of simulated premium values
            percentiles: List of percentiles to calculate (default [10, 50, 90])
            
        Returns:
            Dictionary mapping percentiles to their values
        """
        if not scenario_results:
            return {p: 0.0 for p in percentiles}
        
        result_dict = {}
        for p in percentiles:
            result_dict[p] = np.percentile(scenario_results, p)
        
        return result_dict
    
    def calculate_value_at_risk(self, 
                               scenario_results: List[float],
                               confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) for the contract
        
        Args:
            scenario_results: List of simulated premium values
            confidence_level: Confidence level for VaR calculation
            
        Returns:
            Value at Risk at specified confidence level
        """
        if not scenario_results:
            return 0.0
        
        var_percentile = confidence_level * 100
        var_value = np.percentile(scenario_results, var_percentile)
        
        return var_value
    
    def calculate_conditional_value_at_risk(self,
                                          scenario_results: List[float],
                                          confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) for the contract
        
        Args:
            scenario_results: List of simulated premium values
            confidence_level: Confidence level for CVaR calculation
            
        Returns:
            Conditional Value at Risk at specified confidence level
        """
        if not scenario_results:
            return 0.0
        
        var_threshold = self.calculate_value_at_risk(scenario_results, confidence_level)
        
        # Get all values above the VaR threshold (the "tail risk")
        threshold_idx = int(len(scenario_results) * (1 - confidence_level))
        sorted_results = np.sort(scenario_results)
        cvar_values = sorted_results[-threshold_idx:] if threshold_idx > 0 else sorted_results
        
        # Calculate CVaR as the mean of the tail values
        cvar_value = np.mean(cvar_values) if len(cvar_values) > 0 else var_threshold
        
        return cvar_value
    
    def bayesian_bootstrap_premium(self,
                                 contract_data: List[float],
                                 base_premium: float,
                                 contract_exposure: float,
                                 n_scenarios: int = 10000,
                                 confidence_level: float = 0.95,
                                 contract_id: str = "default_contract") -> BayesianBootstrapResult:
        """
        Complete Bayesian bootstrap premium calculation:
        Prêmio = R$ 1.200 ± [R$ 900 (P10) - R$ 2.100 (P90)]
        - Parameter sampling from posterior
        - Monte Carlo simulation of N scenarios
        - VaR and CVaR calculation
        - Percentile calculation
        
        Args:
            contract_data: Historical data for the specific contract
            base_premium: Base premium estimate
            contract_exposure: Exposure amount for the contract
            n_scenarios: Number of Monte Carlo scenarios (default 10,000)
            confidence_level: Confidence level for VaR/CVaR calculation
            contract_id: Unique identifier for the contract
            
        Returns:
            BayesianBootstrapResult with complete uncertainty analysis
        """
        # Sample parameters from posterior
        param_samples = self.sample_posterior_parameters(contract_data)
        
        # Run Monte Carlo simulation
        scenario_results = self.monte_carlo_simulation(
            n_scenarios, param_samples, base_premium, contract_exposure
        )
        
        # Calculate percentiles
        percentiles = self.calculate_percentiles(scenario_results, [10, 50, 90])
        
        # Calculate VaR and CVaR
        var_value = self.calculate_value_at_risk(scenario_results, confidence_level)
        cvar_value = self.calculate_conditional_value_at_risk(scenario_results, confidence_level)
        
        # Return results
        return BayesianBootstrapResult(
            mean_premium=np.mean(scenario_results),
            p10=percentiles[10],
            p90=percentiles[90],
            lower_bound=min(scenario_results),
            upper_bound=max(scenario_results),
            n_scenarios=n_scenarios,
            vaar=var_value,
            cvar=cvar_value,
            contract_id=contract_id,
            scenario_results=scenario_results
        )
    
    def calculate_contract_uncertainty_ranges(self,
                                           contracts_data: Dict[str, Dict[str, Any]]) -> Dict[str, BayesianBootstrapResult]:
        """
        Calculate uncertainty ranges for multiple contracts
        
        Args:
            contracts_data: Dictionary with contract information
            Format: {contract_id: {'data': [history], 'base_premium': float, 'exposure': float}}
            
        Returns:
            Dictionary mapping contract IDs to their Bayesian bootstrap results
        """
        results = {}
        
        for contract_id, contract_info in contracts_data.items():
            data = contract_info.get('data', [])
            base_premium = contract_info.get('base_premium', 1000.0)
            exposure = contract_info.get('exposure', 100000.0)
            n_scenarios = contract_info.get('n_scenarios', 10000)
            
            result = self.bayesian_bootstrap_premium(
                data, base_premium, exposure, n_scenarios, 
                contract_info.get('confidence_level', 0.95), contract_id
            )
            
            results[contract_id] = result
        
        return results

# Global instance
bayesian_bootstrap_service = BayesianBootstrapService()

# Convenience functions for API integration
def sample_posterior_parameters(data: List[float],
                              prior_alpha: float = 2.0,
                              prior_beta: float = 2.0) -> Dict[str, Any]:
    """Sample parameters from posterior distribution using conjugate priors"""
    return bayesian_bootstrap_service.sample_posterior_parameters(
        data, prior_alpha, prior_beta
    )

def monte_carlo_simulation(n_scenarios: int,
                         param_samples: Dict[str, Any],
                         base_premium: float,
                         contract_exposure: float) -> List[float]:
    """Run Monte Carlo simulation for premium estimation"""
    return bayesian_bootstrap_service.monte_carlo_simulation(
        n_scenarios, param_samples, base_premium, contract_exposure
    )

def calculate_percentiles(scenario_results: List[float],
                        percentiles: List[float] = [10, 50, 90]) -> Dict[float, float]:
    """Calculate percentiles from Monte Carlo results"""
    return bayesian_bootstrap_service.calculate_percentiles(scenario_results, percentiles)

def calculate_value_at_risk(scenario_results: List[float],
                           confidence_level: float = 0.95) -> float:
    """Calculate Value at Risk (VaR) for the contract"""
    return bayesian_bootstrap_service.calculate_value_at_risk(scenario_results, confidence_level)

def calculate_conditional_value_at_risk(scenario_results: List[float],
                                       confidence_level: float = 0.95) -> float:
    """Calculate Conditional Value at Risk (CVaR) for the contract"""
    return bayesian_bootstrap_service.calculate_conditional_value_at_risk(
        scenario_results, confidence_level
    )

def bayesian_bootstrap_premium(contract_data: List[float],
                              base_premium: float,
                              contract_exposure: float,
                              n_scenarios: int = 10000,
                              confidence_level: float = 0.95,
                              contract_id: str = "default_contract") -> BayesianBootstrapResult:
    """Complete Bayesian bootstrap premium calculation"""
    return bayesian_bootstrap_service.bayesian_bootstrap_premium(
        contract_data, base_premium, contract_exposure, n_scenarios,
        confidence_level, contract_id
    )

def calculate_contract_uncertainty_ranges(contracts_data: Dict[str, Dict[str, Any]]) -> Dict[str, BayesianBootstrapResult]:
    """Calculate uncertainty ranges for multiple contracts"""
    return bayesian_bootstrap_service.calculate_contract_uncertainty_ranges(contracts_data)
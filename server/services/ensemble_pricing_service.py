"""
Ensemble Pricing Service with Dynamic Model Weights
Implements: Prêmio_final = Σ_m w_m · Prêmio_m + z_α · VaR_ensemble
Where w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m and π_m ~ Dirichlet(α)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import dirichlet, norm

logger = logging.getLogger(__name__)


@dataclass
class EnsemblePricingResult:
    """Result of ensemble pricing calculation"""

    final_premium: float
    model_premiums: List[float]
    model_weights: List[float]
    model_bics: List[float]
    var_ensemble: float
    uncertainty_quantile: float
    ensemble_method: str


class EnsemblePricingService:
    """
    Service implementing ensemble pricing with dynamic model weights based on BIC and Dirichlet priors
    Prêmio_final = Σ_m w_m · Prêmio_m + z_α · VaR_ensemble
    Where w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m and π_m ~ Dirichlet(α)
    """

    def __init__(self):
        self.model_performance_history = {}  # Track BIC values over time
        self.dirichlet_alpha = None  # Prior parameters for Dirichlet distribution
        self.uncertainty_factor = 1.0  # Scaling factor for ensemble uncertainty
        self.bic_sensitivity = 1.0  # η parameter controlling BIC influence

    def calculate_bic(
        self, log_likelihood: float, n_params: int, n_observations: int
    ) -> float:
        """
        Calculate Bayesian Information Criterion (BIC)

        Args:
            log_likelihood: Log-likelihood of the model
            n_params: Number of model parameters
            n_observations: Number of observations

        Returns:
            BIC value
        """
        if n_observations <= 0:
            return float("inf")

        bic = -2 * log_likelihood + n_params * np.log(n_observations)
        return bic

    def calculate_dynamic_weights(
        self,
        bics: List[float],
        n_models: int,
        prior_alpha: Optional[List[float]] = None,
    ) -> List[float]:
        """
        Calculate dynamic model weights based on BIC and Dirichlet prior:
        w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m where π_m ~ Dirichlet(α)

        Args:
            bics: List of BIC values for each model
            n_models: Number of models
            prior_alpha: Prior parameters for Dirichlet distribution α

        Returns:
            Normalized weights for each model
        """
        if not prior_alpha:
            # Default uniform prior
            prior_alpha = [1.0] * n_models

        if len(prior_alpha) != n_models:
            raise ValueError(
                f"Prior alpha length ({len(prior_alpha)}) must match number of models ({n_models})"
            )

        # Calculate base weights from BIC: exp(-η·BIC_m(t-1))
        base_weights = []
        min_bic = min(bics) if bics else 0
        for bic in bics:
            # Use relative BIC (difference from best model) to avoid numerical issues
            relative_bic = bic - min_bic
            weight = np.exp(-self.bic_sensitivity * relative_bic)
            base_weights.append(weight)

        # Sample from Dirichlet distribution for prior weights
        # In practice, we use the mean of Dirichlet which is α_i / sum(α)
        dirichlet_means = [a / sum(prior_alpha) for a in prior_alpha]

        # Combine BIC-based weights with Dirichlet prior
        combined_weights = [b * d for b, d in zip(base_weights, dirichlet_means)]

        # Normalize weights
        total_weight = sum(combined_weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight for w in combined_weights]
        else:
            # Fallback to uniform weights if all weights are zero
            normalized_weights = [1.0 / n_models] * n_models

        return normalized_weights

    def calculate_ensemble_var(
        self,
        model_premiums: List[float],
        model_weights: List[float],
        confidence_level: float = 0.95,
    ) -> float:
        """
        Calculate Value at Risk of the ensemble

        Args:
            model_premiums: Premiums from individual models
            model_weights: Weights for each model
            confidence_level: Confidence level for VaR calculation

        Returns:
            Ensemble Value at Risk
        """
        # Calculate weighted mean (ensemble premium)
        ensemble_mean = sum(w * p for w, p in zip(model_weights, model_premiums))

        # Calculate weighted variance
        if len(model_premiums) > 1:
            # For simplicity, assuming models are uncorrelated
            # In practice, you'd want to consider model correlations
            variance = sum(
                w**2 * (p - ensemble_mean) ** 2
                for w, p in zip(model_weights, model_premiums)
            )
            std_dev = np.sqrt(variance)
        else:
            std_dev = 0.0

        # Calculate VaR based on confidence level
        z_alpha = norm.ppf(confidence_level)
        var_ensemble = z_alpha * std_dev

        return var_ensemble

    def calculate_quantile_uncertainty(self, confidence_level: float = 0.95) -> float:
        """
        Calculate uncertainty quantile z_α from total uncertainty distribution

        Args:
            confidence_level: Confidence level for the quantile

        Returns:
            Quantile value z_α
        """
        return norm.ppf(confidence_level)

    def calculate_ensemble_pricing(
        self,
        model_premiums: List[float],
        model_log_likelihoods: List[float],
        model_n_params: List[int],
        model_n_observations: List[int],
        n_models: int,
        confidence_level: float = 0.95,
        dirichlet_alpha: Optional[List[float]] = None,
        bic_sensitivity: float = 1.0,
        uncertainty_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Complete ensemble pricing calculation:
        Prêmio_final = Σ_m w_m · Prêmio_m + z_α · VaR_ensemble
        Where w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m and π_m ~ Dirichlet(α)

        Args:
            model_premiums: Premiums calculated by each individual model
            model_log_likelihoods: Log-likelihood values for each model
            model_n_params: Number of parameters for each model
            model_n_observations: Number of observations for each model
            n_models: Total number of models in ensemble
            confidence_level: Confidence level for VaR calculation
            dirichlet_alpha: Prior parameters for Dirichlet distribution
            bic_sensitivity: Sensitivity parameter η controlling BIC influence
            uncertainty_factor: Scaling factor for ensemble uncertainty

        Returns:
            Dictionary with complete ensemble pricing results
        """
        if not all(
            len(lst) == n_models
            for lst in [
                model_premiums,
                model_log_likelihoods,
                model_n_params,
                model_n_observations,
            ]
        ):
            raise ValueError("All input lists must have the same length as n_models")

        # Update class parameters
        self.bic_sensitivity = bic_sensitivity
        self.uncertainty_factor = uncertainty_factor

        # Calculate BIC for each model
        bics = []
        for ll, n_params, n_obs in zip(
            model_log_likelihoods, model_n_params, model_n_observations
        ):
            bic = self.calculate_bic(ll, n_params, n_obs)
            bics.append(bic)

        # Calculate dynamic weights
        weights = self.calculate_dynamic_weights(bics, n_models, dirichlet_alpha)

        # Calculate ensemble premium: Σ_m w_m · Prêmio_m
        weighted_premium = sum(w * p for w, p in zip(weights, model_premiums))

        # Calculate ensemble VaR
        var_ensemble = self.calculate_ensemble_var(
            model_premiums, weights, confidence_level
        )
        var_ensemble_scaled = var_ensemble * uncertainty_factor

        # Calculate uncertainty quantile z_α
        z_alpha = self.calculate_quantile_uncertainty(confidence_level)

        # Calculate final premium: Σ_m w_m · Prêmio_m + z_α · VaR_ensemble
        final_premium = weighted_premium + z_alpha * var_ensemble_scaled

        return {
            "final_premium": final_premium,
            "weighted_mean_premium": weighted_premium,
            "var_ensemble": var_ensemble_scaled,
            "uncertainty_addon": z_alpha * var_ensemble_scaled,
            "model_premiums": model_premiums,
            "model_weights": weights,
            "model_bics": bics,
            "model_log_likelihoods": model_log_likelihoods,
            "confidence_level": confidence_level,
            "z_alpha": z_alpha,
            "bic_sensitivity": bic_sensitivity,
            "uncertainty_factor": uncertainty_factor,
            "dirichlet_alpha": dirichlet_alpha or [1.0] * n_models,
            "n_models": n_models,
            "ensemble_method": "BIC-weighted with Dirichlet prior",
            "model_uncertainty": var_ensemble_scaled,
        }

    def update_model_performance(
        self, model_id: str, log_likelihood: float, n_params: int, n_observations: int
    ):
        """
        Update the performance history for a specific model

        Args:
            model_id: Unique identifier for the model
            log_likelihood: Log-likelihood of the model
            n_params: Number of parameters in the model
            n_observations: Number of observations used
        """
        bic = self.calculate_bic(log_likelihood, n_params, n_observations)

        if model_id not in self.model_performance_history:
            self.model_performance_history[model_id] = []

        self.model_performance_history[model_id].append(
            {
                "bic": bic,
                "log_likelihood": log_likelihood,
                "n_params": n_params,
                "n_observations": n_observations,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_historical_model_performance(self, model_id: str) -> List[Dict[str, Any]]:
        """
        Get historical performance for a specific model

        Args:
            model_id: Unique identifier for the model

        Returns:
            List of historical performance records
        """
        return self.model_performance_history.get(model_id, [])


# Global instance
ensemble_pricing_service = EnsemblePricingService()


# Convenience functions for API integration
def calculate_bic(log_likelihood: float, n_params: int, n_observations: int) -> float:
    """Calculate Bayesian Information Criterion (BIC)"""
    return ensemble_pricing_service.calculate_bic(
        log_likelihood, n_params, n_observations
    )


def calculate_dynamic_weights(
    bics: List[float], n_models: int, prior_alpha: Optional[List[float]] = None
) -> List[float]:
    """Calculate dynamic model weights: w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m"""
    return ensemble_pricing_service.calculate_dynamic_weights(
        bics, n_models, prior_alpha
    )


def calculate_ensemble_pricing(
    model_premiums: List[float],
    model_log_likelihoods: List[float],
    model_n_params: List[int],
    model_n_observations: List[int],
    n_models: int,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """Complete ensemble pricing calculation"""
    return ensemble_pricing_service.calculate_ensemble_pricing(
        model_premiums,
        model_log_likelihoods,
        model_n_params,
        model_n_observations,
        n_models,
        confidence_level,
    )


def update_model_performance(
    model_id: str, log_likelihood: float, n_params: int, n_observations: int
):
    """Update model performance history"""
    ensemble_pricing_service.update_model_performance(
        model_id, log_likelihood, n_params, n_observations
    )

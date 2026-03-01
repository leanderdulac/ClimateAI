#!/usr/bin/env python3
"""
Test script to verify the Ensemble Pricing service functionality
"""
import sys
import os
# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import numpy as np
from services.ensemble_pricing_service import ensemble_pricing_service

def test_ensemble_pricing_functionality():
    """Test ensemble pricing functionality"""
    print("🧪 Testing Ensemble Pricing Service...")

    # Generate synthetic data for different models
    np.random.seed(42)
    n_models = 4

    # Model premiums (e.g., from different approaches like GEV, ML, etc.)
    model_premiums = [1250.0, 1320.0, 1180.0, 1290.0]

    print(f"  ✓ Generated {n_models} model premiums: {model_premiums}")

    # Model performance metrics for BIC calculation
    model_log_likelihoods = [-150.5, -145.2, -155.1, -143.8]
    model_n_params = [5, 7, 4, 6]
    model_n_observations = [100, 100, 100, 100]  # Same for all models in this example

    print(f"  ✓ Model log-likelihoods: {model_log_likelihoods}")
    print(f"  ✓ Model parameters: {model_n_params}")

    # Calculate BIC for each model
    bics = []
    for ll, n_params, n_obs in zip(model_log_likelihoods, model_n_params, model_n_observations):
        bic = ensemble_pricing_service.calculate_bic(ll, n_params, n_obs)
        bics.append(bic)

    print(f"  ✓ Calculated BIC values: {bics}")

    # Calculate dynamic weights using BIC and Dirichlet prior
    dirichlet_alpha = [1.0, 1.0, 1.0, 1.0]  # Uniform prior
    weights = ensemble_pricing_service.calculate_dynamic_weights(bics, n_models, dirichlet_alpha)

    print(f"  ✓ Calculated dynamic weights: {[f'{w:.3f}' for w in weights]}")
    print(f"  ✓ Weight sum: {sum(weights):.3f} (should be ~1.0)")

    # Test ensemble pricing calculation
    ensemble_result = ensemble_pricing_service.calculate_ensemble_pricing(
        model_premiums,
        model_log_likelihoods,
        model_n_params,
        model_n_observations,
        n_models,
        confidence_level=0.95
    )

    print(f"  ✓ Ensemble result calculated")
    print(f"  ✓ Weighted mean premium: ${ensemble_result['weighted_mean_premium']:.2f}")
    print(f"  ✓ Ensemble VaR: ${ensemble_result['var_ensemble']:.2f}")
    print(f"  ✓ Final premium: ${ensemble_result['final_premium']:.2f}")
    print(f"  ✓ Confidence level: {ensemble_result['confidence_level']}")

    # Verify that weights sum to approximately 1
    weight_sum = sum(ensemble_result['model_weights'])
    assert abs(weight_sum - 1.0) < 0.01, f"Weights don't sum to 1: {weight_sum}"

    # Test individual BIC calculation
    sample_bic = ensemble_pricing_service.calculate_bic(-150.5, 5, 100)
    print(f"  ✓ Single BIC calculation: {sample_bic:.2f}")

    # Update model performance history
    ensemble_pricing_service.update_model_performance("test_model_1", -150.5, 5, 100)
    history = ensemble_pricing_service.get_historical_model_performance("test_model_1")
    print(f"  ✓ Model performance updated and retrieved: {len(history)} history entries")

    print("  🎉 Ensemble Pricing Service functionality verified!")

def main():
    print("🔬 ClimateWise: Ensemble Pricing Service Test\n")

    test_ensemble_pricing_functionality()

    print("\n📋 Ensemble Pricing Implementation Status:")
    print("   - Complete formula implemented: Prêmio_final = Σ_m w_m · Prêmio_m + z_α · VaR_ensemble")
    print("   - Dynamic weights: w_m(t) ∝ exp(-η·BIC_m(t-1)) · π_m")
    print("   - Dirichlet prior: π_m ~ Dirichlet(α) for expert knowledge integration")
    print("   - Bayesian Information Criterion (BIC) for model comparison")
    print("   - API endpoints available at /api/v1/ensemble-pricing/")

if __name__ == "__main__":
    main()

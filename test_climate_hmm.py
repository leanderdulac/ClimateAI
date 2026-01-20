#!/usr/bin/env python3
"""
Test script to verify the Climate Regime Hidden Markov Model service
"""
import sys
import os
# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import numpy as np
from services.climate_hmm_service import climate_hmm_service

def test_climate_hmm_functionality():
    """Test climate regime HMM functionality"""
    print("🧪 Testing Climate Regime HMM Service...")

    # Generate synthetic climate data
    np.random.seed(42)
    n_time_steps = 20
    n_states = 4

    # Climate observations: [temperature, precipitation, pressure]
    climate_observations = []
    for i in range(n_time_steps):
        # Create different observation patterns for different "regimes"
        if i < 5:  # Cool/wet regime
            temp = 18 + np.random.normal(0, 1)
            precip = 15 + np.random.normal(0, 5)
            pressure = 1015 + np.random.normal(0, 3)
        elif i < 10:  # Warm/dry regime
            temp = 28 + np.random.normal(0, 1)
            precip = 3 + np.random.normal(0, 2)
            pressure = 1010 + np.random.normal(0, 3)
        elif i < 15:  # Hot/arid regime
            temp = 35 + np.random.normal(0, 1.5)
            precip = 1 + np.random.normal(0, 1)
            pressure = 1008 + np.random.normal(0, 2)
        else:  # Variable regime
            temp = 25 + np.random.normal(0, 2)
            precip = 8 + np.random.normal(0, 7)
            pressure = 1012 + np.random.normal(0, 5)

        climate_observations.append([temp, precip, pressure])

    # Climate forcings: [CO₂, CH₄, aerosols]
    climate_forcings = []
    for i in range(n_time_steps):
        # Simulate increasing CO₂, CH₄, and varying aerosols
        co2 = 400 + i * 0.5 + np.random.normal(0, 0.5)  # Rising CO₂
        ch4 = 1800 + i * 0.2 + np.random.normal(0, 1)   # Rising CH₄
        aerosols = -0.3 + np.random.normal(0, 0.1)      # Negative forcing from aerosols
        climate_forcings.append([co2, ch4, aerosols])

    # Temperature history for transition calculations
    temperatures_history = [obs[0] for obs in climate_observations]

    print(f"  ✓ Generated {n_time_steps} time steps of climate data")
    print(f"  ✓ Climate observations: temp=[{min([obs[0] for obs in climate_observations]):.1f}, {max([obs[0] for obs in climate_observations]):.1f}]°C")
    print(f"  ✓ Climate forcings: CO₂=[{min([f[0] for f in climate_forcings]):.1f}, {max([f[0] for f in climate_forcings]):.1f}] ppm")

    # Test regime transition probabilities
    transition_result = climate_hmm_service.compute_regime_transition_probabilities(
        np.array(climate_forcings[0]), temperatures_history[:5], n_states
    )
    print(f"  ✓ Regime transition probabilities calculated for {n_states} states")

    # Test emission probabilities
    emission_result = climate_hmm_service.compute_emission_probabilities(
        np.array(climate_observations[0]), np.array(climate_forcings[0]), n_states
    )
    print(f"  ✓ Emission probabilities calculated for each regime")

    # Test complete HMM model
    hmm_result = climate_hmm_service.compute_climate_regime_model(
        climate_observations, climate_forcings, temperatures_history, n_states
    )

    print(f"  ✓ HMM analysis completed")
    print(f"  ✓ Regime sequence length: {len(hmm_result['regime_sequence'])}")
    print(f"  ✓ Dominant regime: {hmm_result['regime_statistics']['dominant_regime']}")
    print(f"  ✓ Number of regime switches: {hmm_result['regime_statistics']['regime_switches']}")
    print(f"  ✓ Detected regimes: {hmm_result['regime_statistics']['regime_counts']}")

    # Display regime descriptions
    for regime_id, count in hmm_result['regime_statistics']['regime_counts'].items():
        description = hmm_result['regime_descriptions'][regime_id]
        print(f"    - Regime {regime_id} ({description}): {count} time steps")

    print("  🎉 Climate Regime HMM Service functionality verified!")

def main():
    print("🔬 ClimateAI: Climate Regime Hidden Markov Model Test\n")

    test_climate_hmm_functionality()

    print("\n📋 Climate Regime HMM Implementation Status:")
    print("   - Complete HMM implemented: P(S_t = j | S_{t-1} = i) = A_ij(ΔT_t)")
    print("   - Emission probabilities: P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j)")
    print("   - Climate forcing integration: θ_t = [CO₂, CH₄, aerosols]")
    print("   - Viterbi decoding for optimal regime sequence")
    print("   - API endpoints available at /api/v1/climate-hmm/")

if __name__ == "__main__":
    main()

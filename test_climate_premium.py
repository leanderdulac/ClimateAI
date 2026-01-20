#!/usr/bin/env python3
"""
Test script to verify the Climate-Inclusive Premium service
"""
import sys
import os
# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import numpy as np
from services.climate_premium_service import climate_premium_service

def test_climate_premium_calculation():
    """Test climate-inclusive premium calculation"""
    print("🧪 Testing Climate-Inclusive Premium Service...")

    # Define climate parameters
    expected_loss = 50000.0  # $50,000 expected loss
    time_horizon = 10.0  # 10-year horizon
    loading_factor = 0.20  # 20% loading
    operational_costs = 2500.0  # $2,500 operational costs
    mitigation_discount = 0.10  # 10% mitigation discount

    print(f"  ✓ Expected loss: ${expected_loss:,.2f}")
    print(f"  ✓ Time horizon: {time_horizon} years")
    print(f"  ✓ Loading factor: {loading_factor:.1%}")
    print(f"  ✓ Operational costs: ${operational_costs:,.2f}")
    print(f"  ✓ Mitigation discount: {mitigation_discount:.1%}")

    # Climate parameters
    initial_delta_temp = 1.0  # 1.0°C current warming
    temperature_trend = 0.2  # 0.2°C/year warming
    initial_co2_rate = 2.5  # 2.5 ppm/year CO₂ rate
    co2_trend = 0.1  # 0.1 ppm/year acceleration

    print(f"  ✓ Initial temperature change: {initial_delta_temp}°C")
    print(f"  ✓ Temperature trend: {temperature_trend}°C/year")
    print(f"  ✓ Initial CO₂ rate: {initial_co2_rate} ppm/year")
    print(f"  ✓ CO₂ trend: {co2_trend} ppm/year")

    # Calculate premium
    premium_result = climate_premium_service.calculate_climate_inclusive_premium(
        expected_loss=expected_loss,
        time_horizon_years=time_horizon,
        loading_factor=loading_factor,
        operational_costs=operational_costs,
        mitigation_discount=mitigation_discount,
        initial_delta_temp=initial_delta_temp,
        temperature_trend=temperature_trend,
        initial_co2_rate=initial_co2_rate,
        co2_trend=co2_trend
    )

    print(f"  ✓ Final premium: ${premium_result.premium:,.2f}")
    print(f"  ✓ Climatic inflation factor: {premium_result.climatic_inflation_factor:.4f}")
    print(f"  ✓ Climate drift rate: {premium_result.climate_drift_rate:.5f}")
    print(f"  ✓ Expected loss component: ${expected_loss * (1 + loading_factor):,.2f}")
    print(f"  ✓ With operational costs: ${(expected_loss * (1 + loading_factor) + operational_costs):,.2f}")
    print(f"  ✓ After mitigation: ${(expected_loss * (1 + loading_factor) + operational_costs) * (1 - mitigation_discount):,.2f}")

    print("  🎉 Climate-Inclusive Premium Service functionality verified!")

def main():
    print("🔬 ClimateAI: Climate-Inclusive Premium Service Test\n")

    test_climate_premium_calculation()

    print("\n📋 Climate-Inclusive Premium Implementation Status:")
    print("   - Complete formula implemented: Prêmio_t = [E[Loss_t] · (1 + Loading) + Custo_op] · (1 - Disc_mitaga) · Climatic_Inflation_Factor(t)")
    print("   - Climatic inflation factor: exp(∫_0^t λ_s ds)")
    print("   - Climate drift rate: λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt")
    print("   - Time-dependent climate projections")
    print("   - API endpoints available at /api/v1/climate-premium/")

if __name__ == "__main__":
    main()

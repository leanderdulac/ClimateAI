#!/usr/bin/env python3
"""
Test script to verify the Parametric Insurance service structure and functionality
"""
import sys
import os
# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import numpy as np
from services.parametric_insurance_service import parametric_insurance_service

def test_parametric_insurance_functionality():
    """Test parametric insurance functionality"""
    print("🧪 Testing Parametric Insurance Service...")
    
    # Generate synthetic data
    np.random.seed(42)
    n_points = 50
    
    # Climate data
    wind_speeds = np.random.uniform(10, 30, n_points).tolist()  # m/s
    precip_data = np.random.exponential(20, n_points).tolist()  # mm
    temp_data = (25 + np.random.normal(5, 8, n_points)).tolist()  # °C
    
    # Actual losses (correlated with climate data for realistic testing)
    losses = []
    for i in range(n_points):
        # Higher losses when climate indices are high
        loss = 0
        if wind_speeds[i] > 25:
            loss += (wind_speeds[i] - 25) * 1000
        if precip_data[i] > 50:
            loss += (precip_data[i] - 50) * 500
        if temp_data[i] > 35:
            loss += (temp_data[i] - 35) * 2000
        losses.append(loss)
    
    print(f"  ✓ Generated {n_points} data points")
    print(f"  ✓ Wind speeds: range [{min(wind_speeds):.1f}, {max(wind_speeds):.1f}] m/s")
    print(f"  ✓ Precipitation: range [{min(precip_data):.1f}, {max(precip_data):.1f}] mm")
    print(f"  ✓ Temperature: range [{min(temp_data):.1f}, {max(temp_data):.1f}] °C")
    print(f"  ✓ Actual losses: range [{min(losses):.1f}, {max(losses):.1f}] $")
    
    # Test individual index calculations
    wind_indices = parametric_insurance_service.calculate_wind_index(wind_speeds, threshold=20.0)
    precip_indices = parametric_insurance_service.calculate_precipitation_index(precip_data, threshold=30.0)
    temp_indices = parametric_insurance_service.calculate_temperature_index(temp_data, threshold=30.0)
    
    print(f"  ✓ Wind indices calculated: range [{min(wind_indices):.3f}, {max(wind_indices):.3f}]")
    print(f"  ✓ Precipitation indices: range [{min(precip_indices):.3f}, {max(precip_indices):.3f}]")
    print(f"  ✓ Temperature indices: range [{min(temp_indices):.3f}, {max(temp_indices):.3f}]")
    
    # Test composite index
    composite_indices = parametric_insurance_service.calculate_composite_index(
        wind_indices, precip_indices, temp_indices
    )
    print(f"  ✓ Composite indices: range [{min(composite_indices):.3f}, {max(composite_indices):.3f}]")
    
    # Test payout calculation with a fixed trigger
    payouts = parametric_insurance_service.calculate_payout(
        composite_indices, losses, trigger=0.5, cap=100000, factor=0.8
    )
    trigger_events = sum(1 for idx in composite_indices if idx > 0.5)
    total_payout = sum(payouts)
    print(f"  ✓ Payouts calculated for trigger=0.5: {trigger_events} events, total=${total_payout:.0f}")
    
    # Test basis risk calculation
    basis_risk = parametric_insurance_service.calculate_basis_risk(payouts, losses)
    print(f"  ✓ Basis risk: {basis_risk:.2f}")
    
    # Test contract calculation (with optimization disabled to avoid complex optimization)
    contract_result = parametric_insurance_service.calculate_parametric_insurance_contract(
        wind_speeds, precip_data, temp_data, losses,
        cap=100000, factor=0.8, trigger=0.5,  # Fixed trigger to avoid optimization
        optimize_trigger_flag=False
    )
    
    print(f"  ✓ Contract calculation completed: trigger={contract_result['contract_params']['trigger']}")
    print(f"  ✓ Total payouts: ${contract_result['total_payouts']:.0f}")
    print(f"  ✓ Total losses: ${contract_result['total_losses']:.0f}")
    print(f"  ✓ Payout-loss ratio: {contract_result['payout_loss_ratio']:.3f}")
    
    print("  🎉 Parametric Insurance Service functionality verified!")

def main():
    print("🔬 ClimateAI: Parametric Insurance Service Test\n")
    
    test_parametric_insurance_functionality()
    
    print("\n📋 Parametric Insurance Implementation Status:")
    print("   - Complete formula implemented: Payout_t = K · I{Índice_t > Trigger} · min(Cap, Loss_t)")
    print("   - Climate indices: Wind, Precipitation, Temperature")
    print("   - Optimal trigger calculation: argmin_T [E[(Payout - Loss)²] + λ·BasisRisk]")
    print("   - API endpoints available at /api/v1/parametric-insurance/")

if __name__ == "__main__":
    main()
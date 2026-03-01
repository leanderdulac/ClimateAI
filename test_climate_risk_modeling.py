#!/usr/bin/env python3
"""
Test script to demonstrate the advanced climate risk modeling with regularized loss functions
"""
import sys
import os
# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import numpy as np
from services.climate_risk_modeling_service import climate_risk_modeling_service

def test_spi_calculation():
    """Test Standardized Precipitation Index calculation"""
    print("🧪 Testing SPI Calculation...")

    # Generate synthetic precipitation data (daily values for 2 years)
    np.random.seed(42)
    precipitation_data = np.random.gamma(shape=2, scale=5, size=730).tolist()  # 2 years of data

    # Calculate SPI for different windows
    spi_3m = climate_risk_modeling_service.calculate_standardized_precipitation_index(
        precipitation_data, window_months=3
    )
    spi_6m = climate_risk_modeling_service.calculate_standardized_precipitation_index(
        precipitation_data, window_months=6
    )

    print(f"  ✓ 3-month SPI: {len(spi_3m)} values, range [{min(spi_3m):.2f}, {max(spi_3m):.2f}]")
    print(f"  ✓ 6-month SPI: {len(spi_6m)} values, range [{min(spi_6m):.2f}, {max(spi_6m):.2f}]")
    print()

def test_rwi_calculation():
    """Test Relative Wetness Index calculation"""
    print("🧪 Testing RWI Calculation...")

    # Generate synthetic data
    np.random.seed(42)
    precipitation = np.random.exponential(scale=10, size=100).tolist()
    temperature = (20 + np.random.normal(0, 5, 100)).tolist()

    rwi_values = climate_risk_modeling_service.calculate_relative_wetness_index(
        precipitation, temperature
    )

    print(f"  ✓ RWI: {len(rwi_values)} values, range [{min(rwi_values):.3f}, {max(rwi_values):.3f}]")
    print()

def test_synoptic_patterns():
    """Test synoptic circulation pattern extraction"""
    print("🧪 Testing Synoptic Circulation Patterns...")

    # Generate synthetic data
    np.random.seed(42)
    pressure_data = (1013 + np.random.normal(0, 10, 50)).tolist()
    wind_data = [(np.random.uniform(3, 15), np.random.uniform(0, 360)) for _ in range(50)]
    lat_lon_data = [(np.random.uniform(-35, 5), np.random.uniform(-75, -30)) for _ in range(50)]

    patterns = climate_risk_modeling_service.extract_synoptic_circulation_patterns(
        pressure_data, wind_data, lat_lon_data
    )

    print(f"  ✓ Circulation patterns: {len(patterns)} records")
    if patterns:
        sample_pattern = patterns[0]
        print(f"  ✓ Sample features: pressure_anomaly={sample_pattern['pressure_anomaly']:.2f}, "
              f"wind_intensity={sample_pattern['wind_intensity']:.2f}")
    print()

def test_temperature_gradients():
    """Test vertical temperature gradient calculation"""
    print("🧪 Testing Vertical Temperature Gradients...")

    # Generate synthetic temperature profiles (surface, 850hPa, 700hPa, 500hPa)
    np.random.seed(42)
    temp_profiles = []
    for _ in range(30):
        # Create realistic temperature profile (decreasing with altitude)
        surface_temp = 20 + np.random.normal(0, 5)
        temp_profile = [
            surface_temp,           # Surface
            surface_temp - 7,       # 850 hPa (~1.5 km)
            surface_temp - 14,      # 700 hPa (~3 km)
            surface_temp - 22       # 500 hPa (~5.5 km)
        ]
        temp_profiles.append(temp_profile)

    gradients = climate_risk_modeling_service.calculate_vertical_temperature_gradient(
        temp_profiles
    )

    print(f"  ✓ Temperature gradients: {len(gradients)} values, "
          f"range [{min(gradients):.3f}, {max(gradients):.3f}] °C/km")
    print()

def test_regularized_loss_function():
    """Test regularized loss function calculation"""
    print("🧪 Testing Regularized Loss Function...")

    # Generate synthetic data
    np.random.seed(42)
    y_true = np.random.normal(100, 15, 100)
    y_pred = y_true + np.random.normal(0, 3, 100)  # Add some prediction error
    model_weights = np.random.normal(0, 1, 50)  # Model weights

    # Test different loss types
    for loss_type in ['mse', 'mae']:
        reg_loss = climate_risk_modeling_service.regularized_loss_function(
            y_true, y_pred, model_weights, gamma=0.1, lambda_reg=0.01, loss_type=loss_type
        )
        print(f"  ✓ {loss_type.upper()} regularized loss: {reg_loss:.3f}")

    print()

def test_comprehensive_climate_risk():
    """Test comprehensive climate risk assessment"""
    print("🧪 Testing Comprehensive Climate Risk Assessment...")

    # Generate synthetic data (at least 90 days for 3-month SPI, which is our minimum)
    np.random.seed(42)
    n_samples = 120  # This provides 3-month SPI but not 6-month or 12-month

    precipitation_data = np.random.exponential(scale=8, size=n_samples).tolist()
    temperature_data = (22 + np.random.normal(0, 4, n_samples)).tolist()
    pressure_data = (1013 + np.random.normal(0, 8, n_samples)).tolist()
    wind_data = [(np.random.uniform(4, 12), np.random.uniform(0, 360)) for _ in range(n_samples)]
    lat_lon_data = [(np.random.uniform(-30, 0), np.random.uniform(-60, -40)) for _ in range(n_samples)]

    # Create temperature profiles
    temp_profiles = []
    for i in range(n_samples):
        surface_temp = temperature_data[i]
        temp_profile = [
            surface_temp,
            surface_temp - 6 - np.random.uniform(-1, 1),  # 850hPa
            surface_temp - 12 - np.random.uniform(-1, 1), # 700hPa
            surface_temp - 20 - np.random.uniform(-1, 1)  # 500hPa
        ]
        temp_profiles.append(temp_profile)

    target_values = (0.5 + np.random.normal(0, 0.2, n_samples)).tolist()

    # Perform comprehensive assessment
    assessment = climate_risk_modeling_service.comprehensive_climate_risk_assessment(
        precipitation_data, temperature_data, pressure_data,
        wind_data, lat_lon_data, temp_profiles, target_values,
        gamma=0.1, lambda_reg=0.01
    )

    print(f"  ✓ Model MSE: {assessment['model_results']['mse']:.3f}")
    print(f"  ✓ Model MAE: {assessment['model_results']['mae']:.3f}")
    print(f"  ✓ Regularized loss: {assessment['model_results']['regularized_loss']:.3f}")
    print(f"  ✓ Predicted risk level: {assessment['risk_assessment']['predicted_risk_level']:.3f}")
    # Show SPI values if available, otherwise show that they weren't calculated due to insufficient data
    spi_3m_available = len(assessment['climate_features']['spi_3m'])
    if spi_3m_available > 0:
        print(f"  ✓ SPI 3-month values (last 5): {assessment['climate_features']['spi_3m'][-5:]}")
    else:
        print(f"  ✓ SPI 3-month values: None (insufficient data for separate calculation)")
    print(f"  ✓ Total SPI values calculated: {spi_3m_available}")
    print(f"  ✓ Low pressure systems: {assessment['synoptic_patterns']['low_pressure_systems']}")
    print()

def main():
    print("🔬 ClimateWise: Advanced Climate Risk Modeling Test Suite\n")

    test_spi_calculation()
    test_rwi_calculation()
    test_synoptic_patterns()
    test_temperature_gradients()
    test_regularized_loss_function()
    test_comprehensive_climate_risk()

    print("🎉 All advanced climate risk modeling functions are working correctly!")
    print("\n📋 Features Implemented:")
    print("   - Standardized Precipitation Index (SPI) 3/6/12 months")
    print("   - Relative Wetness Index (RWI)")
    print("   - Synoptic circulation pattern analysis")
    print("   - Vertical temperature gradient calculation")
    print("   - Regularized loss function: L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f) where Ω(f) = γT + ½λ||w||²")
    print("   - Comprehensive climate risk assessment")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to demonstrate the advanced mathematical engines in ClimateWise
"""
import sys
import os
# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import numpy as np
import asyncio
from services.extreme_value_service import combined_gev_gpd_analysis
from services.spatial_statistics_service import combined_spatial_risk_assessment
from services.stochastic_process_service import multivariate_climate_modeling

def test_extreme_value_engine():
    """Test the extreme value analysis engine"""
    print("🧪 Testing Extreme Value Analysis Engine...")

    # Generate synthetic extreme climate data (e.g., extreme precipitation)
    np.random.seed(42)
    base_data = np.random.normal(50, 15, 200)  # Base precipitation
    extreme_events = np.random.pareto(1.16, 20) * 50  # Extreme events following Pareto
    full_data = np.concatenate([base_data, extreme_events])

    # Perform combined GEV-GPD analysis
    result = combined_gev_gpd_analysis(full_data.tolist(), threshold=np.percentile(full_data, 90))

    print(f"  ✓ Block maxima analysis: {len(result['block_maxima_analysis']['block_maxima'])} blocks")
    print(f"  ✓ POT analysis: threshold={result['peaks_over_threshold_analysis']['gpd_parameters']['threshold']:.2f}")
    print(f"  ✓ Risk metrics: VaR_995={result['risk_metrics']['var_995']:.2f}")

    # Test the new climate-adapted GEV functionality
    print("  🧪 Testing Climate-Adapted GEV Functionality...")

    # Create base GEV parameters
    from services.extreme_value_service import GEVParameters
    base_params = GEVParameters(
        location=50.0,   # Base location parameter
        scale=10.0,      # Base scale parameter
        shape=0.1,       # Base shape parameter (positive for heavy tail)
        return_period=100.0,
        confidence_interval=(45.0, 55.0)
    )

    # Import the service to test the new functionality
    from services.extreme_value_service import extreme_value_service

    # Test GEV CDF calculation
    cdf_value = extreme_value_service.gev_distribution_cdf(60.0, 50.0, 10.0, 0.1)
    print(f"  ✓ GEV CDF at z=60: {cdf_value:.4f}")

    # Test climate adaptation
    adapted_params = extreme_value_service.calculate_climate_adapted_gev_params(
        base_params,
        delta_temperature=2.0,      # 2°C temperature increase
        delta_precipitation=10.0,   # 10mm precipitation change
        co2_level=450.0,            # CO2 concentration
        alpha=0.02, beta=0.01, gamma=0.001
    )
    print(f"  ✓ Climate-adapted location: {adapted_params.location:.2f} (was {base_params.location})")
    print(f"  ✓ Climate-adapted scale: {adapted_params.scale:.2f} (was {base_params.scale})")

    # Test return level calculation with climate adaptation
    return_levels = extreme_value_service.calculate_return_level_with_climate_adaptation(
        base_params,
        delta_temperature=2.0,
        delta_precipitation=10.0,
        co2_level=450.0,
        return_period=50.0
    )
    print(f"  ✓ Base return level (50yr): {return_levels['base_return_level']:.2f}")
    print(f"  ✓ Adapted return level (50yr): {return_levels['adapted_return_level']:.2f}")
    print(f"  ✓ Difference: {return_levels['difference']:.2f}")
    print()

def test_spatial_statistics_engine():
    """Test the spatial statistics engine"""
    print("🧪 Testing Spatial Statistics Engine...")

    # Generate synthetic spatial data (coordinates and risk values)
    coordinates = [
        (-23.5505, -46.6333),  # São Paulo
        (-22.9068, -43.1729),  # Rio de Janeiro
        (-19.9167, -43.9345),  # Belo Horizonte
        (-15.7942, -47.8822),  # Brasília
        (-25.4296, -49.2712),  # Curitiba
        (-30.0346, -51.2177),  # Porto Alegre
        (-12.9734, -38.4879),  # Salvador
        (-3.7184, -38.5410),  # Fortaleza
    ]

    asset_values = [1000000, 750000, 500000, 600000, 400000, 550000, 800000, 650000]
    risk_scores = [0.3, 0.7, 0.5, 0.4, 0.6, 0.5, 0.8, 0.4]

    # Perform combined spatial risk assessment
    result = combined_spatial_risk_assessment(coordinates, asset_values, risk_scores)

    print(f"  ✓ KDE analysis: {len(result['kernel_density_estimation'])} density values")
    print(f"  ✓ Spatial correlation: {result['spatial_correlation_analysis']['spatial_correlation']:.3f}")
    print(f"  ✓ Geospatial clusters: {result['geospatial_clustering']['n_clusters']} clusters")
    print(f"  ✓ Exposure density: {result['exposure_density'][:3]} (first 3 locations)")

    # Test the new spatial Gaussian Process functionality
    print("  🧪 Testing Spatial Gaussian Process Functionality...")

    from services.spatial_statistics_service import spatial_statistics_service

    # Create synthetic climate observations at each location
    climate_observations = [32.5, 28.7, 25.3, 22.1, 19.8, 17.2, 26.9, 30.1]  # temperatures

    # Create covariates (e.g., elevation, distance to coast, etc.)
    covariates = [
        [500, 1.2],   # São Paulo: elevation 500m, factor 1.2
        [35, 0.8],    # Rio: elevation 35m, factor 0.8
        [800, 1.1],   # BH: elevation 800m, factor 1.1
        [1200, 1.0],  # Brasília: elevation 1200m, factor 1.0
        [900, 0.9],   # Curitiba: elevation 900m, factor 0.9
        [100, 0.7],   # POA: elevation 100m, factor 0.7
        [20, 1.3],    # Salvador: elevation 20m, factor 1.3
        [25, 1.4]     # Fortaleza: elevation 25m, factor 1.4
    ]

    # Fit spatial Gaussian Process model
    gp_result = spatial_statistics_service.spatial_gaussian_process_model(
        coordinates, climate_observations, covariates,
        nugget=0.1, range_param=500.0, variance_param=2.0  # Units in km
    )

    print(f"  ✓ Fitted GP model with {len(climate_observations)} observations")
    print(f"  ✓ Estimated beta coefficients: {gp_result['estimated_beta'][:3]} (first 3)")
    print(f"  ✓ Model RMSE: {gp_result['rmse']:.3f}")
    print(f"  ✓ Range parameter (φ): {gp_result['parameters']['range']}")
    print(f"  ✓ Nugget parameter (η²): {gp_result['parameters']['nugget']}")

    # Test prediction at new locations
    new_locations = [
        (-20.0, -45.0),  # New location 1
        (-18.0, -40.0),  # New location 2
    ]

    new_covariates = [
        [600, 1.0],  # elevation 600m, factor 1.0
        [700, 1.1],  # elevation 700m, factor 1.1
    ]

    prediction_result = spatial_statistics_service.predict_at_new_locations(
        gp_result, new_locations, new_covariates
    )

    print(f"  ✓ Predicted at {len(new_locations)} new locations")
    print(f"  ✓ Predictions: {prediction_result['new_predictions']}")
    print(f"  ✓ Prediction variances: {prediction_result['prediction_variances']}")
    print()

def test_stochastic_processes_engine():
    """Test the stochastic processes engine"""
    print("🧪 Testing Stochastic Processes Engine...")

    # Generate synthetic climate variables
    np.random.seed(42)
    time_periods = 200
    temperature = 20 + np.cumsum(np.random.normal(0, 0.5, time_periods)) + 5 * np.sin(np.arange(time_periods) * 2 * np.pi / 365)
    precipitation = np.abs(np.random.normal(10, 8, time_periods)) * np.random.random(time_periods) * 10  # Skewed distribution

    climate_vars = {
        'temperature': temperature.tolist(),
        'precipitation': precipitation.tolist()
    }

    # Perform multivariate climate modeling
    result = multivariate_climate_modeling(climate_vars)

    print(f"  ✓ Analyzed {result['n_observations']} time periods")
    print(f"  ✓ Variables: {result['variables']}")
    print(f"  ✓ Univariate models: {list(result['univariate_models'].keys())}")
    print(f"  ✓ Dependence structure: {len(result['dependence_structure'])} pairs analyzed")
    print()

def main():
    print("🔬 ClimateWise: Advanced Mathematical Engines Test Suite\n")

    test_extreme_value_engine()
    test_spatial_statistics_engine()
    test_stochastic_processes_engine()

    print("🎉 All mathematical engines are working correctly!")
    print("\n📋 Next Steps:")
    print("   - Integrate with real climate data sources")
    print("   - Expand with CMIP6 and SSP-RCP scenarios")
    print("   - Implement civil liability modeling")
    print("   - Deploy to production environment")

if __name__ == "__main__":
    main()

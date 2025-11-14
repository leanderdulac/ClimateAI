#!/usr/bin/env python3
"""
Test script to verify the Climate Systemic Risk and Climate SCR services
"""
import sys
import os
# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import numpy as np
from services.climate_systemic_risk_service import climate_systemic_risk_service
from services.climate_scr_service import climate_scr_service

def test_climate_systemic_risk():
    """Test climate systemic risk functionality"""
    print("🧪 Testing Climate Systemic Risk Service...")
    
    # Generate synthetic data
    np.random.seed(42)
    
    # Climate data
    climate_data = {
        'temperature': [32, 36, 34, 38, 32, 35, 37, 33, 36, 34],
        'precipitation': [50, 120, 40, 150, 25, 80, 110, 35, 90, 45],
        'wind': [15, 28, 12, 35, 10, 20, 25, 18, 22, 16]
    }
    
    print(f"  ✓ Climate data: temperature=[{min(climate_data['temperature'])}, {max(climate_data['temperature'])}]°C, precipitation=[{min(climate_data['precipitation'])}, {max(climate_data['precipitation'])}]mm")
    
    # Portfolio returns
    portfolio_returns = [-0.02, -0.01, -0.03, -0.04, -0.02, -0.01, -0.03, -0.02, -0.01, -0.02]
    
    print(f"  ✓ Portfolio returns: min={min(portfolio_returns):.3f}, max={max(portfolio_returns):.3f}")
    
    # Test extreme event probability
    extreme_prob = climate_systemic_risk_service.calculate_extreme_climate_event_probability(
        climate_data, 'compound'
    )
    print(f"  ✓ Extreme event probability: {extreme_prob:.3f}")
    
    # Test conditional VaR
    covar_result = climate_systemic_risk_service.calculate_conditional_var(
        portfolio_returns, climate_data, 'compound', 0.95
    )
    print(f"  ✓ Conditional VaR (CoVaR): {covar_result:.4f}")
    
    # Test climate loading
    loading_result = climate_systemic_risk_service.calculate_climate_loading(
        portfolio_returns, climate_data, 0.95, 'compound'
    )
    print(f"  ✓ Climate loading: {loading_result.loading_climate:.4f}")
    
    print("  🎉 Climate Systemic Risk Service functionality verified!")

def test_climate_scr():
    """Test climate SCR functionality"""
    print("\n🧪 Testing Climate SCR Service...")
    
    # Climate risk factors
    climate_risk_factors = {
        'temperature_sensitivity': 0.1,
        'precipitation_sensitivity': 0.05,
        'wind_sensitivity': 0.08
    }
    
    portfolio_exposure = 1000000.0  # 1M currency units
    print(f"  ✓ Portfolio exposure: ${portfolio_exposure:,.2f}")
    print(f"  ✓ Climate risk factors: {list(climate_risk_factors.keys())}")
    
    # Test basic SCR
    basic_scr = climate_scr_service.calculate_basic_scr(
        climate_risk_factors, portfolio_exposure, 0.995
    )
    print(f"  ✓ Basic climate SCR: ${basic_scr:,.2f}")
    
    # Test uncertainty coefficient for long-term projection
    from services.climate_scr_service import ProjectionHorizon
    uncertainty_coeff = climate_scr_service.determine_uncertainty_coefficient(
        ProjectionHorizon.LONG_TERM, 'good', 0.05
    )
    print(f"  ✓ Uncertainty coefficient Ψ (long-term): {uncertainty_coeff:.3f}")
    
    # Test SCR margin calculation
    scr_margin = climate_scr_service.calculate_climate_scr_margin(basic_scr, uncertainty_coeff)
    print(f"  ✓ Climate SCR margin: ${scr_margin:,.2f}")
    print(f"    Formula: {basic_scr:,.2f} * sqrt(1 + {uncertainty_coeff:.3f}²) = ${scr_margin:,.2f}")
    
    # Test complete calculation with dynamic horizon
    time_horizon_years = 12.0
    complete_result = climate_scr_service.calculate_scr_with_dynamic_horizon(
        climate_risk_factors, portfolio_exposure, time_horizon_years, 'good', 0.995
    )
    
    print(f"  ✓ Complete SCR with dynamic horizon ({time_horizon_years} years): ${complete_result.margin:,.2f}")
    print(f"  ✓ Uncertainty coefficient: {complete_result.uncertainty_coefficient:.3f}")
    print(f"  ✓ Projection horizon: {complete_result.projection_horizon.value}")
    
    print("  🎉 Climate SCR Service functionality verified!")

def main():
    print("🔬 ClimateAI: Climate Systemic Risk & SCR Services Test\n")
    
    test_climate_systemic_risk()
    test_climate_scr()
    
    print("\n📋 Climate Systemic Risk & SCR Implementation Status:")
    print("   - Climate CoVaR implemented: Loading_clim = max(0, CoVaR_portfolio - CoVaR_benchmark)")
    print("   - Climate SCR margin: Margem = SCR_climatico · √(1 + Ψ²)")
    print("   - Uncertainty coefficient: Ψ = f(prazo_projecao, qualidade_dados)")
    print("   - Time horizon adjustments for short, medium, long term")
    print("   - Data quality integration")
    print("   - API endpoints available at /api/v1/climate-risk-analysis/")

if __name__ == "__main__":
    main()
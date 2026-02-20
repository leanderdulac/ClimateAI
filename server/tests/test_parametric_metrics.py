import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.parametric_actuary import (
    RainfallIndexContract, 
    compute_historical_payouts, 
    expected_loss_and_metrics,
    calculate_var_tvar
)

@pytest.fixture
def mock_rainfall_data():
    # Generate 10 years of synthetic rainfall data
    # Create a scenario where some years trigger
    years = range(2010, 2021)
    data = []
    
    for year in years:
        start_date = datetime(year, 1, 1)
        # 90 days of rain
        for i in range(90):
            date = start_date + timedelta(days=i)
            # Random rain with some heavy days
            rain = np.random.exponential(scale=10) 
            
            # Make 2015 and 2019 bad years (high rain for flood contract?)
            # Or low rain for drought?
            # Let's assume the contract is for EXCESS rain (Flood)
            if year in [2015, 2019] and i in [40, 41, 42]:
                rain += 100 # Huge storm
                
            data.append({
                "area_id": "TEST_AREA",
                "date": date,
                "rain_mm": rain
            })
            
    return pd.DataFrame(data)

def test_rainfall_contract_max_3day(mock_rainfall_data):
    contract = RainfallIndexContract(
        area_id="TEST_AREA",
        start_date="01-01",
        end_date="03-31",
        trigger_mm=100.0,
        exhaustion_mm=200.0,
        max_payout=1000.0,
        index_type="max_3day",
        payment_shape="linear"
    )
    
    # Test for a normal year (2010) - likely 0 payout
    idx_2010 = contract.compute_index_for_period(mock_rainfall_data, 2010)
    # Most random exp(10) sums over 3 days won't reach 100 easily unless unlucky
    # But let's check logic validity not randomness
    assert idx_2010 >= 0
    
    # Test for 2015 (Heavy Storm)
    # We added 100mm on 3 consecutive days -> sum 300mm+
    idx_2015 = contract.compute_index_for_period(mock_rainfall_data, 2015)
    assert idx_2015 > 300
    
    payout_2015 = contract.index_to_payout_amount(idx_2015)
    assert payout_2015 == 1000.0 # Full payout (capped at 200mm exhaustion)

def test_backtesting_and_metrics(mock_rainfall_data):
    contract = RainfallIndexContract(
        area_id="TEST_AREA",
        start_date="01-01",
        end_date="03-31",
        trigger_mm=100.0,
        exhaustion_mm=200.0,
        max_payout=1000.0
    )
    
    years = sorted(mock_rainfall_data['date'].dt.year.unique())
    df_payouts = compute_historical_payouts(mock_rainfall_data, contract, years)
    
    assert len(df_payouts) == len(years)
    assert "payout" in df_payouts.columns
    
    metrics = expected_loss_and_metrics(df_payouts)
    
    # We expect at least 2015 and 2019 to have payouts
    assert metrics["p_positive"] >= 2/11
    assert metrics["AAL"] > 0

def test_var_tvar_metrics():
    # Create deterministic payout series
    payouts = pd.DataFrame({
        'payout': [0, 0, 0, 0, 0, 0, 0, 0, 100, 500] 
        # 10 years. 8 zeros. 
        # 90th percentile is between 100 and 0?
        # sorted: 0,0,0,0,0,0,0,0,100,500
        # n=10.
        # VaR 95% -> index floor(0.95 * 10) = 9. -> 500?
        # Let's check logic.
    })
    
    metrics = calculate_var_tvar(payouts, alpha=0.90) 
    # idx = floor(0.9 * 10) = 9. Element at index 9 is 500.
    assert metrics['VaR'] == 500
    assert metrics['TVaR'] == 500 # Mean of [500]
    
    metrics_80 = calculate_var_tvar(payouts, alpha=0.80)
    # idx = floor(0.8 * 10) = 8. Element at index 8 is 100.
    assert metrics_80['VaR'] == 100
    # TVaR is mean of payouts[8:] -> [100, 500] -> 300
    assert metrics_80['TVaR'] == 300

"""
Testes Unitários para Backtesting Service
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from services.backtesting_service import BacktestingService

class TestBacktestingService:
    @pytest.fixture
    def backtest_service(self):
        return BacktestingService()

    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n = 365
        dates = [datetime.now() - timedelta(days=n-i) for i in range(n)]
        actual_losses = np.random.lognormal(mean=11, sigma=0.5, size=n)
        
        df = pd.DataFrame({
            'date': dates,
            'actual_loss': actual_losses,
            'latitude': -23.55,
            'longitude': -46.63,
            'coverage_amount': 100000
        })
        return df

    def test_run_backtest(self, backtest_service, sample_data):
        def mock_pricing(features, train_data):
            return 1000.0  # mock premium

        start_date = sample_data['date'].iloc[100]
        end_date = sample_data['date'].iloc[-1]
        
        result = backtest_service.run_backtest(
            model_name="MockModel",
            historical_data=sample_data,
            pricing_function=mock_pricing,
            test_period_start=start_date,
            test_period_end=end_date,
            train_period_days=30
        )
        
        assert result.model_name == "MockModel"
        assert result.n_policies > 0
        assert "mape" in result.accuracy_metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

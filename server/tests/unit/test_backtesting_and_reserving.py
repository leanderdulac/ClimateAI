"""
Unit Tests for Backtesting and Loss Reserving Services

Tests for:
- services/backtesting_service.py
- services/loss_reserving_service.py
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from services.backtesting_service import (
    BacktestingService,
    BacktestMetric,
    PolicyBacktestResult,
    ModelBacktestResult,
    backtesting_service,
)

from services.loss_reserving_service import (
    LossReservingService,
    TriangleData,
    MackResult,
    BornhuetterFergusonResult,
    BootstrapReserveResult,
    loss_reserving_service,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_triangle_data():
    """Create sample loss development triangle"""
    # Cumulative triangle data (accident years x development periods)
    data = np.array([
        [3500, 4500, 5000, 5200, 5300, 5350],
        [3800, 4900, 5400, 5600, 5700, np.nan],
        [4100, 5300, 5900, 6100, np.nan, np.nan],
        [4400, 5700, 6300, np.nan, np.nan, np.nan],
        [4800, 6200, np.nan, np.nan, np.nan, np.nan],
        [5200, np.nan, np.nan, np.nan, np.nan, np.nan],
    ])
    
    return TriangleData(
        data=data,
        accident_years=[2015, 2016, 2017, 2018, 2019, 2020],
        development_periods=[0, 12, 24, 36, 48, 60],
        cumulative=True,
    )


@pytest.fixture
def sample_historical_data():
    """Create sample historical data for backtesting"""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    
    return pd.DataFrame({
        'date': dates,
        'policy_id': [f'policy_{i}' for i in range(100)],
        'latitude': np.random.uniform(-30, 10, 100),
        'longitude': np.random.uniform(-60, -30, 100),
        'coverage_amount': np.random.uniform(50000, 500000, 100),
        'temperature': np.random.uniform(15, 35, 100),
        'precipitation': np.random.uniform(0, 100, 100),
        'actual_loss': np.random.uniform(0, 50000, 100),
        'predicted_loss': np.random.uniform(0, 50000, 100),
    })


@pytest.fixture
def sample_claims_data():
    """Create sample individual claims data"""
    return pd.DataFrame({
        'claim_id': range(1, 51),
        'accident_date': pd.date_range('2020-01-01', periods=50, freq='D'),
        'reported_date': pd.date_range('2020-01-15', periods=50, freq='D'),
        'amount': np.random.exponential(5000, 50),
    })


@pytest.fixture
def backtesting_service_instance():
    """Create backtesting service instance"""
    return BacktestingService()


@pytest.fixture
def reserving_service_instance():
    """Create loss reserving service instance"""
    return LossReservingService()


# ============================================================================
# TESTS: TRIANGLE DATA
# ============================================================================

class TestTriangleData:
    """Tests for TriangleData class"""
    
    def test_triangle_creation(self, sample_triangle_data):
        """Test triangle data creation"""
        assert sample_triangle_data.data.shape == (6, 6)
        assert len(sample_triangle_data.accident_years) == 6
        assert len(sample_triangle_data.development_periods) == 6
        assert sample_triangle_data.cumulative is True
    
    def test_triangle_from_dataframe(self):
        """Test creating triangle from DataFrame"""
        df = pd.DataFrame({
            'accident_year': [2015, 2015, 2016, 2016],
            'development_period': [0, 12, 0, 12],
            'value': [1000, 1500, 1200, 1800],
        })
        
        triangle = TriangleData.from_dataframe(df, 'value')
        
        assert triangle.data.shape == (2, 2)
        assert triangle.accident_years == [2015, 2016]
        assert triangle.development_periods == [0, 12]
    
    def test_to_incremental(self, sample_triangle_data):
        """Test converting cumulative to incremental triangle"""
        incremental = sample_triangle_data.to_incremental()
        
        # First column should be the same
        assert np.allclose(incremental[:, 0], sample_triangle_data.data[:, 0])
        
        # Second column should be differences
        expected_second = sample_triangle_data.data[:, 1] - sample_triangle_data.data[:, 0]
        assert np.allclose(incremental[:, 1], expected_second, equal_nan=True)
    
    def test_get_latest_cumulative(self, sample_triangle_data):
        """Test getting latest cumulative values"""
        latest = sample_triangle_data.get_latest_cumulative()
        
        assert len(latest) == 6
        assert latest[0] == 5350  # First row last value
        assert latest[1] == 5700  # Second row last non-NaN


# ============================================================================
# TESTS: MACK'S FORMULA
# ============================================================================

class TestMacksFormula:
    """Tests for Mack's Formula implementation"""
    
    def test_mack_basic_calculation(self, reserving_service_instance, sample_triangle_data):
        """Test basic Mack's Formula calculation"""
        result = reserving_service_instance.calculate_mack_reserve(sample_triangle_data)
        
        assert isinstance(result, MackResult)
        assert result.method == "mack"
        assert result.ultimate_losses > 0
        assert result.reserves > 0
        assert result.standard_error >= 0
        assert len(result.development_factors) > 0
    
    def test_mack_development_factors(self, reserving_service_instance, sample_triangle_data):
        """Test that development factors are reasonable"""
        result = reserving_service_instance.calculate_mack_reserve(sample_triangle_data)
        
        # All factors should be > 0
        assert all(f > 0 for f in result.development_factors)
        
        # Factors should generally decrease (later periods have less development)
        if len(result.development_factors) > 1:
            # Not a strict requirement, but common pattern
            pass  # Just verify calculation completes
    
    def test_mack_confidence_intervals(self, reserving_service_instance, sample_triangle_data):
        """Test confidence interval calculation"""
        result = reserving_service_instance.calculate_mack_reserve(
            sample_triangle_data,
            confidence_level=0.95,
        )
        
        assert "95%" in result.confidence_intervals
        ci_lower, ci_upper = result.confidence_intervals["95%"]
        assert ci_lower < result.reserves
        assert ci_upper > result.reserves
    
    def test_mack_with_invalid_triangle(self, reserving_service_instance):
        """Test Mack's Formula with invalid input"""
        # Non-cumulative triangle should raise error
        triangle = TriangleData(
            data=np.array([[1000, 1500], [1200, 1800]]),
            accident_years=[2015, 2016],
            development_periods=[0, 12],
            cumulative=False,
        )
        
        with pytest.raises(ValueError, match="cumulative"):
            reserving_service_instance.calculate_mack_reserve(triangle)


# ============================================================================
# TESTS: BORNHUETTER-FERGUSON
# ============================================================================

class TestBornhuetterFerguson:
    """Tests for Bornhuetter-Ferguson method"""
    
    def test_bf_basic_calculation(self, reserving_service_instance, sample_triangle_data):
        """Test basic Bornhuetter-Ferguson calculation"""
        prior_ultimate = 40000  # Prior estimate
        
        result = reserving_service_instance.calculate_bornhuetter_ferguson(
            sample_triangle_data,
            prior_ultimate=prior_ultimate,
        )
        
        assert isinstance(result, BornhuetterFergusonResult)
        assert result.method == "bornhuetter_ferguson"
        assert result.ultimate_losses > 0
        assert result.reserves > 0
        assert 0 <= result.credibility_weight <= 1
    
    def test_bf_credibility_weight(self, reserving_service_instance, sample_triangle_data):
        """Test credibility weight behavior"""
        # Create triangle with more development periods (should have higher credibility)
        data_large = np.array([
            [1000, 1500, 1800, 2000, 2100, 2150, 2180, 2200],
            [1100, 1600, 1900, 2100, 2200, 2250, 2280, np.nan],
            [1200, 1700, 2000, 2200, 2300, 2350, np.nan, np.nan],
            [1300, 1800, 2100, 2300, 2400, np.nan, np.nan, np.nan],
            [1400, 1900, 2200, 2400, np.nan, np.nan, np.nan, np.nan],
        ])
        
        triangle_large = TriangleData(
            data=data_large,
            accident_years=[2015, 2016, 2017, 2018, 2019],
            development_periods=[0, 12, 24, 36, 48, 60, 72, 84],
            cumulative=True,
        )
        
        result_small = reserving_service_instance.calculate_bornhuetter_ferguson(
            sample_triangle_data,
            prior_ultimate=40000,
        )
        
        result_large = reserving_service_instance.calculate_bornhuetter_ferguson(
            triangle_large,
            prior_ultimate=40000,
        )
        
        # Larger triangle should have higher credibility
        assert result_large.credibility_weight >= result_small.credibility_weight


# ============================================================================
# TESTS: BOOTSTRAP RESERVING
# ============================================================================

class TestBootstrapReserving:
    """Tests for Bootstrap reserving method"""
    
    def test_bootstrap_basic(self, reserving_service_instance, sample_triangle_data):
        """Test basic bootstrap calculation"""
        result = reserving_service_instance.calculate_bootstrap_reserves(
            sample_triangle_data,
            n_simulations=100,  # Small for testing
        )
        
        assert isinstance(result, BootstrapReserveResult)
        assert result.method == "bootstrap"
        assert result.n_simulations > 0
        assert result.point_estimate > 0
        assert result.standard_error > 0
    
    def test_bootstrap_percentiles(self, reserving_service_instance, sample_triangle_data):
        """Test bootstrap percentile calculation"""
        result = reserving_service_instance.calculate_bootstrap_reserves(
            sample_triangle_data,
            n_simulations=100,
        )
        
        # Check all percentiles exist
        expected_percentiles = ["P10", "P25", "P50", "P75", "P90", "P95", "P99"]
        for p in expected_percentiles:
            assert p in result.percentiles
        
        # Percentiles should be ordered (allowing for negative reserves in edge cases)
        assert result.percentiles["P10"] <= result.percentiles["P50"]
        assert result.percentiles["P50"] <= result.percentiles["P90"]
        
        # P50 should be close to point estimate
        assert abs(result.percentiles["P50"] - result.point_estimate) < result.standard_error * 2


# ============================================================================
# TESTS: COMPREHENSIVE RESERVING
# ============================================================================

class TestComprehensiveReserving:
    """Tests for comprehensive reserving calculation"""
    
    def test_comprehensive_all_methods(self, reserving_service_instance, sample_triangle_data, sample_claims_data):
        """Test comprehensive reserving with all methods"""
        result = reserving_service_instance.calculate_comprehensive_reserves(
            triangle=sample_triangle_data,
            prior_ultimate=40000,
            claims_data=sample_claims_data,
            exposure=1000000,
            n_bootstrap_simulations=50,
        )
        
        assert result.recommended_reserve > 0
        assert len(result.method_results) >= 2  # At least Mack and BF
        assert len(result.method_weights) > 0
        assert sum(result.method_weights.values()) == pytest.approx(1.0)
        assert result.reserve_range[0] < result.reserve_range[1]
    
    def test_comprehensive_diagnostic_metrics(self, reserving_service_instance, sample_triangle_data):
        """Test diagnostic metrics calculation"""
        result = reserving_service_instance.calculate_comprehensive_reserves(
            triangle=sample_triangle_data,
            prior_ultimate=40000,
        )
        
        assert "n_methods_used" in result.diagnostic_metrics
        assert "reserve_cv" in result.diagnostic_metrics
        assert "method_agreement" in result.diagnostic_metrics


# ============================================================================
# TESTS: BACKTESTING SERVICE
# ============================================================================

class TestBacktestingService:
    """Tests for BacktestingService"""
    
    def test_backtest_basic(self, backtesting_service_instance, sample_historical_data):
        """Test basic backtest execution"""
        # Simple pricing function for testing
        def pricing_fn(features, train_data):
            return features.get('historical_mean_loss', 10000) * 1.35
        
        test_start = datetime(2020, 2, 1)
        test_end = datetime(2020, 3, 31)
        
        result = backtesting_service_instance.run_backtest(
            model_name="test_model",
            historical_data=sample_historical_data,
            pricing_function=pricing_fn,
            test_period_start=test_start,
            test_period_end=test_end,
            train_period_days=30,
        )
        
        assert isinstance(result, ModelBacktestResult)
        assert result.model_name == "test_model"
        assert result.n_policies > 0
        assert hasattr(result, 'accuracy_metrics')
        assert hasattr(result, 'risk_metrics')
    
    def test_backtest_accuracy_metrics(self, backtesting_service_instance):
        """Test accuracy metrics calculation"""
        actual = np.array([100, 200, 300, 400, 500])
        predicted = np.array([110, 190, 310, 390, 510])
        
        metrics = backtesting_service_instance._calculate_accuracy_metrics(actual, predicted)
        
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "mape" in metrics
        assert "r_squared" in metrics
        
        # R² should be high for good predictions
        assert metrics["r_squared"] > 0.9
    
    def test_backtest_risk_metrics(self, backtesting_service_instance):
        """Test risk metrics calculation"""
        profit_losses = np.array([100, -50, 200, -30, 150, 80, -20, 300])
        premiums = np.array([500, 400, 600, 450, 550, 480, 420, 700])
        actual_losses = np.array([400, 450, 400, 480, 400, 400, 440, 400])
        
        metrics = backtesting_service_instance._calculate_risk_metrics(
            profit_losses, premiums, actual_losses, 0.95
        )
        
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "hit_ratio" in metrics
        assert "var_95" in metrics
        assert "expected_shortfall" in metrics
    
    def test_model_validation(self, backtesting_service_instance, sample_historical_data):
        """Test model validation"""
        # Create a good result manually
        result = ModelBacktestResult(
            model_name="good_model",
            test_period_start=datetime(2020, 1, 1),
            test_period_end=datetime(2020, 12, 31),
            n_policies=100,
            total_premium=100000,
            total_actual_loss=60000,
            total_predicted_loss=65000,
            net_profit=40000,
            profit_margin=0.40,
            combined_ratio=0.80,
            loss_ratio=0.60,
            expense_ratio=0.20,
            accuracy_metrics={"mape": 0.10, "r_squared": 0.85},
            risk_metrics={"sharpe_ratio": 1.5, "hit_ratio": 0.65},
        )
        
        is_valid, issues = backtesting_service_instance.validate_model(result)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_model_validation_failures(self, backtesting_service_instance):
        """Test model validation with failures"""
        # Create a bad result
        result = ModelBacktestResult(
            model_name="bad_model",
            test_period_start=datetime(2020, 1, 1),
            test_period_end=datetime(2020, 12, 31),
            n_policies=100,
            total_premium=100000,
            total_actual_loss=120000,
            total_predicted_loss=70000,
            net_profit=-20000,
            profit_margin=-0.20,
            combined_ratio=1.40,
            loss_ratio=1.20,
            expense_ratio=0.20,
            accuracy_metrics={"mape": 0.35, "r_squared": 0.40},
            risk_metrics={"sharpe_ratio": -0.5, "hit_ratio": 0.35},
        )
        
        is_valid, issues = backtesting_service_instance.validate_model(result)
        
        assert is_valid is False
        assert len(issues) > 0
    
    def test_model_comparison(self, backtesting_service_instance):
        """Test model comparison"""
        # Add multiple results
        for i, (name, profit_margin, mape) in enumerate([
            ("model_a", 0.30, 0.15),
            ("model_b", 0.40, 0.10),
            ("model_c", 0.25, 0.20),
        ]):
            result = ModelBacktestResult(
                model_name=name,
                test_period_start=datetime(2020, 1, 1),
                test_period_end=datetime(2020, 12, 31),
                n_policies=100,
                total_premium=100000,
                total_actual_loss=100000 * (1 - profit_margin),
                total_predicted_loss=70000,
                net_profit=100000 * profit_margin,
                profit_margin=profit_margin,
                combined_ratio=1 - profit_margin,
                loss_ratio=0.70,
                expense_ratio=0.20,
                accuracy_metrics={"mape": mape, "r_squared": 0.80},
                risk_metrics={"sharpe_ratio": 1.0, "hit_ratio": 0.60},
            )
            backtesting_service_instance.results_history.append(result)
        
        comparison = backtesting_service_instance.compare_models()
        
        assert comparison.best_model in ["model_a", "model_b", "model_c"]
        assert len(comparison.ranking) == 3
        assert comparison.model_results is not None


# ============================================================================
# TESTS: FREQUENCY-SEVERITY METHOD
# ============================================================================

class TestFrequencySeverity:
    """Tests for Frequency-Severity method"""
    
    def test_frequency_severity_basic(self, reserving_service_instance, sample_claims_data):
        """Test basic frequency-severity calculation"""
        exposure = 10000  # Number of policies
    
        result = reserving_service_instance.calculate_frequency_severity(
            sample_claims_data,
            exposure,
        )
        
        assert result["method"] == "frequency_severity"
        assert result["n_claims"] == len(sample_claims_data)
        assert result["frequency"] > 0
        assert result["severity"] > 0
        assert result["pure_premium"] == pytest.approx(
            result["frequency"] * result["severity"], rel=1e-5
        )
    
    def test_frequency_severity_empty_data(self, reserving_service_instance):
        """Test frequency-severity with empty data"""
        empty_df = pd.DataFrame(columns=['claim_id', 'accident_date', 'amount'])
        
        result = reserving_service_instance.calculate_frequency_severity(empty_df, 10000)
        
        assert result["n_claims"] == 0
        assert result["frequency"] == 0
        assert result["severity"] == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for reserving and backtesting"""
    
    def test_full_reserving_pipeline(self, reserving_service_instance, sample_triangle_data):
        """Test complete reserving pipeline"""
        # Calculate all methods
        mack = reserving_service_instance.calculate_mack_reserve(sample_triangle_data)
        bf = reserving_service_instance.calculate_bornhuetter_ferguson(
            sample_triangle_data, prior_ultimate=40000
        )
        bootstrap = reserving_service_instance.calculate_bootstrap_reserves(
            sample_triangle_data, n_simulations=50
        )
        comprehensive = reserving_service_instance.calculate_comprehensive_reserves(
            sample_triangle_data, prior_ultimate=40000, n_bootstrap_simulations=50
        )
        
        # All should produce positive reserves
        assert mack.reserves > 0
        assert bf.reserves > 0
        assert bootstrap.point_estimate > 0
        assert comprehensive.recommended_reserve > 0
    
    def test_backtest_report_generation(self, backtesting_service_instance, sample_historical_data):
        """Test backtest report generation"""
        def pricing_fn(features, train_data):
            return 10000
        
        result = backtesting_service_instance.run_backtest(
            model_name="report_test",
            historical_data=sample_historical_data,
            pricing_function=pricing_fn,
            test_period_start=datetime(2020, 2, 1),
            test_period_end=datetime(2020, 3, 31),
            train_period_days=30,
        )
        
        report = backtesting_service_instance.generate_backtest_report(result)
        
        assert "report_type" in report
        assert "model_name" in report
        assert "summary" in report
        assert "accuracy_metrics" in report
        assert "risk_metrics" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

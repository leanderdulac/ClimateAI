"""
Unit Tests for VaR Backtesting Service

Tests for:
- services/var_backtesting_service.py
- api/var_backtesting.py

Tests cover:
- Kupiec POF Test
- Christoffersen Independence Test
- Christoffersen Conditional Coverage Test
- Basel III Traffic Light System
- Regulatory report generation
"""

import pytest
import numpy as np
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from services.var_backtesting_service import (
    VaRBacktestingService,
    VaRBacktestResult,
    VaRBacktestReport,
    TrafficLightZone,
    RegulatoryStatus,
    TestResult,
    var_backtesting_service,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def var_backtesting_service_instance():
    """Create VaR backtesting service instance"""
    return VaRBacktestingService()


@pytest.fixture
def sample_backtest_data():
    """Generate sample backtesting data"""
    np.random.seed(42)
    n = 504  # 2 years
    
    # Generate losses from lognormal distribution
    losses = np.random.lognormal(mean=10, sigma=0.5, size=n)
    
    # Generate VaR predictions (95% VaR)
    var_95 = np.percentile(losses, 95)
    var_predictions = np.ones(n) * var_95 * 1.05  # Slightly conservative
    
    return losses, var_predictions


@pytest.fixture
def sample_exceptions():
    """Generate sample exception array"""
    np.random.seed(42)
    n = 504
    
    # Generate exceptions with ~5% rate
    exceptions = np.random.choice([0, 1], size=n, p=[0.95, 0.05])
    
    return exceptions


# ============================================================================
# TESTS: KUPIEC POF TEST
# ============================================================================

class TestKupiecPOFTest:
    """Tests for Kupiec Proportion of Failures Test"""
    
    def test_kupiec_test_pass(self, var_backtesting_service_instance):
        """Test Kupiec test with passing scenario"""
        # 25 exceptions out of 500 (5% expected)
        result = var_backtesting_service_instance._kupiec_pof_test(
            n_exceptions=25,
            n_observations=500,
            confidence_level=0.95,
        )
        
        assert isinstance(result, TestResult)
        assert result.test_name == "Kupiec POF Test"
        assert result.statistic >= 0
        assert 0 <= result.p_value <= 1
        assert result.critical_value > 0
        assert result.significance_level == 0.05
        assert "Exception rate" in result.null_hypothesis
    
    def test_kupiec_test_fail_underestimation(self, var_backtesting_service_instance):
        """Test Kupiec test with underestimation (too many exceptions)"""
        # 50 exceptions out of 500 (10% actual vs 5% expected)
        result = var_backtesting_service_instance._kupiec_pof_test(
            n_exceptions=50,
            n_observations=500,
            confidence_level=0.95,
        )
        
        # Should fail (p-value should be very low)
        assert result.p_value < 0.05
        assert result.details["observed_rate"] > result.details["expected_rate"]
    
    def test_kupiec_test_fail_overestimation(self, var_backtesting_service_instance):
        """Test Kupiec test with overestimation (too few exceptions)"""
        # 5 exceptions out of 500 (1% actual vs 5% expected)
        result = var_backtesting_service_instance._kupiec_pof_test(
            n_exceptions=5,
            n_observations=500,
            confidence_level=0.95,
        )
        
        # May or may not fail depending on p-value
        assert isinstance(result, TestResult)
        assert result.details["observed_rate"] < result.details["expected_rate"]
    
    def test_kupiec_test_edge_cases(self, var_backtesting_service_instance):
        """Test Kupiec test with edge cases"""
        # Zero exceptions
        result_zero = var_backtesting_service_instance._kupiec_pof_test(
            n_exceptions=0,
            n_observations=500,
            confidence_level=0.95,
        )
        assert isinstance(result_zero, TestResult)
        
        # All exceptions (should fail)
        result_all = var_backtesting_service_instance._kupiec_pof_test(
            n_exceptions=500,
            n_observations=500,
            confidence_level=0.95,
        )
        assert isinstance(result_all, TestResult)


# ============================================================================
# TESTS: CHRISTOFFERSEN INDEPENDENCE TEST
# ============================================================================

class TestChristoffersenIndependenceTest:
    """Tests for Christoffersen Independence Test"""
    
    def test_christoffersen_ind_no_clustering(self, var_backtesting_service_instance):
        """Test independence test with no clustering"""
        np.random.seed(42)
        n = 504
        exceptions = np.random.choice([0, 1], size=n, p=[0.95, 0.05])
        
        result = var_backtesting_service_instance._christoffersen_independence_test(
            exceptions=exceptions,
            confidence_level=0.95,
        )
        
        assert isinstance(result, TestResult)
        assert result.test_name == "Christoffersen Independence Test"
        assert "pi0" in result.details  # Transition probability
        assert "pi1" in result.details  # Transition probability
        assert "clustering_ratio" in result.details
    
    def test_christoffersen_ind_with_clustering(self, var_backtesting_service_instance):
        """Test independence test with clustering"""
        # Create clustered exceptions
        exceptions = np.zeros(504, dtype=int)
        
        # Add clusters of exceptions
        clusters = [50, 150, 300, 400]  # Start positions
        for start in clusters:
            exceptions[start:start + 5] = 1  # 5 consecutive exceptions
        
        result = var_backtesting_service_instance._christoffersen_independence_test(
            exceptions=exceptions,
            confidence_level=0.95,
        )
        
        assert isinstance(result, TestResult)
        # Clustering should be detected (pi1 > pi0)
        assert result.details["pi1"] > result.details["pi0"]
        assert result.details["clustering_ratio"] > 1
    
    def test_christoffersen_ind_insufficient_data(self, var_backtesting_service_instance):
        """Test independence test with insufficient data"""
        # Only 1 observation
        exceptions = np.array([1])
        
        result = var_backtesting_service_instance._christoffersen_independence_test(
            exceptions=exceptions,
            confidence_level=0.95,
        )
        
        assert isinstance(result, TestResult)
        assert "note" in result.details


# ============================================================================
# TESTS: CHRISTOFFERSEN CONDITIONAL COVERAGE TEST
# ============================================================================

class TestChristoffersenConditionalCoverageTest:
    """Tests for Christoffersen Conditional Coverage Test"""
    
    def test_christoffersen_cc_pass(self, var_backtesting_service_instance):
        """Test conditional coverage with passing scenario"""
        np.random.seed(42)
        n = 504
        exceptions = np.random.choice([0, 1], size=n, p=[0.95, 0.05])
        
        result = var_backtesting_service_instance._christoffersen_conditional_coverage_test(
            exceptions=exceptions,
            n_observations=n,
            confidence_level=0.95,
        )
        
        assert isinstance(result, TestResult)
        assert result.test_name == "Christoffersen Conditional Coverage Test"
        assert "kupiec_statistic" in result.details
        assert "independence_statistic" in result.details
    
    def test_christoffersen_cc_combined_statistic(self, var_backtesting_service_instance):
        """Test that CC statistic = POF + Independence"""
        np.random.seed(42)
        n = 504
        exceptions = np.random.choice([0, 1], size=n, p=[0.95, 0.05])
        
        kupiec = var_backtesting_service_instance._kupiec_pof_test(
            n_exceptions=int(np.sum(exceptions)),
            n_observations=n,
            confidence_level=0.95,
        )
        
        ind = var_backtesting_service_instance._christoffersen_independence_test(
            exceptions=exceptions,
            confidence_level=0.95,
        )
        
        cc = var_backtesting_service_instance._christoffersen_conditional_coverage_test(
            exceptions=exceptions,
            n_observations=n,
            confidence_level=0.95,
        )
        
        # CC statistic should be sum of POF and Independence
        expected_combined = kupiec.statistic + ind.statistic
        assert abs(cc.statistic - expected_combined) < 1e-6


# ============================================================================
# TESTS: BASEL III TRAFFIC LIGHT
# ============================================================================

class TestBaselTrafficLight:
    """Tests for Basel III Traffic Light System"""
    
    def test_basel_green_zone(self, var_backtesting_service_instance):
        """Test green zone (0-4 exceptions)"""
        for n_exc in [0, 1, 2, 3, 4]:
            result = var_backtesting_service_instance._basel_traffic_light(
                n_exceptions=n_exc,
                n_observations=252,
                confidence_level=0.95,
            )
            
            assert result.zone == TrafficLightZone.GREEN
            assert result.multiplier == 2.0
            assert result.status == RegulatoryStatus.COMPLIANT
    
    def test_basel_yellow_zone(self, var_backtesting_service_instance):
        """Test yellow zone (5-9 exceptions)"""
        for n_exc in [5, 6, 7, 8, 9]:
            result = var_backtesting_service_instance._basel_traffic_light(
                n_exceptions=n_exc,
                n_observations=252,
                confidence_level=0.95,
            )
            
            assert result.zone == TrafficLightZone.YELLOW
            # Sliding scale: 5=2.5, 6=2.75, 7=3.0, 8=3.25, 9=3.5
            expected_mult = 2.5 + 0.25 * (n_exc - 5)
            assert abs(result.multiplier - expected_mult) < 0.01
            assert result.status == RegulatoryStatus.NEEDS_REVIEW
    
    def test_basel_red_zone(self, var_backtesting_service_instance):
        """Test red zone (10+ exceptions)"""
        for n_exc in [10, 15, 20, 25]:
            result = var_backtesting_service_instance._basel_traffic_light(
                n_exceptions=n_exc,
                n_observations=252,
                confidence_level=0.95,
            )
            
            assert result.zone == TrafficLightZone.RED
            assert result.multiplier == 4.0
            assert result.status == RegulatoryStatus.NON_COMPLIANT
    
    def test_basel_next_review_date(self, var_backtesting_service_instance):
        """Test next review date by zone"""
        # Green zone - quarterly review
        green = var_backtesting_service_instance._basel_traffic_light(
            n_exceptions=2, n_observations=252, confidence_level=0.95
        )
        assert green.next_review_date > date.today()
        
        # Red zone - weekly review
        red = var_backtesting_service_instance._basel_traffic_light(
            n_exceptions=15, n_observations=252, confidence_level=0.95
        )
        assert red.next_review_date > date.today()
        assert (red.next_review_date - date.today()).days <= 14


# ============================================================================
# TESTS: FULL BACKTEST
# ============================================================================

class TestFullBacktest:
    """Tests for complete VaR backtesting workflow"""
    
    def test_full_backtest_well_calibrated(
        self, var_backtesting_service_instance, sample_backtest_data
    ):
        """Test backtest with well-calibrated model"""
        losses, var_predictions = sample_backtest_data
        
        result = var_backtesting_service_instance.run_backtest(
            policy_id="test_policy_001",
            historical_losses=losses,
            var_predictions=var_predictions,
            confidence_level=0.95,
            var_model="historical_simulation",
        )
        
        assert isinstance(result, VaRBacktestResult)
        assert result.policy_id == "test_policy_001"
        assert result.n_observations == len(losses)
        assert result.confidence_level == 0.95
        assert result.kupiec_test is not None
        assert result.christoffersen_ind_test is not None
        assert result.christoffersen_cc_test is not None
    
    def test_full_backtest_underestimation(
        self, var_backtesting_service_instance, sample_backtest_data
    ):
        """Test backtest with underestimating model"""
        losses, var_predictions = sample_backtest_data
        
        # Make VaR predictions too low (underestimation)
        var_predictions_under = var_predictions * 0.8
        
        result = var_backtesting_service_instance.run_backtest(
            policy_id="test_policy_under",
            historical_losses=losses,
            var_predictions=var_predictions_under,
            confidence_level=0.95,
            var_model="underestimating_model",
        )
        
        # Should have more exceptions than expected
        assert result.exception_ratio > 1.5
        assert len(result.warnings) > 0
        assert len(result.recommendations) > 0
    
    def test_full_backtest_clustering(
        self, var_backtesting_service_instance, sample_backtest_data
    ):
        """Test backtest with clustered exceptions"""
        losses, var_predictions = sample_backtest_data
        
        # Add clustering to losses
        np.random.seed(42)
        for i in range(0, len(losses), 100):
            if i + 5 < len(losses):
                losses[i:i + 5] *= 1.5  # Cluster of high losses
        
        result = var_backtesting_service_instance.run_backtest(
            policy_id="test_policy_cluster",
            historical_losses=losses,
            var_predictions=var_predictions,
            confidence_level=0.95,
            var_model="clustered_model",
        )
        
        # Clustering may or may not be detected depending on severity
        assert isinstance(result.clustering_detected, bool)
    
    def test_full_backtest_invalid_input(
        self, var_backtesting_service_instance, sample_backtest_data
    ):
        """Test backtest with invalid input"""
        losses, var_predictions = sample_backtest_data
        
        # Different lengths should raise error
        with pytest.raises(ValueError, match="Length mismatch"):
            var_backtesting_service_instance.run_backtest(
                policy_id="test_policy_invalid",
                historical_losses=losses,
                var_predictions=var_predictions[:100],  # Wrong length
                confidence_level=0.95,
            )


# ============================================================================
# TESTS: REGULATORY REPORT
# ============================================================================

class TestRegulatoryReport:
    """Tests for regulatory report generation"""
    
    def test_generate_regulatory_report(
        self, var_backtesting_service_instance, sample_backtest_data
    ):
        """Test regulatory report generation"""
        losses, var_predictions = sample_backtest_data
        
        # Run backtest first
        result = var_backtesting_service_instance.run_backtest(
            policy_id="test_policy_report",
            historical_losses=losses,
            var_predictions=var_predictions,
            confidence_level=0.95,
        )
        
        # Generate report
        report = var_backtesting_service_instance.generate_regulatory_report(
            result=result,
            prepared_by="Test Risk Analyst",
            reviewed_by="Test CRO",
            approved_by="Test Board Committee",
        )
        
        assert isinstance(report, VaRBacktestReport)
        assert report.policy_id == "test_policy_report"
        assert report.report_type == "VaR_Backtesting_Regulatory_Report"
        assert "summary" in report.__dict__
        assert "statistical_tests" in report.__dict__
        assert "basel_traffic_light" in report.__dict__
        assert "susep_compliance" in report.__dict__
        assert report.prepared_by == "Test Risk Analyst"
    
    def test_export_report_to_json(
        self, var_backtesting_service_instance, sample_backtest_data, tmp_path
    ):
        """Test exporting report to JSON"""
        losses, var_predictions = sample_backtest_data
        
        result = var_backtesting_service_instance.run_backtest(
            policy_id="test_policy_json",
            historical_losses=losses,
            var_predictions=var_predictions,
            confidence_level=0.95,
        )
        
        report = var_backtesting_service_instance.generate_regulatory_report(result)
        
        # Export to file
        filepath = tmp_path / "var_backtest_report.json"
        output_path = var_backtesting_service_instance.export_report_to_json(
            report, str(filepath)
        )
        
        assert output_path == str(filepath)
        assert filepath.exists()
        
        # Verify JSON is valid
        import json
        with open(filepath) as f:
            data = json.load(f)
            assert "report_id" in data
            assert "policy_id" in data


# ============================================================================
# TESTS: EXCEPTION ANALYSIS
# ============================================================================

class TestExceptionAnalysis:
    """Tests for exception analysis functions"""
    
    def test_analyze_exceptions_by_period(
        self, var_backtesting_service_instance
    ):
        """Test exception analysis by month"""
        np.random.seed(42)
        n = 504
        exceptions = np.random.choice([0, 1], size=n, p=[0.95, 0.05])
        
        start_date = date(2022, 1, 1)
        end_date = date(2023, 6, 30)
        
        by_month = var_backtesting_service_instance._analyze_exceptions_by_period(
            exceptions, start_date, end_date
        )
        
        assert isinstance(by_month, dict)
        # Should have entries for each month with exceptions
        assert len(by_month) > 0
        
        # Keys should be in YYYY-MM format
        for key in by_month.keys():
            assert len(key) == 7  # YYYY-MM
            assert key[4] == "-"
    
    def test_detect_clustering_true(
        self, var_backtesting_service_instance
    ):
        """Test clustering detection with actual clustering"""
        # Create clear clustering pattern
        exceptions = np.zeros(100, dtype=int)
        exceptions[10:15] = 1  # 5 exceptions in 5 days
        exceptions[50:53] = 1  # 3 exceptions in 3 days
        
        clustering = var_backtesting_service_instance._detect_clustering(
            exceptions, window_size=5
        )
        
        assert clustering is True
    
    def test_detect_clustering_false(
        self, var_backtesting_service_instance
    ):
        """Test clustering detection without clustering"""
        # Spread exceptions evenly
        exceptions = np.zeros(100, dtype=int)
        exceptions[::20] = 1  # 1 exception every 20 days
        
        clustering = var_backtesting_service_instance._detect_clustering(
            exceptions, window_size=5
        )
        
        assert clustering is False


# ============================================================================
# TESTS: RECOMMENDATIONS AND WARNINGS
# ============================================================================

class TestRecommendationsAndWarnings:
    """Tests for recommendation and warning generation"""
    
    def test_generate_recommendations_underestimation(
        self, var_backtesting_service_instance
    ):
        """Test recommendations for underestimating model"""
        # Create mock test results
        kupiec = TestResult(
            test_name="Kupiec POF Test",
            test_type="kupiec_pof",
            statistic=10.0,
            p_value=0.001,
            critical_value=3.84,
            passed=False,
            null_hypothesis="",
            alternative_hypothesis="",
            details={"observed_rate": 0.10, "expected_rate": 0.05},
        )
        
        basel = var_backtesting_service_instance._basel_traffic_light(
            n_exceptions=25, n_observations=252, confidence_level=0.95
        )
        
        recommendations = var_backtesting_service_instance._generate_recommendations(
            kupiec_test=kupiec,
            christoffersen_ind_test=None,
            christoffersen_cc_test=None,
            basel_result=basel,
            exception_ratio=2.0,
            clustering_detected=False,
        )
        
        assert len(recommendations) > 0
        assert any("underestimating" in rec.lower() or "increasing" in rec.lower()
                   for rec in recommendations)
    
    def test_generate_warnings_short_history(
        self, var_backtesting_service_instance
    ):
        """Test warnings for short history"""
        warnings = var_backtesting_service_instance._generate_warnings(
            n_observations=100,  # Less than minimum
            exception_rate=0.05,
            expected_exception_rate=0.05,
        )
        
        assert len(warnings) > 0
        assert any("below" in w.lower() and "minimum" in w.lower()
                   for w in warnings)


# ============================================================================
# TESTS: REGULATORY STATUS
# ============================================================================

class TestRegulatoryStatus:
    """Tests for regulatory status determination"""
    
    def test_status_compliant(self, var_backtesting_service_instance):
        """Test compliant status"""
        kupiec = TestResult(
            test_name="Test", test_type="test",
            statistic=0, p_value=0.5, critical_value=3.84,
            passed=True, null_hypothesis="", alternative_hypothesis="",
        )
        
        basel = var_backtesting_service_instance._basel_traffic_light(
            n_exceptions=2, n_observations=252, confidence_level=0.95
        )
        
        status = var_backtesting_service_instance._determine_regulatory_status(
            kupiec_test=kupiec,
            christoffersen_ind_test=kupiec,
            basel_result=basel,
        )
        
        assert status == RegulatoryStatus.COMPLIANT
    
    def test_status_critical(self, var_backtesting_service_instance):
        """Test critical status (red zone)"""
        kupiec = TestResult(
            test_name="Test", test_type="test",
            statistic=0, p_value=0.5, critical_value=3.84,
            passed=True, null_hypothesis="", alternative_hypothesis="",
        )
        
        basel = var_backtesting_service_instance._basel_traffic_light(
            n_exceptions=15, n_observations=252, confidence_level=0.95
        )
        
        status = var_backtesting_service_instance._determine_regulatory_status(
            kupiec_test=kupiec,
            christoffersen_ind_test=kupiec,
            basel_result=basel,
        )
        
        assert status == RegulatoryStatus.CRITICAL
    
    def test_status_needs_review(self, var_backtesting_service_instance):
        """Test needs review status"""
        kupiec = TestResult(
            test_name="Test", test_type="test",
            statistic=5.0, p_value=0.02, critical_value=3.84,
            passed=False, null_hypothesis="", alternative_hypothesis="",
        )
        
        basel = var_backtesting_service_instance._basel_traffic_light(
            n_exceptions=6, n_observations=252, confidence_level=0.95
        )
        
        status = var_backtesting_service_instance._determine_regulatory_status(
            kupiec_test=kupiec,
            christoffersen_ind_test=kupiec,
            basel_result=basel,
        )
        
        assert status == RegulatoryStatus.NEEDS_REVIEW


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for VaR backtesting"""
    
    def test_full_workflow(self, var_backtesting_service_instance):
        """Test complete backtesting workflow"""
        # Generate data
        np.random.seed(42)
        n = 504
        losses = np.random.lognormal(mean=10, sigma=0.5, size=n)
        var_predictions = np.percentile(losses, 95) * np.ones(n) * 1.05
        
        # Run backtest
        result = var_backtesting_service_instance.run_backtest(
            policy_id="integration_test_policy",
            historical_losses=losses,
            var_predictions=var_predictions,
            confidence_level=0.95,
        )
        
        # Generate report
        report = var_backtesting_service_instance.generate_regulatory_report(result)
        
        # Export to JSON (in memory)
        json_str = var_backtesting_service_instance.export_report_to_json(report)
        
        # Verify
        assert isinstance(result, VaRBacktestResult)
        assert isinstance(report, VaRBacktestReport)
        assert isinstance(json_str, str)
        assert "integration_test_policy" in json_str
    
    def test_multiple_policies(self, var_backtesting_service_instance):
        """Test backtesting multiple policies"""
        np.random.seed(42)
        
        for i in range(3):
            losses = np.random.lognormal(mean=10, sigma=0.5, size=504)
            var_predictions = np.percentile(losses, 95) * np.ones(504) * 1.05
            
            var_backtesting_service_instance.run_backtest(
                policy_id=f"policy_{i:03d}",
                historical_losses=losses,
                var_predictions=var_predictions,
                confidence_level=0.95,
            )
        
        # Check history
        assert len(var_backtesting_service_instance.results_history) == 3
        
        # Get history
        history = var_backtesting_service_instance.results_history
        assert len([r for r in history if r.policy_id.startswith("policy_")]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

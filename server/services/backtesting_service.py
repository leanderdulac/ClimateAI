"""
Backtesting Service for Climate Insurance Pricing Models

Implements comprehensive backtesting framework to validate pricing models
against historical data, ensuring model accuracy and regulatory compliance.

Features:
- Historical performance analysis
- Model accuracy metrics (MAE, RMSE, MAPE)
- Profit/Loss tracking
- Risk metric validation (VaR, Expected Shortfall)
- Model comparison and selection
- Regulatory reporting (SUSEP compliant)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class BacktestMetric(str, Enum):
    """Available backtesting metrics"""
    MAE = "mae"  # Mean Absolute Error
    RMSE = "rmse"  # Root Mean Square Error
    MAPE = "mape"  # Mean Absolute Percentage Error
    R_SQUARED = "r_squared"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    PROFIT_LOSS_RATIO = "profit_loss_ratio"
    HIT_RATIO = "hit_ratio"
    CALMAR_RATIO = "calmar_ratio"


@dataclass
class PolicyBacktestResult:
    """Result for a single policy backtest"""
    policy_id: str
    predicted_premium: float
    actual_loss: float
    predicted_loss: float
    profit_loss: float
    combined_ratio: float
    accuracy_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    timestamp: datetime


@dataclass
class ModelBacktestResult:
    """Aggregated result for a pricing model backtest"""
    model_name: str
    test_period_start: datetime
    test_period_end: datetime
    n_policies: int
    total_premium: float
    total_actual_loss: float
    total_predicted_loss: float
    net_profit: float
    profit_margin: float
    combined_ratio: float
    loss_ratio: float
    expense_ratio: float
    accuracy_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    policy_results: List[PolicyBacktestResult] = field(default_factory=list)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    statistical_tests: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestComparison:
    """Comparison of multiple models"""
    best_model: str
    ranking: List[Tuple[str, float]]  # (model_name, score)
    model_results: Dict[str, ModelBacktestResult]
    recommendation: str
    statistical_significance: Dict[str, Any]


# ============================================================================
# Legacy/Compatibility Classes for API
# ============================================================================

@dataclass
class BacktestResult:
    """Legacy backtest result for API compatibility"""
    policy_id: str
    test_period_days: int
    total_premium: float
    total_loss: float
    net_profit: float
    combined_ratio: float
    accuracy_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    validation_passed: bool
    validation_issues: List[str]
    timestamp: str


@dataclass
class VaRBacktestReport:
    """VaR backtest report for regulatory compliance"""
    policy_id: str
    rating: str
    regulatory_status: str
    var_95: Dict[str, Any]
    var_99: Dict[str, Any]
    independence: Dict[str, Any]
    total_exceptions: int
    expected_exceptions: int
    exception_ratio: float
    recommendations: List[str]
    generation_timestamp: str


class BacktestingService:
    """
    Comprehensive backtesting service for climate insurance pricing models.
    
    Implements:
    - Historical performance validation
    - Model accuracy assessment
    - Risk metric validation
    - Regulatory compliance reporting
    """
    
    def __init__(self):
        self.results_history: List[ModelBacktestResult] = []
        self.baseline_metrics: Optional[Dict[str, float]] = None
        
        # Thresholds for model validation
        self.validation_thresholds = {
            "max_mape": 0.20,  # Maximum 20% MAPE
            "min_r_squared": 0.70,  # Minimum R² of 0.70
            "max_combined_ratio": 1.00,  # Must be profitable
            "min_sharpe_ratio": 0.5,  # Minimum risk-adjusted return
            "max_var_breach_rate": 0.05,  # VaR breaches < 5%
        }
        
    def run_backtest(
        self,
        model_name: str,
        historical_data: pd.DataFrame,
        pricing_function: callable,
        test_period_start: datetime,
        test_period_end: datetime,
        train_period_days: int = 365,
        confidence_level: float = 0.95,
    ) -> ModelBacktestResult:
        """
        Run comprehensive backtest for a pricing model
        
        Args:
            model_name: Name of the model being tested
            historical_data: Historical data with features and actual losses
            pricing_function: Function that takes features and returns premium
            test_period_start: Start date of test period
            test_period_end: End date of test period
            train_period_days: Days of lookback for training
            confidence_level: Confidence level for VaR/CVaR
            
        Returns:
            ModelBacktestResult with comprehensive metrics
        """
        logger.info(f"Starting backtest for {model_name} from {test_period_start} to {test_period_end}")
        
        # Filter data for test period
        test_data = historical_data[
            (historical_data['date'] >= test_period_start) &
            (historical_data['date'] <= test_period_end)
        ].copy()
        
        if len(test_data) == 0:
            raise ValueError("No data available for test period")
        
        policy_results = []
        
        # Run backtest for each policy/period
        for idx, row in test_data.iterrows():
            # Get training data (lookback period)
            train_mask = (
                (historical_data['date'] < row['date']) &
                (historical_data['date'] >= row['date'] - timedelta(days=train_period_days))
            )
            train_data = historical_data[train_mask]
            
            # Generate features for pricing
            features = self._extract_features(row, train_data)
            
            # Get predicted premium from model
            predicted_premium = pricing_function(features, train_data)
            
            # Get actual loss
            actual_loss = row.get('actual_loss', 0.0)
            predicted_loss = row.get('predicted_loss', predicted_premium * 0.7)  # Default 70% loss ratio
            
            # Calculate metrics
            profit_loss = predicted_premium - actual_loss
            combined_ratio = actual_loss / predicted_premium if predicted_premium > 0 else float('inf')
            
            policy_result = PolicyBacktestResult(
                policy_id=row.get('policy_id', f"policy_{idx}"),
                predicted_premium=predicted_premium,
                actual_loss=actual_loss,
                predicted_loss=predicted_loss,
                profit_loss=profit_loss,
                combined_ratio=combined_ratio,
                accuracy_metrics={},  # Filled in aggregation
                risk_metrics={},  # Filled in aggregation
                timestamp=row['date'],
            )
            policy_results.append(policy_result)
        
        # Aggregate results
        result = self._aggregate_backtest_results(
            model_name=model_name,
            policy_results=policy_results,
            test_period_start=test_period_start,
            test_period_end=test_period_end,
            confidence_level=confidence_level,
        )
        
        # Store result
        self.results_history.append(result)
        
        logger.info(f"Backtest completed for {model_name}: Net Profit = {result.net_profit:.2f}, CR = {result.combined_ratio:.2%}")
        
        return result
    
    def _extract_features(self, row: pd.Series, train_data: pd.DataFrame) -> Dict[str, Any]:
        """Extract features for pricing model"""
        features = {
            'latitude': row.get('latitude', 0.0),
            'longitude': row.get('longitude', 0.0),
            'coverage_amount': row.get('coverage_amount', 100000),
            'risk_factors': {},
        }
        
        # Calculate historical statistics
        if len(train_data) > 0:
            features['historical_mean_loss'] = train_data.get('actual_loss', pd.Series([0])).mean()
            features['historical_std_loss'] = train_data.get('actual_loss', pd.Series([0])).std()
            features['historical_max_loss'] = train_data.get('actual_loss', pd.Series([0])).max()
            
        # Add climate features if available
        for col in ['temperature', 'precipitation', 'humidity', 'wind_speed']:
            if col in row:
                features['risk_factors'][col] = row[col]
        
        return features
    
    def _aggregate_backtest_results(
        self,
        model_name: str,
        policy_results: List[PolicyBacktestResult],
        test_period_start: datetime,
        test_period_end: datetime,
        confidence_level: float,
    ) -> ModelBacktestResult:
        """Aggregate individual policy results into model-level metrics"""
        
        # Extract arrays
        premiums = np.array([r.predicted_premium for r in policy_results])
        actual_losses = np.array([r.actual_loss for r in policy_results])
        predicted_losses = np.array([r.predicted_loss for r in policy_results])
        profit_losses = np.array([r.profit_loss for r in policy_results])
        combined_ratios = np.array([r.combined_ratio for r in policy_results])
        
        # Calculate totals
        total_premium = np.sum(premiums)
        total_actual_loss = np.sum(actual_losses)
        total_predicted_loss = np.sum(predicted_losses)
        net_profit = np.sum(profit_losses)
        
        # Calculate ratios
        profit_margin = net_profit / total_premium if total_premium > 0 else 0
        loss_ratio = total_actual_loss / total_premium if total_premium > 0 else float('inf')
        expense_ratio = 0.20  # Assumed 20% operational expenses
        combined_ratio = loss_ratio + expense_ratio
        
        # Calculate accuracy metrics
        accuracy_metrics = self._calculate_accuracy_metrics(actual_losses, predicted_losses)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(
            profit_losses, premiums, actual_losses, confidence_level
        )
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            profit_losses, combined_ratios, confidence_level
        )
        
        # Run statistical tests
        statistical_tests = self._run_statistical_tests(
            actual_losses, predicted_losses, profit_losses
        )
        
        return ModelBacktestResult(
            model_name=model_name,
            test_period_start=test_period_start,
            test_period_end=test_period_end,
            n_policies=len(policy_results),
            total_premium=total_premium,
            total_actual_loss=total_actual_loss,
            total_predicted_loss=total_predicted_loss,
            net_profit=net_profit,
            profit_margin=profit_margin,
            combined_ratio=combined_ratio,
            loss_ratio=loss_ratio,
            expense_ratio=expense_ratio,
            accuracy_metrics=accuracy_metrics,
            risk_metrics=risk_metrics,
            policy_results=policy_results,
            confidence_intervals=confidence_intervals,
            statistical_tests=statistical_tests,
        )
    
    def _calculate_accuracy_metrics(
        self,
        actual: np.ndarray,
        predicted: np.ndarray,
    ) -> Dict[str, float]:
        """Calculate prediction accuracy metrics"""
        
        # Filter out zeros to avoid division issues
        mask = actual > 0
        if mask.sum() == 0:
            return {
                "mae": 0.0,
                "rmse": 0.0,
                "mape": 0.0,
                "r_squared": 0.0,
            }
        
        actual_filtered = actual[mask]
        predicted_filtered = predicted[mask]
        
        # MAE (Mean Absolute Error)
        mae = np.mean(np.abs(actual_filtered - predicted_filtered))
        
        # RMSE (Root Mean Square Error)
        rmse = np.sqrt(np.mean((actual_filtered - predicted_filtered) ** 2))
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actual_filtered - predicted_filtered) / actual_filtered))
        
        # R² (Coefficient of Determination)
        ss_res = np.sum((actual_filtered - predicted_filtered) ** 2)
        ss_tot = np.sum((actual_filtered - np.mean(actual_filtered)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "r_squared": float(r_squared),
        }
    
    def _calculate_risk_metrics(
        self,
        profit_losses: np.ndarray,
        premiums: np.ndarray,
        actual_losses: np.ndarray,
        confidence_level: float,
    ) -> Dict[str, float]:
        """Calculate risk management metrics"""
        
        # Sharpe Ratio (assuming risk-free rate = 0)
        if np.std(profit_losses) > 0:
            sharpe_ratio = np.mean(profit_losses) / np.std(profit_losses)
        else:
            sharpe_ratio = float('inf') if np.mean(profit_losses) > 0 else 0.0
        
        # Maximum Drawdown
        cumulative_pnl = np.cumsum(profit_losses)
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = (cumulative_pnl - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0.0
        
        # Profit/Loss Ratio
        profits = profit_losses[profit_losses > 0]
        losses = np.abs(profit_losses[profit_losses < 0])
        pl_ratio = np.mean(profits) / np.mean(losses) if len(losses) > 0 else float('inf')
        
        # Hit Ratio (percentage of profitable policies)
        hit_ratio = np.sum(profit_losses > 0) / len(profit_losses)
        
        # VaR (Value at Risk)
        var = -np.percentile(profit_losses, (1 - confidence_level) * 100)
        
        # Expected Shortfall (CVaR)
        es = -np.mean(profit_losses[profit_losses <= -var]) if len(profit_losses[profit_losses <= -var]) > 0 else var
        
        # Calmar Ratio (return / max_drawdown)
        calmar_ratio = np.mean(profit_losses) / abs(max_drawdown) if max_drawdown != 0 else float('inf')
        
        return {
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "profit_loss_ratio": float(pl_ratio),
            "hit_ratio": float(hit_ratio),
            "var_95": float(var),
            "expected_shortfall": float(es),
            "calmar_ratio": float(calmar_ratio),
        }
    
    def _calculate_confidence_intervals(
        self,
        profit_losses: np.ndarray,
        combined_ratios: np.ndarray,
        confidence_level: float,
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for key metrics"""
        
        alpha = 1 - confidence_level
        n = len(profit_losses)
        
        # CI for mean profit/loss
        mean_pnl = np.mean(profit_losses)
        std_pnl = np.std(profit_losses, ddof=1) if n > 1 else 0
        t_value = stats.t.ppf(1 - alpha/2, df=n-1) if n > 1 else 1.96
        pnl_margin = t_value * std_pnl / np.sqrt(n) if n > 0 else 0
        
        # CI for combined ratio
        mean_cr = np.mean(combined_ratios)
        std_cr = np.std(combined_ratios, ddof=1) if n > 1 else 0
        cr_margin = t_value * std_cr / np.sqrt(n) if n > 0 else 0
        
        return {
            "mean_profit_loss": (mean_pnl - pnl_margin, mean_pnl + pnl_margin),
            "combined_ratio": (mean_cr - cr_margin, mean_cr + cr_margin),
        }
    
    def _run_statistical_tests(
        self,
        actual: np.ndarray,
        predicted: np.ndarray,
        profit_losses: np.ndarray,
    ) -> Dict[str, Any]:
        """Run statistical tests for model validation"""
        
        tests = {}
        
        # T-test: Is mean profit/loss significantly different from 0?
        t_stat, t_pvalue = stats.ttest_1samp(profit_losses, 0.0)
        tests["t_test_profit"] = {
            "t_statistic": float(t_stat),
            "p_value": float(t_pvalue),
            "significant_at_5pct": t_pvalue < 0.05,
        }
        
        # Kolmogorov-Smirnov: Do predicted and actual have same distribution?
        if len(actual) > 0 and len(predicted) > 0:
            ks_stat, ks_pvalue = stats.kstest(actual, predicted)
            tests["ks_test_distribution"] = {
                "ks_statistic": float(ks_stat),
                "p_value": float(ks_pvalue),
                "same_distribution": ks_pvalue > 0.05,
            }
        
        # Chi-square test for hit ratio (is it significantly > 0.5?)
        n_profitable = np.sum(profit_losses > 0)
        n_total = len(profit_losses)
        if n_total > 0:
            # Use binomtest instead of deprecated binom_test
            binom_result = stats.binomtest(int(n_profitable), n_total, 0.5, alternative='greater')
            tests["binomial_test_hit_ratio"] = {
                "profitable_count": int(n_profitable),
                "total_count": int(n_total),
                "p_value": float(binom_result.pvalue),
                "better_than_random": binom_result.pvalue < 0.05,
            }
        
        return tests
    
    def validate_model(self, result: ModelBacktestResult) -> Tuple[bool, List[str]]:
        """
        Validate model against predefined thresholds
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check MAPE
        mape = result.accuracy_metrics.get("mape", 0)
        if mape > self.validation_thresholds["max_mape"]:
            issues.append(f"MAPE {mape:.2%} exceeds threshold {self.validation_thresholds['max_mape']:.2%}")
        
        # Check R²
        r_squared = result.accuracy_metrics.get("r_squared", 0)
        if r_squared < self.validation_thresholds["min_r_squared"]:
            issues.append(f"R² {r_squared:.2f} below threshold {self.validation_thresholds['min_r_squared']:.2f}")
        
        # Check Combined Ratio
        if result.combined_ratio > self.validation_thresholds["max_combined_ratio"]:
            issues.append(f"Combined Ratio {result.combined_ratio:.2%} exceeds 100%")
        
        # Check Sharpe Ratio
        sharpe = result.risk_metrics.get("sharpe_ratio", 0)
        if sharpe < self.validation_thresholds["min_sharpe_ratio"]:
            issues.append(f"Sharpe Ratio {sharpe:.2f} below threshold {self.validation_thresholds['min_sharpe_ratio']:.2f}")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def compare_models(
        self,
        model_names: Optional[List[str]] = None,
        scoring_weights: Optional[Dict[str, float]] = None,
    ) -> BacktestComparison:
        """
        Compare multiple models and rank them
        
        Args:
            model_names: List of model names to compare (default: all)
            scoring_weights: Weights for scoring criteria
            
        Returns:
            BacktestComparison with ranking and recommendation
        """
        # Default weights for scoring
        if scoring_weights is None:
            scoring_weights = {
                "profit_margin": 0.30,
                "sharpe_ratio": 0.20,
                "r_squared": 0.20,
                "hit_ratio": 0.15,
                "low_mape": 0.15,  # Lower is better
            }
        
        # Filter results
        if model_names:
            results = [r for r in self.results_history if r.model_name in model_names]
        else:
            results = self.results_history
        
        if len(results) == 0:
            raise ValueError("No backtest results found for comparison")
        
        # Calculate scores
        scores = {}
        for result in results:
            score = self._calculate_model_score(result, scoring_weights)
            scores[result.model_name] = score
        
        # Rank models
        ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_model = ranking[0][0]
        
        # Generate recommendation
        best_result = next(r for r in results if r.model_name == best_model)
        is_valid, issues = self.validate_model(best_result)
        
        if is_valid:
            recommendation = f"Model '{best_model}' is recommended with score {scores[best_model]:.2f}"
        else:
            recommendation = f"Model '{best_model}' has highest score but validation issues: {'; '.join(issues)}"
        
        # Statistical significance testing
        statistical_significance = self._test_model_differences(results)
        
        return BacktestComparison(
            best_model=best_model,
            ranking=ranking,
            model_results={r.model_name: r for r in results},
            recommendation=recommendation,
            statistical_significance=statistical_significance,
        )
    
    def _calculate_model_score(
        self,
        result: ModelBacktestResult,
        weights: Dict[str, float],
    ) -> float:
        """Calculate composite score for a model"""
        
        score = 0.0
        
        # Profit Margin (higher is better)
        score += weights.get("profit_margin", 0) * result.profit_margin * 100
        
        # Sharpe Ratio (higher is better)
        score += weights.get("sharpe_ratio", 0) * result.risk_metrics.get("sharpe_ratio", 0) * 10
        
        # R² (higher is better)
        score += weights.get("r_squared", 0) * result.accuracy_metrics.get("r_squared", 0) * 100
        
        # Hit Ratio (higher is better)
        score += weights.get("hit_ratio", 0) * result.risk_metrics.get("hit_ratio", 0) * 100
        
        # MAPE (lower is better, so we invert)
        mape = result.accuracy_metrics.get("mape", 1)
        score += weights.get("low_mape", 0) * (1 - mape) * 100
        
        return score
    
    def _test_model_differences(
        self,
        results: List[ModelBacktestResult],
    ) -> Dict[str, Any]:
        """Test if differences between models are statistically significant"""
        
        if len(results) < 2:
            return {"note": "Need at least 2 models for comparison"}
        
        # Collect profit/loss arrays from all models
        pnl_arrays = {}
        for result in results:
            pnl_arrays[result.model_name] = np.array([
                r.profit_loss for r in result.policy_results
            ])
        
        # Pairwise t-tests
        pairwise_tests = []
        model_names = list(pnl_arrays.keys())
        
        for i in range(len(model_names)):
            for j in range(i + 1, len(model_names)):
                model_a = model_names[i]
                model_b = model_names[j]
                
                t_stat, p_value = stats.ttest_ind(pnl_arrays[model_a], pnl_arrays[model_b])
                
                pairwise_tests.append({
                    "model_a": model_a,
                    "model_b": model_b,
                    "t_statistic": float(t_stat),
                    "p_value": float(p_value),
                    "significant": p_value < 0.05,
                })
        
        return {"pairwise_t_tests": pairwise_tests}
    
    def generate_backtest_report(
        self,
        result: ModelBacktestResult,
        output_format: str = "dict",
    ) -> Dict[str, Any]:
        """Generate comprehensive backtest report"""
        
        report = {
            "report_type": "backtest_validation",
            "generated_at": datetime.now().isoformat(),
            "model_name": result.model_name,
            "test_period": {
                "start": result.test_period_start.isoformat(),
                "end": result.test_period_end.isoformat(),
                "days": (result.test_period_end - result.test_period_start).days,
            },
            "summary": {
                "n_policies": result.n_policies,
                "total_premium": result.total_premium,
                "total_loss": result.total_actual_loss,
                "net_profit": result.net_profit,
                "profit_margin_pct": result.profit_margin * 100,
                "combined_ratio_pct": result.combined_ratio * 100,
            },
            "accuracy_metrics": result.accuracy_metrics,
            "risk_metrics": result.risk_metrics,
            "confidence_intervals": result.confidence_intervals,
            "statistical_tests": result.statistical_tests,
            "validation": self.validate_model(result),
        }
        
        if output_format == "json":
            import json
            return json.loads(json.dumps(report, default=str))
        
        return report


# Singleton instance
backtesting_service = BacktestingService()


# ============================================================================
# Legacy/Compatibility Methods for API
# ============================================================================

# Add legacy attributes to BacktestingService for API compatibility
BacktestingService.min_history_years = 10  # Minimum 10 years for regulatory compliance
BacktestingService.stress_scenarios = [
    {"name": "2008_subprime_crisis", "description": "Global financial crisis"},
    {"name": "2020_covid_pandemic", "description": "COVID-19 pandemic impact"},
    {"name": "brazil_2015_recession", "description": "Brazil economic recession"},
    {"name": "climate_extreme_event", "description": "100-year climate event"},
]

# Add legacy methods to BacktestingService
def _generate_var_backtest_report(
    self,
    policy_id: str,
    historical_losses: np.ndarray,
    var_predictions: np.ndarray,
) -> VaRBacktestReport:
    """Generate VaR backtest report for regulatory compliance"""
    from scipy import stats
    
    # Calculate exceptions (breaches)
    exceptions_95 = historical_losses > var_predictions * (np.percentile(var_predictions, 95) / np.percentile(historical_losses, 95))
    exceptions_99 = historical_losses > var_predictions * (np.percentile(var_predictions, 99) / np.percentile(historical_losses, 99))
    
    n_95 = np.sum(exceptions_95)
    n_99 = np.sum(exceptions_99)
    expected_95 = int(len(historical_losses) * 0.05)
    expected_99 = int(len(historical_losses) * 0.01)
    
    # Kupiec POF test
    def kupiec_pof(n, N, p):
        """Kupiec Proportion of Failures test"""
        if n == 0:
            return 1.0, True
        p_hat = n / N
        if p_hat == 0 or p_hat == 1:
            return 0.0, False
        lr = -2 * np.log(((1-p)**(N-n) * p**n) / ((1-p_hat)**(N-n) * p_hat**n))
        p_value = 1 - stats.chi2.cdf(lr, 1)
        return p_value, p_value > 0.05
    
    # Christoffersen independence test
    def christoffersen_ind(exceptions):
        """Christoffersen Independence test"""
        n = len(exceptions)
        if n < 2:
            return 1.0, True
        
        # Count transitions
        n00 = n01 = n10 = n11 = 0
        for i in range(1, n):
            if exceptions[i-1] == 0 and exceptions[i] == 0:
                n00 += 1
            elif exceptions[i-1] == 0 and exceptions[i] == 1:
                n01 += 1
            elif exceptions[i-1] == 1 and exceptions[i] == 0:
                n10 += 1
            else:
                n11 += 1
        
        n0 = n00 + n01
        n1 = n10 + n11
        
        if n0 == 0 or n1 == 0:
            return 1.0, True
        
        p0 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0
        p1 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0
        p = (n01 + n11) / n
        
        if p0 == 0 or p1 == 0 or p == 0:
            return 1.0, True
        
        lr = -2 * np.log(
            ((1-p0)**n00 * p0**n01 * (1-p1)**n10 * p1**n11) /
            ((1-p)**(n00+n01) * p**(n01) * (1-p)**(n10+n11) * p**(n11))
        )
        p_value = 1 - stats.chi2.cdf(lr, 1)
        return p_value, p_value > 0.05
    
    # Run tests
    pof_95_passed = kupiec_pof(n_95, len(historical_losses), 0.05)[1]
    pof_99_passed = kupiec_pof(n_99, len(historical_losses), 0.01)[1]
    ind_95_passed = christoffersen_ind(exceptions_95)[1]
    ind_99_passed = christoffersen_ind(exceptions_99)[1]
    
    # Determine rating
    all_passed = pof_95_passed and pof_99_passed and ind_95_passed and ind_99_passed
    var_passed = pof_95_passed and pof_99_passed
    
    if all_passed:
        rating = "AAA" if n_95 <= expected_95 * 1.1 else "AA"
    elif var_passed:
        rating = "A"
    elif pof_95_passed:
        rating = "BBB"
    else:
        rating = "BB"
    
    # Generate recommendations
    recommendations = []
    if not pof_95_passed:
        recommendations.append("VaR 95% model needs recalibration - exception rate too high")
    if not pof_99_passed:
        recommendations.append("VaR 99% model needs recalibration - exception rate too high")
    if not ind_95_passed:
        recommendations.append("Exceptions show clustering - consider regime-switching model")
    if not recommendations:
        recommendations.append("Model performs well within regulatory tolerance")
    
    return VaRBacktestReport(
        policy_id=policy_id,
        rating=rating,
        regulatory_status="COMPLIANT" if all_passed else "NEEDS_REVIEW",
        var_95={"passed": pof_95_passed, "exceptions": int(n_95), "expected": expected_95},
        var_99={"passed": pof_99_passed, "exceptions": int(n_99), "expected": expected_99},
        independence={"passed": ind_95_passed and ind_99_passed},
        total_exceptions=int(n_95 + n_99),
        expected_exceptions=expected_95 + expected_99,
        exception_ratio=(n_95 + n_99) / (expected_95 + expected_99) if (expected_95 + expected_99) > 0 else 0,
        recommendations=recommendations,
        generation_timestamp=datetime.now().isoformat(),
    )


def _run_stress_test(self, portfolio_df, scenarios=None):
    """Run stress test on portfolio"""
    results = {}
    
    default_scenarios = {
        "2008_subprime_crisis": {"loss_multiplier": 2.5, "probability": 0.01},
        "2020_covid_pandemic": {"loss_multiplier": 3.0, "probability": 0.02},
        "brazil_2015_recession": {"loss_multiplier": 1.8, "probability": 0.05},
        "climate_extreme_event": {"loss_multiplier": 5.0, "probability": 0.01},
    }
    
    scenarios_to_run = scenarios if scenarios else list(default_scenarios.keys())
    
    for scenario_name in scenarios_to_run:
        scenario_params = default_scenarios.get(scenario_name, {"loss_multiplier": 2.0, "probability": 0.05})
        
        # Simulate losses under stress
        base_losses = portfolio_df.select_dtypes(include=[np.number]).sum().sum() if hasattr(portfolio_df, 'select_dtypes') else 100000
        stressed_loss = base_losses * scenario_params["loss_multiplier"]
        
        results[scenario_name] = {
            "scenario": scenario_name,
            "loss_multiplier": scenario_params["loss_multiplier"],
            "probability": scenario_params["probability"],
            "total_loss": stressed_loss,
            "impact_description": f"Losses increase by {(scenario_params['loss_multiplier'] - 1) * 100:.0f}%",
        }
    
    return results


def _validate_minimum_history(self, start_date, end_date):
    """Validate minimum history requirements"""
    years = (end_date - start_date).days / 365.25
    
    if years >= self.min_history_years:
        return True, f"Historical period of {years:.1f} years meets regulatory requirements"
    else:
        return False, f"Historical period of {years:.1f} years is below minimum {self.min_history_years} years"


# Bind methods to class
BacktestingService.generate_var_backtest_report = _generate_var_backtest_report
BacktestingService.run_stress_test = _run_stress_test
BacktestingService.validate_minimum_history = _validate_minimum_history

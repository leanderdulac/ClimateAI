"""
VaR Backtesting Service - Implementation of Regulatory Tests

Implements comprehensive VaR backtesting framework for regulatory compliance:
- Kupiec POF (Proportion of Failures) Test
- Christoffersen Independence Test
- Christoffersen Conditional Coverage Test
- Basel III Traffic Light System
- SUSEP Circular 562/2015 Compliance

References:
- Kupiec, P. (1995). "Techniques for Verifying the Accuracy of Risk Measurement Models"
- Christoffersen, P. (1998). "Evaluating Interval Forecasts"
- Basel Committee (1996). "Supervisory Framework for the Use of Backtesting"
- SUSEP Circular 562/2015 (Seguros Paramétricos)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import json

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class TrafficLightZone(str, Enum):
    """Basel III Traffic Light Zones"""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class RegulatoryStatus(str, Enum):
    """Regulatory compliance status"""
    COMPLIANT = "compliant"
    NEEDS_REVIEW = "needs_review"
    NON_COMPLIANT = "non_compliant"
    CRITICAL = "critical"


class TestType(str, Enum):
    """Available backtesting tests"""
    KUPIC_POF = "kupiec_pof"
    CHRISTOFFERSEN_IND = "christoffersen_independence"
    CHRISTOFFERSEN_CC = "christoffersen_conditional_coverage"
    BASEL_TRAFFIC_LIGHT = "basel_traffic_light"
    SUSEP_COMPLIANCE = "susep_compliance"


@dataclass
class TestResult:
    """Result from a single statistical test"""
    test_name: str
    test_type: str
    statistic: float
    p_value: float
    critical_value: float
    passed: bool
    null_hypothesis: str
    alternative_hypothesis: str
    significance_level: float = 0.05
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VaRBacktestResult:
    """Complete VaR backtesting result"""
    policy_id: str
    test_period_start: date
    test_period_end: date
    n_observations: int
    confidence_level: float
    var_model: str
    
    # Exception statistics
    total_exceptions: int
    expected_exceptions: int
    exception_rate: float
    expected_exception_rate: float
    exception_ratio: float
    
    # Statistical tests
    kupiec_test: Optional[TestResult] = None
    christoffersen_ind_test: Optional[TestResult] = None
    christoffersen_cc_test: Optional[TestResult] = None
    
    # Basel III Traffic Light
    traffic_light_zone: TrafficLightZone = TrafficLightZone.GREEN
    basel_multiplier: float = 2.0
    regulatory_status: RegulatoryStatus = RegulatoryStatus.COMPLIANT
    
    # Time series analysis
    exceptions_by_month: Dict[str, int] = field(default_factory=dict)
    clustering_detected: bool = False
    independence_violated: bool = False
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    generation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    model_version: str = "1.0"


@dataclass
class BaselTrafficLightResult:
    """Basel III Traffic Light System result"""
    zone: TrafficLightZone
    n_exceptions: int
    n_observations: int
    confidence_level: float
    multiplier: float
    status: RegulatoryStatus
    description: str
    required_action: str
    next_review_date: Optional[date] = None


@dataclass
class VaRBacktestReport:
    """Comprehensive VaR backtesting report for regulatory submission"""
    report_id: str
    policy_id: str
    report_type: str
    generated_at: str
    test_period: Dict[str, str]
    
    # Summary
    summary: Dict[str, Any]
    
    # Test results
    statistical_tests: Dict[str, Dict[str, Any]]
    
    # Basel III
    basel_traffic_light: Dict[str, Any]
    
    # SUSEP compliance
    susep_compliance: Dict[str, Any]
    
    # Recommendations
    recommendations: List[str]
    required_actions: List[str]
    
    # Signatures
    prepared_by: str
    reviewed_by: str
    approved_by: str


class VaRBacktestingService:
    """
    Comprehensive VaR Backtesting Service for regulatory compliance.
    
    Implements tests required by:
    - SUSEP Circular 562/2015 (Seguros Paramétricos)
    - Basel III Market Risk Framework
    - Solvency II Internal Models
    """
    
    def __init__(self):
        # Minimum history requirements
        self.min_history_days = {
            "susep": 2520,  # 10 years (trading days)
            "basel_iii": 252,  # 1 year minimum
            "recommended": 504,  # 2 years recommended
        }
        
        # Basel III Traffic Light thresholds (for 95% VaR, 1 year = 252 observations)
        self.basel_thresholds = {
            "green_zone_max": 4,  # 0-4 exceptions: green zone
            "yellow_zone_max": 9,  # 5-9 exceptions: yellow zone
            # 10+ exceptions: red zone
        }
        
        # Significance levels
        self.significance_level = 0.05
        
        # Historical results storage
        self.results_history: List[VaRBacktestResult] = []
        
    def run_backtest(
        self,
        policy_id: str,
        historical_losses: np.ndarray,
        var_predictions: np.ndarray,
        confidence_level: float = 0.95,
        var_model: str = "historical_simulation",
        test_period_start: Optional[date] = None,
        test_period_end: Optional[date] = None,
    ) -> VaRBacktestResult:
        """
        Run comprehensive VaR backtesting
        
        Args:
            policy_id: Policy identifier
            historical_losses: Array of actual historical losses
            var_predictions: Array of VaR predictions (same length as losses)
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            var_model: VaR model name
            test_period_start: Start date of test period
            test_period_end: End date of test period
            
        Returns:
            VaRBacktestResult with all test results
        """
        logger.info(f"Starting VaR backtest for {policy_id} at {confidence_level:.2%} confidence")
        
        # Validate inputs
        if len(historical_losses) != len(var_predictions):
            raise ValueError(
                f"Length mismatch: losses={len(historical_losses)}, "
                f"var={len(var_predictions)}"
            )
        
        if len(historical_losses) < self.min_history_days["basel_iii"]:
            logger.warning(
                f"History of {len(historical_losses)} days is below "
                f"minimum {self.min_history_days['basel_iii']} days"
            )
        
        # Convert to numpy arrays
        losses = np.array(historical_losses)
        var_preds = np.array(var_predictions)
        
        # Calculate exceptions (breaches)
        exceptions = losses > var_preds
        n_exceptions = int(np.sum(exceptions))
        n_observations = len(losses)
        exception_rate = n_exceptions / n_observations if n_observations > 0 else 0
        expected_exception_rate = 1 - confidence_level
        expected_exceptions = int(n_observations * expected_exception_rate)
        exception_ratio = exception_rate / expected_exception_rate if expected_exception_rate > 0 else 0
        
        # Set default dates if not provided
        if test_period_end is None:
            test_period_end = date.today()
        if test_period_start is None:
            test_period_start = test_period_end - timedelta(days=n_observations)
        
        # Run statistical tests
        kupiec_test = self._kupiec_pof_test(
            n_exceptions, n_observations, confidence_level
        )
        
        christoffersen_ind_test = self._christoffersen_independence_test(
            exceptions, confidence_level
        )
        
        christoffersen_cc_test = self._christoffersen_conditional_coverage_test(
            exceptions, n_observations, confidence_level
        )
        
        # Basel III Traffic Light
        basel_result = self._basel_traffic_light(
            n_exceptions, n_observations, confidence_level
        )
        
        # Time series analysis
        exceptions_by_month = self._analyze_exceptions_by_period(
            exceptions, test_period_start, test_period_end
        )
        
        clustering_detected = self._detect_clustering(exceptions)
        independence_violated = not christoffersen_ind_test.passed if christoffersen_ind_test else False
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            kupiec_test, christoffersen_ind_test, christoffersen_cc_test,
            basel_result, exception_ratio, clustering_detected
        )
        
        warnings = self._generate_warnings(
            n_observations, exception_rate, expected_exception_rate
        )
        
        # Determine regulatory status
        regulatory_status = self._determine_regulatory_status(
            kupiec_test, christoffersen_ind_test, basel_result
        )
        
        # Create result object
        result = VaRBacktestResult(
            policy_id=policy_id,
            test_period_start=test_period_start,
            test_period_end=test_period_end,
            n_observations=n_observations,
            confidence_level=confidence_level,
            var_model=var_model,
            total_exceptions=n_exceptions,
            expected_exceptions=expected_exceptions,
            exception_rate=exception_rate,
            expected_exception_rate=expected_exception_rate,
            exception_ratio=exception_ratio,
            kupiec_test=kupiec_test,
            christoffersen_ind_test=christoffersen_ind_test,
            christoffersen_cc_test=christoffersen_cc_test,
            traffic_light_zone=basel_result.zone,
            basel_multiplier=basel_result.multiplier,
            regulatory_status=regulatory_status,
            exceptions_by_month=exceptions_by_month,
            clustering_detected=clustering_detected,
            independence_violated=independence_violated,
            recommendations=recommendations,
            warnings=warnings,
        )
        
        # Store result
        self.results_history.append(result)
        
        logger.info(
            f"VaR backtest completed for {policy_id}: "
            f"{n_exceptions}/{n_observations} exceptions, "
            f"zone={basel_result.zone.value}, "
            f"status={regulatory_status.value}"
        )
        
        return result
    
    def _kupiec_pof_test(
        self,
        n_exceptions: int,
        n_observations: int,
        confidence_level: float,
    ) -> TestResult:
        """
        Kupiec Proportion of Failures (POF) Test
        
        Tests if the exception rate equals the expected rate.
        
        Null hypothesis: Exception rate = expected rate
        Alternative: Exception rate ≠ expected rate
        
        Test statistic follows Chi-squared(1) distribution.
        """
        p = 1 - confidence_level  # Expected exception rate
        n = n_observations
        x = n_exceptions
        
        # Calculate likelihood ratio test statistic
        if x == 0 or x == n:
            # Edge cases
            lr_stat = float('inf') if x != n * p else 0
        else:
            p_hat = x / n  # Observed exception rate
            
            # Likelihood ratio
            lr_stat = -2 * np.log(
                ((1 - p) ** (n - x)) * (p ** x) /
                ((1 - p_hat) ** (n - x)) * (p_hat ** x)
            )
        
        # Calculate p-value from Chi-squared(1) distribution
        p_value = 1 - stats.chi2.cdf(lr_stat, 1)
        
        # Critical value at 5% significance level
        critical_value = stats.chi2.ppf(1 - self.significance_level, 1)
        
        # Test passes if p-value > significance level
        passed = p_value > self.significance_level
        
        return TestResult(
            test_name="Kupiec POF Test",
            test_type=TestType.KUPIC_POF.value,
            statistic=float(lr_stat),
            p_value=float(p_value),
            critical_value=float(critical_value),
            passed=passed,
            null_hypothesis="Exception rate equals expected rate",
            alternative_hypothesis="Exception rate differs from expected rate",
            significance_level=self.significance_level,
            details={
                "observed_exceptions": x,
                "expected_exceptions": int(n * p),
                "observed_rate": x / n if n > 0 else 0,
                "expected_rate": p,
                "rate_ratio": (x / n) / p if n > 0 and p > 0 else 0,
            }
        )
    
    def _christoffersen_independence_test(
        self,
        exceptions: np.ndarray,
        confidence_level: float,
    ) -> TestResult:
        """
        Christoffersen Independence Test
        
        Tests if exceptions are independent over time (no clustering).
        
        Null hypothesis: Exceptions are independent
        Alternative: Exceptions show clustering
        
        Test statistic follows Chi-squared(1) distribution.
        """
        n = len(exceptions)
        
        if n < 2:
            return TestResult(
                test_name="Christoffersen Independence Test",
                test_type=TestType.CHRISTOFFERSEN_IND.value,
                statistic=0.0,
                p_value=1.0,
                critical_value=stats.chi2.ppf(1 - self.significance_level, 1),
                passed=True,
                null_hypothesis="Exceptions are independent",
                alternative_hypothesis="Exceptions show clustering",
                significance_level=self.significance_level,
                details={"note": "Insufficient data for independence test"}
            )
        
        # Count transitions
        n00 = n01 = n10 = n11 = 0
        for i in range(1, n):
            if exceptions[i - 1] == 0 and exceptions[i] == 0:
                n00 += 1
            elif exceptions[i - 1] == 0 and exceptions[i] == 1:
                n01 += 1
            elif exceptions[i - 1] == 1 and exceptions[i] == 0:
                n10 += 1
            else:  # both 1
                n11 += 1
        
        n0 = n00 + n01  # Total transitions from non-exception
        n1 = n10 + n11  # Total transitions from exception
        
        if n0 == 0 or n1 == 0:
            # Cannot calculate if no transitions of one type
            return TestResult(
                test_name="Christoffersen Independence Test",
                test_type=TestType.CHRISTOFFERSEN_IND.value,
                statistic=0.0,
                p_value=1.0,
                critical_value=stats.chi2.ppf(1 - self.significance_level, 1),
                passed=True,
                null_hypothesis="Exceptions are independent",
                alternative_hypothesis="Exceptions show clustering",
                significance_level=self.significance_level,
                details={
                    "n00": n00, "n01": n01, "n10": n10, "n11": n11,
                    "note": "Insufficient transitions for independence test"
                }
            )
        
        # Calculate transition probabilities
        pi0 = n01 / n0  # Prob of exception after non-exception
        pi1 = n11 / n1  # Prob of exception after exception
        pi = (n01 + n11) / n  # Unconditional probability
        
        # Calculate likelihood ratio test statistic
        if pi0 > 0 and pi0 < 1 and pi1 > 0 and pi1 < 1 and pi > 0 and pi < 1:
            lr_ind = -2 * np.log(
                ((1 - pi0) ** n00) * (pi0 ** n01) *
                ((1 - pi1) ** n10) * (pi1 ** n11) /
                ((1 - pi) ** (n00 + n01)) * (pi ** (n01 + n11))
            )
        else:
            lr_ind = 0.0
        
        # Calculate p-value from Chi-squared(1) distribution
        p_value = 1 - stats.chi2.cdf(lr_ind, 1)
        
        # Critical value
        critical_value = stats.chi2.ppf(1 - self.significance_level, 1)
        
        # Test passes if p-value > significance level
        passed = p_value > self.significance_level
        
        return TestResult(
            test_name="Christoffersen Independence Test",
            test_type=TestType.CHRISTOFFERSEN_IND.value,
            statistic=float(lr_ind),
            p_value=float(p_value),
            critical_value=float(critical_value),
            passed=passed,
            null_hypothesis="Exceptions are independent",
            alternative_hypothesis="Exceptions show clustering",
            significance_level=self.significance_level,
            details={
                "n00": n00, "n01": n01, "n10": n10, "n11": n11,
                "pi0": float(pi0),  # Prob(exception | no exception yesterday)
                "pi1": float(pi1),  # Prob(exception | exception yesterday)
                "pi": float(pi),  # Unconditional probability
                "clustering_ratio": pi1 / pi0 if pi0 > 0 else float('inf'),
            }
        )
    
    def _christoffersen_conditional_coverage_test(
        self,
        exceptions: np.ndarray,
        n_observations: int,
        confidence_level: float,
    ) -> TestResult:
        """
        Christoffersen Conditional Coverage Test
        
        Joint test of correct coverage AND independence.
        
        Null hypothesis: Correct coverage AND independence
        Alternative: Incorrect coverage OR dependence
        
        Test statistic follows Chi-squared(2) distribution.
        """
        # Get Kupiec POF test result
        n_exceptions = int(np.sum(exceptions))
        kupiec_result = self._kupiec_pof_test(
            n_exceptions, n_observations, confidence_level
        )
        
        # Get Independence test result
        ind_result = self._christoffersen_independence_test(
            exceptions, confidence_level
        )
        
        # Conditional coverage test statistic = POF + Independence
        lr_cc = kupiec_result.statistic + ind_result.statistic
        
        # Calculate p-value from Chi-squared(2) distribution
        p_value = 1 - stats.chi2.cdf(lr_cc, 2)
        
        # Critical value for Chi-squared(2)
        critical_value = stats.chi2.ppf(1 - self.significance_level, 2)
        
        # Test passes if p-value > significance level
        passed = p_value > self.significance_level
        
        return TestResult(
            test_name="Christoffersen Conditional Coverage Test",
            test_type=TestType.CHRISTOFFERSEN_CC.value,
            statistic=float(lr_cc),
            p_value=float(p_value),
            critical_value=float(critical_value),
            passed=passed,
            null_hypothesis="Correct coverage AND independence",
            alternative_hypothesis="Incorrect coverage OR dependence",
            significance_level=self.significance_level,
            details={
                "kupiec_statistic": kupiec_result.statistic,
                "independence_statistic": ind_result.statistic,
                "combined_statistic": float(lr_cc),
            }
        )
    
    def _basel_traffic_light(
        self,
        n_exceptions: int,
        n_observations: int,
        confidence_level: float,
    ) -> BaselTrafficLightResult:
        """
        Basel III Traffic Light System
        
        Categorizes VaR model performance into zones:
        - Green: 0-4 exceptions (model performing well)
        - Yellow: 5-9 exceptions (model needs review)
        - Red: 10+ exceptions (model rejected)
        
        Each zone has a corresponding multiplier for capital requirements.
        """
        # Determine zone based on number of exceptions
        if n_exceptions <= self.basel_thresholds["green_zone_max"]:
            zone = TrafficLightZone.GREEN
            multiplier = 2.0
            status = RegulatoryStatus.COMPLIANT
            description = "Model performing within acceptable parameters"
            required_action = "Continue regular monitoring"
        elif n_exceptions <= self.basel_thresholds["yellow_zone_max"]:
            zone = TrafficLightZone.YELLOW
            # Sliding scale: 5 exceptions = 2.5, 9 exceptions = 3.5
            multiplier = 2.5 + 0.25 * (n_exceptions - 5)  # 2.5 to 3.5
            status = RegulatoryStatus.NEEDS_REVIEW
            description = "Model showing signs of degradation"
            required_action = "Investigate causes and consider model adjustment"
        else:
            zone = TrafficLightZone.RED
            multiplier = 4.0
            status = RegulatoryStatus.NON_COMPLIANT
            description = "Model rejected - unacceptable performance"
            required_action = "Immediate model review and recalibration required"
        
        # Calculate next review date based on zone
        if zone == TrafficLightZone.GREEN:
            next_review = date.today() + timedelta(days=90)  # Quarterly
        elif zone == TrafficLightZone.YELLOW:
            next_review = date.today() + timedelta(days=30)  # Monthly
        else:
            next_review = date.today() + timedelta(days=7)  # Weekly
        
        return BaselTrafficLightResult(
            zone=zone,
            n_exceptions=n_exceptions,
            n_observations=n_observations,
            confidence_level=confidence_level,
            multiplier=multiplier,
            status=status,
            description=description,
            required_action=required_action,
            next_review_date=next_review,
        )
    
    def _analyze_exceptions_by_period(
        self,
        exceptions: np.ndarray,
        start_date: date,
        end_date: date,
    ) -> Dict[str, int]:
        """Analyze exceptions by month"""
        # Create date range
        dates = pd.date_range(start=start_date, end=end_date, periods=len(exceptions))
        
        # Group by month
        exceptions_by_month = {}
        for i, exc in enumerate(exceptions):
            if exc:  # Only count exceptions
                month_key = dates[i].strftime("%Y-%m")
                exceptions_by_month[month_key] = exceptions_by_month.get(month_key, 0) + 1
        
        return exceptions_by_month
    
    def _detect_clustering(self, exceptions: np.ndarray, window_size: int = 5) -> bool:
        """
        Detect clustering of exceptions
        
        Returns True if more than 2 exceptions occur within any window_size period
        """
        if len(exceptions) < window_size:
            return False
        
        for i in range(len(exceptions) - window_size + 1):
            window_sum = np.sum(exceptions[i:i + window_size])
            if window_sum >= 3:  # 3+ exceptions in 5 days = clustering
                return True
        
        return False
    
    def _generate_recommendations(
        self,
        kupiec_test: Optional[TestResult],
        christoffersen_ind_test: Optional[TestResult],
        christoffersen_cc_test: Optional[TestResult],
        basel_result: BaselTrafficLightResult,
        exception_ratio: float,
        clustering_detected: bool,
    ) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Kupiec test recommendations
        if kupiec_test and not kupiec_test.passed:
            if exception_ratio > 1.5:
                recommendations.append(
                    "VaR model is underestimating risk - consider increasing VaR estimates "
                    f"by {(exception_ratio - 1) * 100:.1f}%"
                )
            elif exception_ratio < 0.5:
                recommendations.append(
                    "VaR model is overly conservative - capital may be tied up unnecessarily"
                )
        
        # Christoffersen independence recommendations
        if christoffersen_ind_test and not christoffersen_ind_test.passed:
            recommendations.append(
                "Exceptions show clustering - consider regime-switching model or "
                "GARCH-family models to capture volatility clustering"
            )
        
        # Christoffersen conditional coverage recommendations
        if christoffersen_cc_test and not christoffersen_cc_test.passed:
            recommendations.append(
                "Model fails joint test - review both calibration and independence assumptions"
            )
        
        # Basel traffic light recommendations
        if basel_result.zone == TrafficLightZone.YELLOW:
            recommendations.append(
                f"Model in yellow zone - increase monitoring frequency and "
                f"prepare for potential recalibration"
            )
        elif basel_result.zone == TrafficLightZone.RED:
            recommendations.append(
                "URGENT: Model in red zone - immediate recalibration required. "
                "Consider temporary use of higher Basel multiplier (4.0x) for capital."
            )
        
        # Clustering recommendations
        if clustering_detected:
            recommendations.append(
                "Exception clustering detected - investigate market stress periods "
                "and consider stress testing enhancements"
            )
        
        # Default recommendation if all tests pass
        if not recommendations:
            recommendations.append(
                "Model performing within acceptable parameters - continue regular monitoring"
            )
        
        return recommendations
    
    def _generate_warnings(
        self,
        n_observations: int,
        exception_rate: float,
        expected_exception_rate: float,
    ) -> List[str]:
        """Generate warnings based on data quality and coverage"""
        warnings = []
        
        # Check minimum observations
        if n_observations < self.min_history_days["recommended"]:
            warnings.append(
                f"History of {n_observations} days is below recommended "
                f"{self.min_history_days['recommended']} days (2 years)"
            )
        
        if n_observations < self.min_history_days["basel_iii"]:
            warnings.append(
                f"History of {n_observations} days is below minimum "
                f"{self.min_history_days['basel_iii']} days required by Basel III"
            )
        
        # Check extreme exception rates
        if exception_rate > 2 * expected_exception_rate:
            warnings.append(
                f"Exception rate ({exception_rate:.2%}) is more than 2x expected "
                f"({expected_exception_rate:.2%})"
            )
        
        return warnings
    
    def _determine_regulatory_status(
        self,
        kupiec_test: Optional[TestResult],
        christoffersen_ind_test: Optional[TestResult],
        basel_result: BaselTrafficLightResult,
    ) -> RegulatoryStatus:
        """Determine overall regulatory status"""
        # Red zone = non-compliant
        if basel_result.zone == TrafficLightZone.RED:
            return RegulatoryStatus.CRITICAL
        
        # All tests pass + green zone = compliant
        kupiec_passed = kupiec_test.passed if kupiec_test else True
        ind_passed = christoffersen_ind_test.passed if christoffersen_ind_test else True
        
        if kupiec_passed and ind_passed and basel_result.zone == TrafficLightZone.GREEN:
            return RegulatoryStatus.COMPLIANT
        
        # Yellow zone or some tests fail = needs review
        if basel_result.zone == TrafficLightZone.YELLOW:
            return RegulatoryStatus.NEEDS_REVIEW
        
        if not kupiec_passed or not ind_passed:
            return RegulatoryStatus.NEEDS_REVIEW
        
        return RegulatoryStatus.COMPLIANT
    
    def generate_regulatory_report(
        self,
        result: VaRBacktestResult,
        prepared_by: str = "Risk Management System",
        reviewed_by: str = "Chief Risk Officer",
        approved_by: str = "Board Risk Committee",
    ) -> VaRBacktestReport:
        """
        Generate comprehensive regulatory report for SUSEP submission
        
        Args:
            result: VaR backtesting result
            prepared_by: Name/title of report preparer
            reviewed_by: Name/title of reviewer
            approved_by: Name/title of approver
            
        Returns:
            VaRBacktestReport ready for regulatory submission
        """
        # Generate unique report ID
        report_id = f"VAR-BT-{result.policy_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Compile statistical tests
        statistical_tests = {}
        if result.kupiec_test:
            statistical_tests["kupiec_pof"] = {
                "test_name": result.kupiec_test.test_name,
                "statistic": result.kupiec_test.statistic,
                "p_value": result.kupiec_test.p_value,
                "critical_value": result.kupiec_test.critical_value,
                "passed": result.kupiec_test.passed,
                "null_hypothesis": result.kupiec_test.null_hypothesis,
                "details": result.kupiec_test.details,
            }
        
        if result.christoffersen_ind_test:
            statistical_tests["christoffersen_independence"] = {
                "test_name": result.christoffersen_ind_test.test_name,
                "statistic": result.christoffersen_ind_test.statistic,
                "p_value": result.christoffersen_ind_test.p_value,
                "critical_value": result.christoffersen_ind_test.critical_value,
                "passed": result.christoffersen_ind_test.passed,
                "null_hypothesis": result.christoffersen_ind_test.null_hypothesis,
                "details": result.christoffersen_ind_test.details,
            }
        
        if result.christoffersen_cc_test:
            statistical_tests["christoffersen_conditional_coverage"] = {
                "test_name": result.christoffersen_cc_test.test_name,
                "statistic": result.christoffersen_cc_test.statistic,
                "p_value": result.christoffersen_cc_test.p_value,
                "critical_value": result.christoffersen_cc_test.critical_value,
                "passed": result.christoffersen_cc_test.passed,
                "null_hypothesis": result.christoffersen_cc_test.null_hypothesis,
                "details": result.christoffersen_cc_test.details,
            }
        
        # Basel III traffic light
        basel_traffic_light = {
            "zone": result.traffic_light_zone.value,
            "n_exceptions": result.total_exceptions,
            "n_observations": result.n_observations,
            "confidence_level": result.confidence_level,
            "multiplier": result.basel_multiplier,
            "status": result.regulatory_status.value,
            "next_review_date": str(date.today() + timedelta(days=90)),
        }
        
        # SUSEP compliance
        susep_compliance = {
            "circular": "562/2015",
            "minimum_history_days": self.min_history_days["susep"],
            "actual_history_days": result.n_observations,
            "history_compliant": result.n_observations >= self.min_history_days["susep"],
            "tests_performed": list(statistical_tests.keys()),
            "all_tests_passed": all(
                test.get("passed", False) for test in statistical_tests.values()
            ),
            "overall_status": result.regulatory_status.value,
        }
        
        # Required actions
        required_actions = []
        if result.regulatory_status in [RegulatoryStatus.NEEDS_REVIEW, RegulatoryStatus.CRITICAL]:
            required_actions.extend(result.recommendations)
        
        return VaRBacktestReport(
            report_id=report_id,
            policy_id=result.policy_id,
            report_type="VaR_Backtesting_Regulatory_Report",
            generated_at=datetime.now().isoformat(),
            test_period={
                "start": str(result.test_period_start),
                "end": str(result.test_period_end),
                "days": result.n_observations,
            },
            summary={
                "total_exceptions": result.total_exceptions,
                "expected_exceptions": result.expected_exceptions,
                "exception_rate": result.exception_rate,
                "expected_exception_rate": result.expected_exception_rate,
                "exception_ratio": result.exception_ratio,
                "traffic_light_zone": result.traffic_light_zone.value,
                "basel_multiplier": result.basel_multiplier,
            },
            statistical_tests=statistical_tests,
            basel_traffic_light=basel_traffic_light,
            susep_compliance=susep_compliance,
            recommendations=result.recommendations,
            required_actions=required_actions,
            prepared_by=prepared_by,
            reviewed_by=reviewed_by,
            approved_by=approved_by,
        )
    
    def export_report_to_json(
        self,
        report: VaRBacktestReport,
        filepath: Optional[str] = None,
    ) -> str:
        """Export report to JSON file"""
        import json
        
        # Custom JSON encoder for numpy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.bool_):
                    return bool(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)
        
        # Convert dataclass to dict
        report_dict = {
            "report_id": report.report_id,
            "policy_id": report.policy_id,
            "report_type": report.report_type,
            "generated_at": report.generated_at,
            "test_period": report.test_period,
            "summary": report.summary,
            "statistical_tests": report.statistical_tests,
            "basel_traffic_light": report.basel_traffic_light,
            "susep_compliance": report.susep_compliance,
            "recommendations": report.recommendations,
            "required_actions": report.required_actions,
            "prepared_by": report.prepared_by,
            "reviewed_by": report.reviewed_by,
            "approved_by": report.approved_by,
        }
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(report_dict, f, indent=2, cls=NumpyEncoder)
            logger.info(f"Report exported to {filepath}")
            return filepath
        else:
            return json.dumps(report_dict, indent=2, cls=NumpyEncoder)


# Singleton instance
var_backtesting_service = VaRBacktestingService()

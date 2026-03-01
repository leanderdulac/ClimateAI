"""
VaR Backtesting API Endpoints

Regulatory compliance endpoints for:
- SUSEP Circular 562/2015 (Seguros Paramétricos)
- Basel III Market Risk Framework
- Solvency II Internal Models

Endpoints:
- POST /api/v1/var-backtest/run - Execute VaR backtesting
- POST /api/v1/var-backtest/kupiec - Kupiec POF Test only
- POST /api/v1/var-backtest/christoffersen - Christoffersen Tests only
- GET /api/v1/var-backtest/basel-traffic-light - Basel III Traffic Light
- GET /api/v1/var-backtest/report/{policy_id} - Generate regulatory report
- GET /api/v1/var-backtest/history - Get backtesting history
- POST /api/v1/var-backtest/generate-synthetic - Generate synthetic test data
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
import numpy as np

from services.var_backtesting_service import (
    var_backtesting_service,
    VaRBacktestingService,
    VaRBacktestResult,
    VaRBacktestReport,
    TrafficLightZone,
    RegulatoryStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/var-backtest", tags=["VaR Backtesting"])


# ============================================================================
# Request/Response Models
# ============================================================================

class VaRBacktestRequest(BaseModel):
    """Request for VaR backtesting"""
    policy_id: str = Field(..., description="Policy identifier")
    historical_losses: List[float] = Field(
        ...,
        description="Historical losses (actual realized losses)",
        min_length=252,  # Minimum 1 year
    )
    var_predictions: List[float] = Field(
        ...,
        description="VaR predictions (same length as historical_losses)",
        min_length=252,
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.90,
        le=0.999,
        description="Confidence level (e.g., 0.95 for 95%)",
    )
    var_model: str = Field(
        default="historical_simulation",
        description="VaR model name/type",
    )
    test_period_start: Optional[str] = Field(
        default=None,
        description="Test period start date (YYYY-MM-DD)",
    )
    test_period_end: Optional[str] = Field(
        default=None,
        description="Test period end date (YYYY-MM-DD)",
    )


class VaRBacktestResponse(BaseModel):
    """Response from VaR backtesting"""
    policy_id: str
    test_period: dict
    n_observations: int
    confidence_level: float
    var_model: str
    
    # Exception statistics
    total_exceptions: int
    expected_exceptions: int
    exception_rate: float
    expected_exception_rate: float
    exception_ratio: float
    
    # Test results
    kupiec_test: Optional[dict]
    christoffersen_ind_test: Optional[dict]
    christoffersen_cc_test: Optional[dict]
    
    # Basel III
    traffic_light_zone: str
    basel_multiplier: float
    regulatory_status: str
    
    # Analysis
    clustering_detected: bool
    independence_violated: bool
    
    # Recommendations
    recommendations: List[str]
    warnings: List[str]
    
    # Metadata
    generation_timestamp: str


class KupiecTestRequest(BaseModel):
    """Request for Kupiec POF Test only"""
    n_exceptions: int = Field(..., ge=0, description="Number of exceptions observed")
    n_observations: int = Field(..., ge=1, description="Total number of observations")
    confidence_level: float = Field(
        default=0.95,
        ge=0.90,
        le=0.999,
        description="Confidence level",
    )


class KupiecTestResponse(BaseModel):
    """Response from Kupiec POF Test"""
    test_name: str
    statistic: float
    p_value: float
    critical_value: float
    passed: bool
    null_hypothesis: str
    alternative_hypothesis: str
    significance_level: float
    details: dict


class ChristoffersenTestRequest(BaseModel):
    """Request for Christoffersen Tests"""
    exceptions: List[int] = Field(
        ...,
        description="Binary array: 1=exception, 0=no exception",
        min_length=2,
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.90,
        le=0.999,
        description="Confidence level",
    )


class ChristoffersenTestResponse(BaseModel):
    """Response from Christoffersen Tests"""
    independence_test: dict
    conditional_coverage_test: dict


class BaselTrafficLightRequest(BaseModel):
    """Request for Basel III Traffic Light"""
    n_exceptions: int = Field(..., ge=0, description="Number of exceptions")
    n_observations: int = Field(..., ge=1, description="Total observations")
    confidence_level: float = Field(
        default=0.95,
        ge=0.90,
        le=0.999,
        description="Confidence level",
    )


class BaselTrafficLightResponse(BaseModel):
    """Response from Basel III Traffic Light"""
    zone: str
    n_exceptions: int
    n_observations: int
    confidence_level: float
    multiplier: float
    status: str
    description: str
    required_action: str
    next_review_date: str


class RegulatoryReportResponse(BaseModel):
    """Response with regulatory report"""
    report_id: str
    policy_id: str
    report_type: str
    generated_at: str
    test_period: dict
    summary: dict
    statistical_tests: dict
    basel_traffic_light: dict
    susep_compliance: dict
    recommendations: List[str]
    required_actions: List[str]
    prepared_by: str
    reviewed_by: str
    approved_by: str


class GenerateSyntheticDataRequest(BaseModel):
    """Request to generate synthetic VaR backtesting data"""
    n_observations: int = Field(
        default=504,
        ge=252,
        le=5040,
        description="Number of observations (days)",
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.90,
        le=0.999,
        description="Confidence level",
    )
    var_model_bias: float = Field(
        default=0.0,
        ge=-0.5,
        le=0.5,
        description="Bias in VaR model (negative=underestimation)",
    )
    clustering_factor: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Clustering factor (0=none, 1=high clustering)",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility",
    )


class GenerateSyntheticDataResponse(BaseModel):
    """Response with synthetic data"""
    n_observations: int
    confidence_level: float
    historical_losses: List[float]
    var_predictions: List[float]
    exceptions: List[int]
    n_exceptions: int
    expected_exceptions: int
    metadata: dict


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/run", response_model=VaRBacktestResponse)
async def run_var_backtest(request: VaRBacktestRequest):
    """
    Execute comprehensive VaR backtesting
    
    **Tests Performed:**
    - Kupiec POF Test (Proportion of Failures)
    - Christoffersen Independence Test
    - Christoffersen Conditional Coverage Test
    - Basel III Traffic Light System
    
    **Regulatory Compliance:**
    - SUSEP Circular 562/2015
    - Basel III Market Risk Framework
    - Solvency II Internal Models
    
    **Minimum Requirements:**
    - 252 observations (1 year) - Basel III minimum
    - 504 observations (2 years) - Recommended
    - 2520 observations (10 years) - SUSEP full compliance
    """
    try:
        # Parse dates if provided
        test_period_start = None
        test_period_end = None
        
        if request.test_period_start:
            test_period_start = datetime.strptime(request.test_period_start, "%Y-%m-%d").date()
        if request.test_period_end:
            test_period_end = datetime.strptime(request.test_period_end, "%Y-%m-%d").date()
        
        # Run backtest
        result = var_backtesting_service.run_backtest(
            policy_id=request.policy_id,
            historical_losses=np.array(request.historical_losses),
            var_predictions=np.array(request.var_predictions),
            confidence_level=request.confidence_level,
            var_model=request.var_model,
            test_period_start=test_period_start,
            test_period_end=test_period_end,
        )
        
        # Format response
        return VaRBacktestResponse(
            policy_id=result.policy_id,
            test_period={
                "start": str(result.test_period_start),
                "end": str(result.test_period_end),
                "days": result.n_observations,
            },
            n_observations=result.n_observations,
            confidence_level=result.confidence_level,
            var_model=result.var_model,
            total_exceptions=result.total_exceptions,
            expected_exceptions=result.expected_exceptions,
            exception_rate=result.exception_rate,
            expected_exception_rate=result.expected_exception_rate,
            exception_ratio=result.exception_ratio,
            kupiec_test=_format_test_result(result.kupiec_test) if result.kupiec_test else None,
            christoffersen_ind_test=(
                _format_test_result(result.christoffersen_ind_test)
                if result.christoffersen_ind_test else None
            ),
            christoffersen_cc_test=(
                _format_test_result(result.christoffersen_cc_test)
                if result.christoffersen_cc_test else None
            ),
            traffic_light_zone=result.traffic_light_zone.value,
            basel_multiplier=result.basel_multiplier,
            regulatory_status=result.regulatory_status.value,
            clustering_detected=result.clustering_detected,
            independence_violated=result.independence_violated,
            recommendations=result.recommendations,
            warnings=result.warnings,
            generation_timestamp=result.generation_timestamp,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in VaR backtest: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"VaR backtest failed: {str(e)}")


@router.post("/kupiec", response_model=KupiecTestResponse)
async def run_kupiec_test(request: KupiecTestRequest):
    """
    Run Kupiec POF Test only
    
    **Purpose:** Test if exception rate equals expected rate
    
    **Null Hypothesis:** Exception rate = expected rate
    
    **Distribution:** Chi-squared(1)
    """
    result = var_backtesting_service._kupiec_pof_test(
        n_exceptions=request.n_exceptions,
        n_observations=request.n_observations,
        confidence_level=request.confidence_level,
    )
    
    return _format_test_result(result)


@router.post("/christoffersen", response_model=ChristoffersenTestResponse)
async def run_christoffersen_tests(request: ChristoffersenTestRequest):
    """
    Run Christoffersen Tests (Independence + Conditional Coverage)
    
    **Independence Test:** Tests if exceptions are independent (no clustering)
    
    **Conditional Coverage Test:** Joint test of correct coverage AND independence
    
    **Distribution:** Chi-squared(1) for independence, Chi-squared(2) for CC
    """
    exceptions = np.array(request.exceptions, dtype=bool)
    
    ind_result = var_backtesting_service._christoffersen_independence_test(
        exceptions=exceptions,
        confidence_level=request.confidence_level,
    )
    
    cc_result = var_backtesting_service._christoffersen_conditional_coverage_test(
        exceptions=exceptions,
        n_observations=len(exceptions),
        confidence_level=request.confidence_level,
    )
    
    return ChristoffersenTestResponse(
        independence_test=_format_test_result(ind_result),
        conditional_coverage_test=_format_test_result(cc_result),
    )


@router.post("/basel-traffic-light", response_model=BaselTrafficLightResponse)
async def get_basel_traffic_light(request: BaselTrafficLightRequest):
    """
    Get Basel III Traffic Light Zone
    
    **Zones:**
    - Green (0-4 exceptions): Model performing well
    - Yellow (5-9 exceptions): Model needs review
    - Red (10+ exceptions): Model rejected
    
    **Multipliers:**
    - Green: 2.0x
    - Yellow: 2.5x - 3.5x (sliding scale)
    - Red: 4.0x
    """
    result = var_backtesting_service._basel_traffic_light(
        n_exceptions=request.n_exceptions,
        n_observations=request.n_observations,
        confidence_level=request.confidence_level,
    )
    
    return BaselTrafficLightResponse(
        zone=result.zone.value,
        n_exceptions=result.n_exceptions,
        n_observations=result.n_observations,
        confidence_level=result.confidence_level,
        multiplier=result.multiplier,
        status=result.status.value,
        description=result.description,
        required_action=result.required_action,
        next_review_date=str(result.next_review_date),
    )


@router.get("/report/{policy_id}", response_model=RegulatoryReportResponse)
async def generate_regulatory_report(
    policy_id: str,
    prepared_by: str = Query(default="Risk Management System"),
    reviewed_by: str = Query(default="Chief Risk Officer"),
    approved_by: str = Query(default="Board Risk Committee"),
):
    """
    Generate regulatory report for SUSEP submission
    
    **Report Includes:**
    - Executive summary
    - Statistical test results
    - Basel III Traffic Light
    - SUSEP compliance assessment
    - Recommendations and required actions
    
    **Format:** JSON (exportable to PDF)
    """
    # Find latest result for policy
    policy_results = [
        r for r in var_backtesting_service.results_history
        if r.policy_id == policy_id
    ]
    
    if not policy_results:
        raise HTTPException(
            status_code=404,
            detail=f"No backtest results found for policy {policy_id}",
        )
    
    # Get latest result
    result = policy_results[-1]
    
    # Generate report
    report = var_backtesting_service.generate_regulatory_report(
        result=result,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        approved_by=approved_by,
    )
    
    return RegulatoryReportResponse(
        report_id=report.report_id,
        policy_id=report.policy_id,
        report_type=report.report_type,
        generated_at=report.generated_at,
        test_period=report.test_period,
        summary=report.summary,
        statistical_tests=report.statistical_tests,
        basel_traffic_light=report.basel_traffic_light,
        susep_compliance=report.susep_compliance,
        recommendations=report.recommendations,
        required_actions=report.required_actions,
        prepared_by=report.prepared_by,
        reviewed_by=report.reviewed_by,
        approved_by=report.approved_by,
    )


@router.get("/history")
async def get_backtest_history(
    policy_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
):
    """
    Get VaR backtesting history
    
    **Filters:**
    - policy_id: Filter by specific policy
    - limit: Maximum number of results to return
    """
    results = var_backtesting_service.results_history
    
    if policy_id:
        results = [r for r in results if r.policy_id == policy_id]
    
    # Sort by generation timestamp (newest first)
    results = sorted(results, key=lambda r: r.generation_timestamp, reverse=True)
    
    # Limit results
    results = results[:limit]
    
    return {
        "count": len(results),
        "results": [
            {
                "policy_id": r.policy_id,
                "test_period": {
                    "start": str(r.test_period_start),
                    "end": str(r.test_period_end),
                },
                "n_observations": r.n_observations,
                "confidence_level": r.confidence_level,
                "total_exceptions": r.total_exceptions,
                "exception_rate": r.exception_rate,
                "traffic_light_zone": r.traffic_light_zone.value,
                "regulatory_status": r.regulatory_status.value,
                "generation_timestamp": r.generation_timestamp,
            }
            for r in results
        ],
    }


@router.post("/generate-synthetic", response_model=GenerateSyntheticDataResponse)
async def generate_synthetic_data(request: GenerateSyntheticDataRequest):
    """
    Generate synthetic VaR backtesting data for testing
    
    **Use Cases:**
    - Testing backtesting framework
    - Training and education
    - Demonstrating model behavior
    
    **Parameters:**
    - var_model_bias: Negative = underestimation, Positive = overestimation
    - clustering_factor: Add clustering to exceptions (GARCH-like behavior)
    """
    # Set seed if provided
    if request.seed:
        np.random.seed(request.seed)
    
    n = request.n_observations
    confidence_level = request.confidence_level
    expected_exception_rate = 1 - confidence_level
    
    # Generate base losses (lognormal distribution)
    base_losses = np.random.lognormal(mean=10, sigma=0.5, size=n)
    
    # Generate VaR predictions
    var_base = np.percentile(base_losses, int(confidence_level * 100))
    var_predictions = np.ones(n) * var_base
    
    # Apply bias to VaR model
    if request.var_model_bias != 0:
        var_predictions *= (1 + request.var_model_bias)
    
    # Generate exceptions
    exceptions = (base_losses > var_predictions).astype(int)
    
    # Add clustering if requested
    if request.clustering_factor > 0:
        # Simple clustering: if exception occurred, higher probability of another
        clustered_exceptions = exceptions.copy()
        for i in range(1, n):
            if clustered_exceptions[i - 1] == 1:
                # Higher probability of exception after exception
                if np.random.random() < request.clustering_factor:
                    clustered_exceptions[i] = 1
        
        # Regenerate losses to match clustered exceptions
        for i in range(n):
            if clustered_exceptions[i] == 1:
                base_losses[i] = var_predictions[i] * np.random.uniform(1.1, 2.0)
            else:
                base_losses[i] = var_predictions[i] * np.random.uniform(0.1, 0.9)
        
        exceptions = clustered_exceptions
    
    # Calculate statistics
    n_exceptions = int(np.sum(exceptions))
    expected_exceptions = int(n * expected_exception_rate)
    
    return GenerateSyntheticDataResponse(
        n_observations=n,
        confidence_level=confidence_level,
        historical_losses=base_losses.tolist()[:100],  # Return first 100 for brevity
        var_predictions=var_predictions.tolist()[:100],
        exceptions=exceptions.tolist()[:100],
        n_exceptions=n_exceptions,
        expected_exceptions=expected_exceptions,
        metadata={
            "var_model_bias": request.var_model_bias,
            "clustering_factor": request.clustering_factor,
            "seed": request.seed,
            "full_data_available": True,
        },
    )


@router.get("/methods")
async def get_available_methods():
    """
    Get available backtesting methods and tests
    """
    return {
        "tests": [
            {
                "name": "Kupiec POF Test",
                "type": "proportion_of_failures",
                "null_hypothesis": "Exception rate = expected rate",
                "alternative_hypothesis": "Exception rate ≠ expected rate",
                "distribution": "Chi-squared(1)",
                "regulatory_compliance": ["SUSEP", "Basel III", "Solvency II"],
            },
            {
                "name": "Christoffersen Independence Test",
                "type": "independence",
                "null_hypothesis": "Exceptions are independent",
                "alternative_hypothesis": "Exceptions show clustering",
                "distribution": "Chi-squared(1)",
                "regulatory_compliance": ["SUSEP", "Basel III", "Solvency II"],
            },
            {
                "name": "Christoffersen Conditional Coverage Test",
                "type": "conditional_coverage",
                "null_hypothesis": "Correct coverage AND independence",
                "alternative_hypothesis": "Incorrect coverage OR dependence",
                "distribution": "Chi-squared(2)",
                "regulatory_compliance": ["SUSEP", "Basel III", "Solvency II"],
            },
            {
                "name": "Basel III Traffic Light",
                "type": "traffic_light_system",
                "zones": {
                    "green": {"max_exceptions": 4, "multiplier": 2.0},
                    "yellow": {"max_exceptions": 9, "multiplier": "2.5-3.5"},
                    "red": {"min_exceptions": 10, "multiplier": 4.0},
                },
                "regulatory_compliance": ["Basel III"],
            },
        ],
        "minimum_history": {
            "basel_iii": {"days": 252, "years": 1},
            "recommended": {"days": 504, "years": 2},
            "susep_full": {"days": 2520, "years": 10},
        },
        "confidence_levels": [0.90, 0.95, 0.99],
        "significance_level": 0.05,
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _format_test_result(result) -> dict:
    """Format test result for JSON response"""
    if result is None:
        return None
    
    return {
        "test_name": result.test_name,
        "test_type": result.test_type,
        "statistic": result.statistic,
        "p_value": result.p_value,
        "critical_value": result.critical_value,
        "passed": result.passed,
        "null_hypothesis": result.null_hypothesis,
        "alternative_hypothesis": result.alternative_hypothesis,
        "significance_level": result.significance_level,
        "details": result.details,
    }

"""
API Router for Dynamic Insurance Analysis and Pricing
Implements advanced dynamic evaluation system with profitability tracking and portfolio optimization.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.dynamic_insurance_analysis_service import (
    calculate_dynamic_premium,
    analyze_policy_profitability,
    get_profitability_report,
    optimize_portfolio_composition,
    get_dynamic_pricing_factors,
    add_policy_data
)

router = APIRouter()

@router.post("/dynamic-premium")
async def calculate_dynamic_premium_endpoint(
    coverage_amount: float = Query(..., gt=0, description="Coverage amount"),
    base_loading_factor: float = Query(0.20, ge=0, le=1, description="Base loading factor"),
    risk_factors: Dict[str, float] = None
):
    """
    Calculate dynamic premium with comprehensive profitability analysis.
    Implements: Dynamic pricing = Base_rate * (1 + risk_adjustment) * market_multiplier
    with profitability optimization and portfolio risk management.
    """
    if risk_factors is None:
        risk_factors = {}
    
    try:
        result = calculate_dynamic_premium(
            coverage_amount=coverage_amount,
            risk_factors=risk_factors,
            base_loading_factor=base_loading_factor
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Premium calculation failed: {str(e)}")

@router.post("/policy-profitability/{policy_id}")
async def analyze_policy_profitability_endpoint(policy_id: str):
    """
    Analyze profitability of a specific policy with detailed metrics.
    """
    try:
        result = analyze_policy_profitability(policy_id)
        # Convert dataclass to dict for JSON serialization
        return {
            'policy_id': result.policy_id,
            'premium': result.premium,
            'expected_claims': result.expected_claims,
            'actual_claims': result.actual_claims,
            'profit_margin': result.profit_margin,
            'risk_score': result.risk_score,
            'profitability_score': result.profitability_score,
            'coverage_amount': result.coverage_amount,
            'duration_months': result.duration_months,
            'portfolio_contribution': result.portfolio_contribution
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Policy analysis failed: {str(e)}")

@router.get("/profitability-report")
async def get_profitability_report_endpoint():
    """
    Generate comprehensive profitability report with portfolio and policy level analysis.
    """
    try:
        return get_profitability_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/portfolio-optimization")
async def optimize_portfolio_composition_endpoint():
    """
    Optimize portfolio composition for maximum profitability.
    """
    try:
        return optimize_portfolio_composition()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio optimization failed: {str(e)}")

@router.post("/add-policy-data")
async def add_policy_data_endpoint(
    policy_id: str = Query(..., description="Unique policy identifier"),
    premium: float = Query(..., ge=0, description="Premium charged"),
    expected_claims: float = Query(..., ge=0, description="Expected claims amount"),
    coverage_amount: float = Query(..., gt=0, description="Total coverage amount"),
    duration_months: int = Query(12, ge=1, le=120, description="Policy duration in months"),
    actual_claims: float = Query(0.0, ge=0, description="Actual claims paid"),
    risk_factors: Dict[str, float] = None
):
    """
    Add policy data for analysis and learning.
    """
    if risk_factors is None:
        risk_factors = {}
    
    try:
        add_policy_data(
            policy_id=policy_id,
            premium=premium,
            expected_claims=expected_claims,
            coverage_amount=coverage_amount,
            risk_factors=risk_factors,
            duration_months=duration_months,
            actual_claims=actual_claims
        )
        return {
            'message': 'Policy data added successfully',
            'policy_id': policy_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add policy data: {str(e)}")

@router.post("/dynamic-pricing-factors")
async def get_dynamic_pricing_factors_endpoint(risk_profile: Dict[str, float] = None):
    """
    Get all factors that influence dynamic pricing for a specific risk profile.
    """
    if risk_profile is None:
        risk_profile = {}
    
    try:
        return get_dynamic_pricing_factors(risk_profile)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get pricing factors: {str(e)}")

@router.get("/dynamic-analysis-info")
async def dynamic_analysis_info():
    """
    Get information about the dynamic insurance analysis capabilities.
    """
    return {
        "description": "Dynamic Insurance Analysis and Pricing API",
        "methods": [
            "calculate_dynamic_premium: Calculate premium with profitability analysis",
            "analyze_policy_profitability: Detailed policy profitability analysis", 
            "get_profitability_report: Comprehensive portfolio report",
            "optimize_portfolio_composition: Portfolio optimization recommendations",
            "add_policy_data: Add policy data for ongoing analysis",
            "get_dynamic_pricing_factors: Get pricing factor breakdown"
        ],
        "features": [
            "Dynamic pricing based on risk, market conditions, and portfolio performance",
            "Real-time profitability tracking at policy and portfolio levels", 
            "Portfolio optimization recommendations",
            "Competitive positioning analysis",
            "Market condition adjustments",
            "Risk-adjusted premium calculations"
        ]
    }
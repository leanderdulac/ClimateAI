"""
API Router for Operating Costs Calculation Service
Implements: CO = (Custo_subscrição + Custo_sinistros + Custo_admin) / Prêmio_emitido
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.operating_costs_service import (
    PolicyDetails,
    OperatingCostResult,
    PortfolioOperatingCosts,
    calculate_operating_costs,
    calculate_portfolio_operating_costs,
    calculate_cost_efficiency_improvement,
    calculate_breakeven_premium
)

router = APIRouter()

@router.post("/operating-costs/calculate-single")
async def calculate_single_operating_costs_endpoint(
    policy_id: str = Query(..., description="Unique policy identifier"),
    premium_issued: float = Query(..., gt=0, description="Premium amount issued"),
    processing_method: str = Query("automated", description="Processing method: 'automated' or 'manual'"),
    risk_category: str = Query("standard", description="Risk category: 'low', 'standard', 'high', 'special'"),
    coverage_type: str = Query("property", description="Coverage type: 'property', 'liability', 'vehicle', etc."),
    policy_age_months: int = Query(0, ge=0, description="Policy age in months"),
    claim_history_count: int = Query(0, ge=0, description="Number of past claims"),
    automated_processing_enabled: bool = Query(True, description="Whether automated processing is enabled")
):
    """
    Calculate operating costs for a single policy using the formula:
    CO = (Custo_subscrição + Custo_sinistros + Custo_admin) / Prêmio_emitido
    """
    try:
        # Validate inputs
        valid_processing_methods = ["automated", "manual"]
        if processing_method.lower() not in valid_processing_methods:
            raise HTTPException(
                status_code=400, 
                detail=f"processing_method must be one of: {valid_processing_methods}"
            )
        
        valid_risk_categories = ["low", "standard", "high", "special"]
        if risk_category.lower() not in valid_risk_categories:
            raise HTTPException(
                status_code=400,
                detail=f"risk_category must be one of: {valid_risk_categories}"
            )
        
        # Create policy details
        policy_details = PolicyDetails(
            policy_id=policy_id,
            premium_issued=premium_issued,
            processing_method=processing_method,
            risk_category=risk_category,
            coverage_type=coverage_type,
            policy_age_months=policy_age_months,
            claim_history_count=claim_history_count,
            automated_processing_enabled=automated_processing_enabled
        )
        
        # Calculate operating costs
        result = calculate_operating_costs(policy_details)
        
        return {
            "operating_cost_ratio": result.operating_cost_ratio,
            "subscription_cost": result.subscription_cost,
            "claims_cost": result.claims_cost,
            "admin_cost": result.admin_cost,
            "premium_issued": result.premium_issued,
            "processing_method": result.processing_method,
            "risk_category": result.risk_category,
            "cost_breakdown": result.cost_breakdown,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "policy_id": policy_details.policy_id,
            "cost_components_percentage": {
                "subscription_percentage": (result.subscription_cost / result.premium_issued) * 100 if result.premium_issued > 0 else 0,
                "claims_percentage": (result.claims_cost / result.premium_issued) * 100 if result.premium_issued > 0 else 0,
                "admin_percentage": (result.admin_cost / result.premium_issued) * 100 if result.premium_issued > 0 else 0,
                "total_cost_percentage": result.operating_cost_ratio * 100
            }
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operating cost calculation failed: {str(e)}")

@router.post("/operating-costs/portfolio-analysis")
async def portfolio_operating_costs_endpoint(
    policy_ids: List[str] = Query(..., description="List of policy IDs"),
    premium_values: List[float] = Query(..., description="List of premium values for each policy"),
    processing_methods: List[str] = Query(None, description="List of processing methods (default: automated)"),
    risk_categories: List[str] = Query(None, description="List of risk categories (default: standard)"),
    coverage_types: List[str] = Query(None, description="List of coverage types (default: property)"),
    policy_ages_months: List[int] = Query(None, description="List of policy ages in months (default: 0)"),
    claim_history_counts: List[int] = Query(None, description="List of claim history counts (default: 0)"),
    automated_processing_flags: List[bool] = Query(None, description="List of automated processing flags (default: True)")
):
    """
    Calculate operating costs for a portfolio of policies
    """
    try:
        # Validate input lengths
        n_policies = len(policy_ids)
        if not all(len(lst) == n_policies for lst in [premium_values] if lst is not None):
            raise HTTPException(status_code=400, detail="All required parameter lists must have the same length")
        
        if n_policies == 0:
            raise HTTPException(status_code=400, detail="Must provide at least one policy")
        
        # Set default values if not provided
        if processing_methods is None:
            processing_methods = ["automated"] * n_policies
        if risk_categories is None:
            risk_categories = ["standard"] * n_policies
        if coverage_types is None:
            coverage_types = ["property"] * n_policies
        if policy_ages_months is None:
            policy_ages_months = [0] * n_policies
        if claim_history_counts is None:
            claim_history_counts = [0] * n_policies
        if automated_processing_flags is None:
            automated_processing_flags = [True] * n_policies
        
        # Validate lengths
        if not all(len(lst) == n_policies for lst in [processing_methods, risk_categories, 
                                                     coverage_types, policy_ages_months, 
                                                     claim_history_counts, automated_processing_flags]):
            raise HTTPException(status_code=400, detail="All optional parameter lists must have the same length as required lists")
        
        # Create list of policy details
        policies = []
        for i in range(n_policies):
            policy = PolicyDetails(
                policy_id=policy_ids[i],
                premium_issued=premium_values[i],
                processing_method=processing_methods[i],
                risk_category=risk_categories[i],
                coverage_type=coverage_types[i],
                policy_age_months=policy_ages_months[i],
                claim_history_count=claim_history_counts[i],
                automated_processing_enabled=automated_processing_flags[i]
            )
            policies.append(policy)
        
        # Calculate portfolio operating costs
        result = calculate_portfolio_operating_costs(policies)
        
        return {
            "total_premium_issued": result.total_premium_issued,
            "total_subscription_costs": result.total_subscription_costs,
            "total_claims_processing_costs": result.total_claims_processing_costs,
            "total_administration_costs": result.total_administration_costs,
            "average_operating_cost_ratio": result.average_operating_cost_ratio,
            "policy_count": result.policy_count,
            "portfolio_cost_breakdown": result.portfolio_cost_breakdown,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "cost_percentage_summary": {
                "subscription_cost_percentage": (result.total_subscription_costs / result.total_premium_issued) * 100 if result.total_premium_issued > 0 else 0,
                "claims_cost_percentage": (result.total_claims_processing_costs / result.total_premium_issued) * 100 if result.total_premium_issued > 0 else 0,
                "admin_cost_percentage": (result.total_administration_costs / result.total_premium_issued) * 100 if result.total_premium_issued > 0 else 0,
                "average_cost_percentage": result.average_operating_cost_ratio * 100
            }
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio operating cost calculation failed: {str(e)}")

@router.post("/operating-costs/efficiency-improvement-plan")
async def cost_efficiency_improvement_plan_endpoint(
    current_operating_cost: float = Query(..., ge=0, le=1, description="Current operating cost ratio (0-1)"),
    target_operating_cost: float = Query(..., ge=0, le=1, description="Target operating cost ratio (0-1)"),
    improvement_timeline_months: int = Query(12, ge=1, le=60, description="Timeline for improvement in months")
):
    """
    Generate a plan to improve operating cost efficiency
    """
    try:
        result = calculate_cost_efficiency_improvement(
            current_operating_cost=current_operating_cost,
            target_operating_cost=target_operating_cost,
            improvement_timeline_months=improvement_timeline_months
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost efficiency improvement plan calculation failed: {str(e)}")

@router.post("/operating-costs/breakeven-premium")
async def calculate_breakeven_premium_endpoint(
    expected_claims: float = Query(..., ge=0, description="Expected claims amount"),
    risk_factor_climatic: float = Query(0.1, ge=0, le=1, description="Climatic risk factor (0-1)"),
    risk_factor_economic: float = Query(0.1, ge=0, le=1, description="Economic risk factor (0-1)"),
    risk_factor_location: float = Query(0.1, ge=0, le=1, description="Location risk factor (0-1)"),
    target_operating_margin: float = Query(0.1, ge=0, le=0.5, description="Target operating margin after costs (0-0.5)")
):
    """
    Calculate breakeven premium that accounts for operating costs
    """
    try:
        # Create risk assessment dictionary
        risk_assessment = {
            'expected_claims': expected_claims,
            'risk_factor_climatic': risk_factor_climatic,
            'risk_factor_economic': risk_factor_economic,
            'risk_factor_location': risk_factor_location
        }
        
        breakeven_premium = calculate_breakeven_premium(
            risk_assessment=risk_assessment,
            target_operating_margin=target_operating_margin
        )
        
        return {
            "breakeven_premium": breakeven_premium,
            "expected_claims": expected_claims,
            "target_operating_margin": target_operating_margin,
            "risk_assessment": risk_assessment,
            "operating_cost_ratio_factor": 0.25,  # Estimated using default
            "calculation_timestamp": datetime.now().isoformat(),
            "premium_loading": breakeven_premium - expected_claims if breakeven_premium > expected_claims else expected_claims * 0.2  # Estimated loading
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Breakeven premium calculation failed: {str(e)}")

@router.get("/operating-costs/info")
async def operating_costs_info():
    """
    Get information about the operating costs calculation service
    """
    return {
        "description": "Operating Costs Calculation Service",
        "formula": "CO = (Custo_subscrição + Custo_sinistros + Custo_admin) / Prêmio_emitido",
        "components": {
            "custo_subscrição": "R$ 150 per policy (automated) or R$ 450 (manual)",
            "custo_sinistros": "0.08 × Prêmio (for fraud detection, processing)",
            "custo_admin": "0.12 × Prêmio (for technology, compliance)"
        },
        "methodology": "Insurance Operating Costs Analysis Framework",
        "features": [
            "Single policy operating cost calculation",
            "Portfolio-level operating cost aggregation", 
            "Cost efficiency improvement planning",
            "Breakeven premium calculation with operating costs",
            "Risk category and coverage type adjustments",
            "Age-based cost modifications"
        ],
        "processing_methods": {
            "automated": {
                "cost": "R$ 150 per policy",
                "description": "Fully automated processing with minimal human intervention"
            },
            "manual": {
                "cost": "R$ 450 per policy",
                "description": "Manual processing with human review and approval"
            }
        },
        "risk_categories": {
            "low": {"multiplier": 0.8, "description": "Lower costs for low-risk policies"},
            "standard": {"multiplier": 1.0, "description": "Standard costs for typical policies"},
            "high": {"multiplier": 1.2, "description": "Higher costs for high-risk policies"},
            "special": {"multiplier": 1.5, "description": "Highest costs for special risk policies"}
        },
        "default_rates": {
            "claims_processing_rate": 0.08,  # 8%
            "administrative_rate": 0.12     # 12%
        },
        "efficiency_factor": 0.95,  # 5% efficiency gain
        "applications": [
            "Pricing optimization with operating cost inclusion",
            "Portfolio profitability analysis",
            "Cost structure evaluation",
            "Efficiency improvement planning",
            "Breakeven analysis for new products"
        ]
    }
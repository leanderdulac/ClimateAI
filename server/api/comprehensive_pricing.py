"""
API Router for Comprehensive Pricing Service
Implements: Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda

Where:
- Ajuste_oferta_demanda = f(concentração_zoneamento, capacidade_retida)
- concentração_zoneamento = Σ_{apólices_na_ZCR} (Prêmio_i / Capital_livre)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.comprehensive_pricing_service import (
    PolicyPricingInput,
    calculate_comprehensive_premium,
    calculate_operating_costs,
    calculate_profitability_analysis,
    calculate_supply_demand_adjustment,
    calculate_zone_concentration_ratio,
)

router = APIRouter()


@router.post("/comprehensive-pricing/calculate")
async def calculate_comprehensive_premium_endpoint(
    policy_id: str = Query(..., description="Unique policy identifier"),
    pure_theoretical_premium: float = Query(
        ..., gt=0, description="Pure theoretical premium (PTP)"
    ),
    loading_margin: float = Query(0.10, description="Loading Margin (ML)"),
    total_risk_factor: float = Query(0.05, description="Total Risk factor (TR)"),
    climate_change_factor: float = Query(
        0.02, description="Climate Change factor (CC)"
    ),
    free_capital: float = Query(..., gt=0, description="Free capital of the insurer"),
    zone_policies_premiums: List[float] = Query(
        [], description="Premiums of all policies in the same zone"
    ),
):
    """
    Calculate comprehensive premium using the integrated formula:
    Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda
    """
    try:
        # Create policy pricing input
        pricing_input = PolicyPricingInput(
            policy_id=policy_id,
            pure_theoretical_premium=pure_theoretical_premium,
            loading_margin=loading_margin,
            total_risk_factor=total_risk_factor,
            climate_change_factor=climate_change_factor,
            zone_policies_premiums=zone_policies_premiums,
            free_capital=free_capital,
        )

        # Calculate comprehensive premium
        result = await calculate_comprehensive_premium(pricing_input)

        # Calculate zone concentration ratio
        zone_concentration_ratio = calculate_zone_concentration_ratio(
            zone_policies_premiums=zone_policies_premiums, free_capital=free_capital
        )

        # Calculate supply-demand adjustment
        supply_demand_adjustment = calculate_supply_demand_adjustment(
            zone_concentration_ratio
        )

        return {
            "final_premium": result.final_premium,
            "pure_theoretical_premium": result.pure_theoretical_premium,
            "loading_margin_component": result.loading_margin_component,
            "total_risk_component": result.total_risk_component,
            "climate_change_component": result.climate_change_component,
            "supply_demand_adjustment": supply_demand_adjustment,
            "zone_concentration_ratio": zone_concentration_ratio,
            "free_capital_used": free_capital,
            "profitability_metrics": result.profitability_metrics,
            "calculation_method": result.calculation_method,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "pricing_formula_breakdown": {
                "step1_ptp": pure_theoretical_premium,
                "step2_with_ml": pure_theoretical_premium * (1 + loading_margin),
                "step3_with_tr": pure_theoretical_premium
                * (1 + loading_margin)
                * (1 + total_risk_factor),
                "step4_with_cc": pure_theoretical_premium
                * (1 + loading_margin)
                * (1 + total_risk_factor)
                * (1 + climate_change_factor),
                "step5_with_adjustment": result.final_premium,  # Final with supply-demand adjustment
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comprehensive premium calculation failed: {str(e)}",
        )


@router.post("/comprehensive-pricing/zone-analysis")
async def calculate_zone_concentration_endpoint(
    zone_id: str = Query(..., description="Zone identifier"),
    zone_policies_premiums: List[float] = Query(
        ..., min_items=1, description="Premiums of policies in the zone"
    ),
    free_capital: float = Query(..., gt=0, description="Free capital of the insurer"),
):
    """
    Calculate zone concentration metrics and supply-demand adjustment factor
    """
    try:
        # Calculate concentration ratio
        concentration_ratio = calculate_zone_concentration_ratio(
            zone_policies_premiums=zone_policies_premiums, free_capital=free_capital
        )

        # Calculate supply-demand adjustment
        adjustment_factor = calculate_supply_demand_adjustment(concentration_ratio)

        return {
            "zone_id": zone_id,
            "total_zone_premiums": sum(zone_policies_premiums),
            "free_capital": free_capital,
            "zone_concentration_ratio": concentration_ratio,
            "concentration_adjustment_factor": adjustment_factor,
            "policies_in_zone": len(zone_policies_premiums),
            "calculation_timestamp": datetime.now().isoformat(),
            "recommendations": [
                (
                    "High concentration (>25%) - Apply capacity loading of 30%"
                    if concentration_ratio > 0.25
                    else ""
                ),
                (
                    "Low concentration (<10%) - Apply diversification discount of 10%"
                    if concentration_ratio < 0.10
                    else ""
                ),
                (
                    "Acceptable concentration level - Maintain standard pricing"
                    if 0.10 <= concentration_ratio <= 0.25
                    else ""
                ),
            ],
            "formula_components": {
                "concentração_zoneamento": f"Σ(Premium_i) / Capital_livre = {sum(zone_policies_premiums)} / {free_capital} = {concentration_ratio:.6f}",
                "limite_concentração_alta": 0.25,
                "limite_concentração_baixa": 0.10,
                "ajuste_para_alta_concentração": 1.30,
                "ajuste_para_baixa_concentração": 0.90,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Zone concentration calculation failed: {str(e)}"
        )


@router.post("/comprehensive-pricing/zone-optimization")
async def optimize_pricing_by_zone_endpoint():
    """
    Optimize pricing by zone based on concentration levels and risk factors
    """
    raise HTTPException(
        status_code=501, detail="Endpoint not implemented with current service methods"
    )


@router.get("/comprehensive-pricing/info")
async def comprehensive_pricing_info():
    """
    Get information about the comprehensive pricing calculation service
    """
    return {
        "description": "Comprehensive Pricing Calculation Service",
        "main_formula": "Prêmio = PTP × (1 + ML) × (1 + TR) × (1 + CC) × Ajuste_oferta_demanda",
        "components": {
            "PTP": "Pure Theoretical Premium (base premium based on expected claims)",
            "ML": "Loading Margin (risk loading)",
            "TR": "Total Risk factor (combined risk adjustment)",
            "CC": "Climate Change factor (adjustment for climate risk)",
            "Ajuste_oferta_demanda": "Supply-demand adjustment based on market concentration",
        },
        "supply_demand_component": {
            "formula": "Ajuste_oferta_demanda = f(concentração_zoneamento, capacidade_retida)",
            "concentration_formula": "concentração_zoneamento = Σ_{apólices_na_ZCR} (Prêmio_i / Capital_livre)",
            "adjustment_rules": {
                "concentration_above_25": {
                    "condition": "concentração > 25%",
                    "adjustment": "1.30 (capacity loading)",
                    "reason": "High market concentration requires capacity loading",
                },
                "concentration_below_10": {
                    "condition": "concentração < 10%",
                    "adjustment": "0.90 (diversification discount)",
                    "reason": "Low concentration allows diversification discount",
                },
                "neutral_concentration": {
                    "condition": "10% ≤ concentração ≤ 25%",
                    "adjustment": "1.00 (no adjustment)",
                    "reason": "Acceptable concentration range",
                },
            },
        },
        "methodology": "Integrated Climate Insurance Pricing Framework",
        "features": [
            "Comprehensive premium calculation with all factors",
            "Zone-based concentration analysis",
            "Supply-demand adjustment based on market factors",
            "Profitability optimization",
            "Capital adequacy considerations",
            "Climate risk integration",
        ],
        "integration": "Connects with all other risk assessment services to provide final pricing",
        "risk_integration": [
            "Physical Risk (R_físico)",
            "Transition Risk (R_transição)",
            "Concentration Risk (R_concentração)",
            "Mitigation Effects (M_mitigação)",
            "Final SCR Score",
            "LEI (Loss Expectancy Index)",
            "Capital Surplus Requirements",
            "Operating Costs",
            "Investment Returns",
        ],
        "pricing_factors": {
            "loading_margins": "Up to 30% additional for high-risk scenarios",
            "climate_adjustments": "Based on projected climate impacts",
            "demand_supply_factor": "Adjusts based on market concentration",
            "capital_efficiency": "Incorporates available capital constraints",
        },
        "default_thresholds": {
            "low_concentration": "10%",
            "medium_concentration": "20%",
            "high_concentration": "25%",
            "critical_concentration": "30%",
        },
    }

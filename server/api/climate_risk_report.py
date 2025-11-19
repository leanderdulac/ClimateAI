"""
API Router for Climate Risk Report Generation Service
Generates comprehensive climate risk analysis reports in the standardized format
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.climate_risk_report_service import (
    ClimateRiskComponents,
    generate_policy_analysis_report,
    generate_policy_comparison_report,
)

router = APIRouter()


@router.post("/policy-analysis")
async def generate_policy_analysis_endpoint(
    policy_id: str = Query(..., description="Unique policy identifier"),
    physical_risk: float = Query(..., ge=0, le=1000, description="Physical risk score"),
    transition_risk: float = Query(
        ..., ge=0, le=1000, description="Transition risk score"
    ),
    concentration_risk: float = Query(
        ..., ge=0, le=1000, description="Concentration risk score"
    ),
    mitigation_effect: float = Query(
        ..., ge=0, le=1000, description="Mitigation effect (negative value)"
    ),
    expected_claims: float = Query(
        ..., gt=0, description="Expected claims amount (R$)"
    ),
    coverage_amount: float = Query(..., gt=0, description="Coverage amount (R$)"),
    zone_concentration: float = Query(
        0.22, ge=0, le=1, description="Concentration in the zone (0-1)"
    ),
    temperature_projection: float = Query(
        1.8, description="Temperature increase projection by 2050 (ΔT in °C)"
    ),
    risk_increase_percentage: float = Query(
        129.0, description="Projected risk increase percentage by 2050"
    ),
    implemented_mitigation_measures: str = Query(
        "[]", description="JSON string of implemented mitigation measures"
    ),
    mitigation_impact: str = Query(
        "{}", description="JSON string of mitigation impact"
    ),
):
    """
    Generate comprehensive climate risk analysis report in standard format
    """
    try:
        # Convert JSON strings to Python objects
        try:
            implemented_measures_list = json.loads(implemented_mitigation_measures)
            mitigation_impact_dict = json.loads(mitigation_impact)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in mitigation parameters: {str(e)}",
            )

        # Create risk components object
        risk_components = ClimateRiskComponents(
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=concentration_risk,
            mitigation_effect=mitigation_effect,
            expected_claims=expected_claims,
        )

        # Create climate projections dict
        climate_projections = {
            "temperature_increase_2050": temperature_projection,
            "risk_increase_percentage": risk_increase_percentage,
            "year": 2050,
        }

        # Generate the report
        report = generate_policy_analysis_report(
            policy_id=policy_id,
            risk_components=risk_components,
            expected_claims=expected_claims,
            coverage_amount=coverage_amount,
            zone_concentration=zone_concentration,
            climate_projections=climate_projections,
            implemented_mitigation_measures=implemented_measures_list,
            mitigation_impact=mitigation_impact_dict,
        )

        # Convert the report to a JSON-serializable format
        return {
            "policy_id": report.policy_id,
            "risk_level": report.risk_level,
            "scr_score": report.scr_score,
            "climate_risk_breakdown": report.climate_risk_breakdown,
            "decision": report.decision,
            "decision_reason": report.decision_reason,
            "final_premium": report.final_premium,
            "standard_premium": report.standard_premium,
            "component_analysis": report.component_analysis,
            "discount_opportunities": report.discount_opportunities,
            "potential_premium": report.potential_premium,
            "alerts": report.alerts,
            "next_review_date": report.next_review_date.isoformat(),
            "calculation_timestamp": report.calculation_timestamp.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Policy analysis generation failed: {str(e)}"
        )


@router.post("/portfolio-analysis")
async def generate_portfolio_analysis_endpoint(policies_data: List[Dict[str, Any]]):
    """
    Generate comprehensive analysis for multiple policies (portfolio analysis)
    """
    try:
        # Generate portfolio comparison report
        report = generate_policy_comparison_report(policies_data)

        return report
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Portfolio analysis generation failed: {str(e)}"
        )


@router.get("/format-specification")
async def get_report_format_specification():
    """
    Get the specification and format for climate risk analysis reports
    """
    return {
        "title": "Climate Risk Analysis Report Format",
        "version": "1.0",
        "description": "Standardized format for climate risk analysis and insurance decisions",
        "format_structure": {
            "header": "APÓLICE #[policy_id] - ANÁLISE CLIMÁTICA",
            "risk_assessment": {
                "overall_risk": "RISCO CLIMÁTICO: [LEVEL] (SCR = [score]/1000)",
                "risk_breakdown": [
                    "├─ Risco físico ([type]): [score] pts [projection]",
                    "├─ Risco transição: [score] pts [details]",
                    "└─ Mitigação ativa: [reduction] pts [measures]",
                ],
            },
            "decision": "DECISÃO: [decision_type] ([reason])",
            "premium": "PRÊMIO: R$ [amount]/ano (vs. R$ [standard] padrão)",
            "detailed_breakdown": {
                "components": [
                    "├─ Perda esperada: R$ [amount]",
                    "├─ Carreg. segurança: R$ [amount] (CS=[percentage])",
                    "├─ Carreg. contingência: R$ [amount] (CCC=[percentage])",
                    "├─ Margem emissor: R$ [amount] (ML=[percentage])",
                    "├─ Retorno inv.: R$ [amount] (TR=[percentage])",
                    "├─ Carreg. cliente: R$ [amount] (CC=[percentage])",
                    "└─ Ajuste capacidade: R$ [amount] (concentração zona = [percentage])",
                ]
            },
            "discount_opportunities": {
                "title": "OPORTUNIDADES DE DESCONTO:",
                "format": [
                    "├─ [measure]: -R$ [amount]/ano",
                    "└─ [measure]: -R$ [amount]/ano",
                    "   PRÊMIO POTENCIAL: R$ [potential_amount]/ano",
                ],
            },
            "alerts": {
                "title": "ALERTAS:",
                "format": ["⚠️ [alert_message]", "⚠️ [alert_message]"],
            },
            "review_schedule": {
                "title": "PRÓXIMA REVISÃO:",
                "format": "Automática em [interval] ou se [condition]",
            },
        },
        "risk_levels": {
            "very_low": "(0-200)",
            "low": "(200-400)",
            "moderate": "(400-600)",
            "high": "(600-800)",
            "critical": "(800+)",
        },
        "component_rates": {
            "security_loading": "30% (Carreg. segurança - CS)",
            "contingency_loading": "18% (Carreg. contingência - CCC)",
            "margin_loading": "18% (Margem emissor - ML)",
            "investment_return": "5% (Retorno inv. - TR)",
            "climate_change_loading": "20% (Carreg. cliente - CC)",
            "capacity_adjustment": "Variable (Ajuste capacidade)",
        },
    }

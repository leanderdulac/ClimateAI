"""
API Router for Smart Climate Exclusions Service
Implements exclusions for:
- Eventos não-modeláveis: Terremoto induzido por clima (low confidence)
- Falha de mitigação: Se cliente não implementou medidas exigidas
- Litígio climático: Responsabilidade civil por emissões (ainda não maduro)

Plus governance recommendations:
- Aprovação manual obrigatória para SCR > 600 (não delegar totalmente à IA)
- Comitê de risco climático trimestral para revisar decisões do sistema
- Auditoria externa anual dos modelos (validação por atuárias independentes)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from middleware.auth_middleware import require_admin
from models.schemas import User
from services.smart_climate_exclusions_service import (
    ClimateExclusionType,
    GovernanceRecommendation,
    evaluate_climate_exclusions,
    get_exclusion_decision,
    get_upcoming_reviews,
    smart_exclusions_service,
    update_governance_rule,
)

router = APIRouter()


@router.post("/smart-exclusions/evaluate")
async def evaluate_climate_exclusions_endpoint(
    policy_id: str = Query(..., description="Policy identifier"),
    scr_score: float = Query(0.0, description="Climate risk score (SCR)"),
    climate_induced_seismicity_confidence: float = Query(
        0.5, ge=0, le=1, description="Climate-induced seismicity model confidence"
    ),
    litigation_maturity: float = Query(
        0.2, ge=0, le=1, description="Litigation model maturity"
    ),
    required_mitigation_measures: str = Query(
        "[]", description="JSON string of required mitigation measures"
    ),
    implemented_mitigation_measures: str = Query(
        "[]", description="JSON string of implemented mitigation measures"
    ),
):
    """
    Evaluate smart climate exclusions based on policy data
    Implements the requirements:
    - Eventos não-modeláveis: Terremoto induzido por clima (low confidence) - excluded with 500% loading
    - Falha de mitigação: Se cliente não implementou medidas exigidas - covered with 500% loading
    - Litígio climático: Responsabilidade civil por emissões (ainda não maduro) - excluded with 500% loading
    """
    try:
        import json

        # Parse JSON strings
        try:
            required_measures = json.loads(required_mitigation_measures)
            implemented_measures = json.loads(implemented_mitigation_measures)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in mitigation parameters: {str(e)}",
            )

        # Prepare climate risk factors
        climate_risk_factors = {
            "scr_score": scr_score,
            "litigation_maturity": litigation_maturity,
        }

        # Prepare mitigation status
        mitigation_status = {
            "required_measures": required_measures,
            "implemented_measures": implemented_measures,
        }

        # Prepare model confidence
        model_confidence = {
            "climate_induced_seismicity": climate_induced_seismicity_confidence
        }

        # Evaluate climate exclusions
        decision = evaluate_climate_exclusions(
            policy_id=policy_id,
            climate_risk_factors=climate_risk_factors,
            mitigation_status=mitigation_status,
            model_confidence=model_confidence,
        )

        # Format response
        excluded_risks_formatted = []
        for exclusion in decision.excluded_risks:
            excluded_risks_formatted.append(
                {
                    "exclusion_id": exclusion.exclusion_id,
                    "exclusion_type": exclusion.exclusion_type.value,
                    "risk_description": exclusion.risk_description,
                    "loading_factor": exclusion.loading_factor,
                    "confidence_level": exclusion.confidence_level,
                    "coverage_status": exclusion.coverage_status,
                    "reason": exclusion.reason,
                    "implementation_date": exclusion.implementation_date.isoformat(),
                    "review_date": exclusion.review_date.isoformat(),
                }
            )

        governance_recommendations_formatted = []
        for rule in decision.governance_recommendations:
            governance_recommendations_formatted.append(
                {
                    "rule_id": rule.rule_id,
                    "rule_type": rule.rule_type.value,
                    "trigger_condition": rule.trigger_condition,
                    "threshold_value": rule.threshold_value,
                    "required_action": rule.required_action,
                    "review_frequency": rule.review_frequency,
                    "status": rule.status,
                    "implementation_date": rule.implementation_date.isoformat(),
                }
            )

        return {
            "policy_id": decision.policy_id,
            "excluded_risks": excluded_risks_formatted,
            "coverage_status": decision.coverage_status,
            "governance_recommendations": governance_recommendations_formatted,
            "final_premium_adjustment": decision.final_premium_adjustment,
            "decision_timestamp": decision.decision_timestamp.isoformat(),
            "decision_reasons": decision.decision_reasons,
            "total_exclusions": len(excluded_risks_formatted),
            "total_governance_recommendations": len(
                governance_recommendations_formatted
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Climate exclusions evaluation failed: {str(e)}"
        )


@router.get("/smart-exclusions/decision/{policy_id}")
async def get_exclusion_decision_endpoint(policy_id: str):
    """
    Get the exclusion decision for a specific policy
    """
    try:
        decision = get_exclusion_decision(policy_id)
        if not decision:
            raise HTTPException(
                status_code=404,
                detail=f"No exclusion decision found for policy {policy_id}",
            )

        # Format response
        excluded_risks_formatted = []
        for exclusion in decision.excluded_risks:
            excluded_risks_formatted.append(
                {
                    "exclusion_id": exclusion.exclusion_id,
                    "exclusion_type": exclusion.exclusion_type.value,
                    "risk_description": exclusion.risk_description,
                    "loading_factor": exclusion.loading_factor,
                    "confidence_level": exclusion.confidence_level,
                    "coverage_status": exclusion.coverage_status,
                    "reason": exclusion.reason,
                    "implementation_date": exclusion.implementation_date.isoformat(),
                    "review_date": exclusion.review_date.isoformat(),
                }
            )

        governance_recommendations_formatted = []
        for rule in decision.governance_recommendations:
            governance_recommendations_formatted.append(
                {
                    "rule_id": rule.rule_id,
                    "rule_type": rule.rule_type.value,
                    "trigger_condition": rule.trigger_condition,
                    "threshold_value": rule.threshold_value,
                    "required_action": rule.required_action,
                    "review_frequency": rule.review_frequency,
                    "status": rule.status,
                    "implementation_date": rule.implementation_date.isoformat(),
                }
            )

        return {
            "policy_id": decision.policy_id,
            "excluded_risks": excluded_risks_formatted,
            "coverage_status": decision.coverage_status,
            "governance_recommendations": governance_recommendations_formatted,
            "final_premium_adjustment": decision.final_premium_adjustment,
            "decision_timestamp": decision.decision_timestamp.isoformat(),
            "decision_reasons": decision.decision_reasons,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Exclusion decision retrieval failed: {str(e)}"
        )


@router.get("/smart-exclusions/upcoming-reviews")
async def get_upcoming_reviews_endpoint():
    """
    Get policies and exclusions requiring upcoming reviews
    """
    try:
        upcoming_reviews = get_upcoming_reviews()

        formatted_reviews = []
        for item_id, review_date, review_type in upcoming_reviews:
            formatted_reviews.append(
                {
                    "item_id": item_id,
                    "review_date": review_date.isoformat(),
                    "review_type": review_type,
                    "days_until_review": (review_date - datetime.now()).days,
                }
            )

        return {
            "upcoming_reviews": formatted_reviews,
            "total_reviews_scheduled": len(formatted_reviews),
            "check_date": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Upcoming reviews check failed: {str(e)}"
        )


@router.post("/smart-exclusions/update-governance-rule")
async def update_governance_rule_endpoint(
    rule_id: str = Query(..., description="Rule identifier"),
    new_status: str = Query(
        ..., description="New status for the rule (active, inactive, pending)"
    ),
    current_user: User = Depends(require_admin),
):
    """
    Update the status of a governance rule
    """
    try:
        if new_status not in ["active", "inactive", "pending"]:
            raise HTTPException(
                status_code=400,
                detail="Status must be 'active', 'inactive', or 'pending'",
            )

        rule = update_governance_rule(rule_id, new_status)

        return {
            "rule_id": rule.rule_id,
            "updated_status": rule.status,
            "rule_type": rule.rule_type.value,
            "trigger_condition": rule.trigger_condition,
            "required_action": rule.required_action,
            "last_updated": rule.implementation_date.isoformat(),
            "status": "updated",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Governance rule update failed: {str(e)}"
        )


@router.get("/smart-exclusions/specification")
async def get_exclusions_specification():
    """
    Get the specification and requirements for smart climate exclusions
    """
    return {
        "title": "Smart Climate Exclusions Specification",
        "version": "1.0",
        "description": "Specification for climate risk exclusions and governance recommendations",
        "exclusion_types": {
            "evento_nao_modelavel": {
                "description": "Eventos não-modeláveis: Terremoto induzido por clima (low confidence)",
                "action": "Excluded with 500% loading",
                "condition": "Model confidence < 30%",
            },
            "falha_mitigacao": {
                "description": "Falha de mitigação: Se cliente não implementou medidas exigidas",
                "action": "Covered with 500% loading",
                "condition": "Required mitigation measures not implemented",
            },
            "litigio_climatico": {
                "description": "Litígio climático: Responsabilidade civil por emissões (ainda não maduro)",
                "action": "Excluded with 500% loading",
                "condition": "Model maturity < 40%",
            },
        },
        "governance_recommendations": [
            {
                "type": "aprovacao_manual_obrigatoria",
                "condition": "SCR > 600",
                "action": "Manual approval required, no full AI delegation",
            },
            {
                "type": "comite_risco_trimestral",
                "frequency": "quarterly",
                "action": "Climate risk committee to review system decisions",
            },
            {
                "type": "auditoria_externa_anual",
                "frequency": "annual",
                "action": "External audit of models by independent actuaries",
            },
        ],
        "loading_factors": {
            "excluded_risk": 5.0,  # 500% loading for excluded risks
            "description": "Multiplier applied to risks that are not covered normally",
        },
        "implementation_notes": [
            "Apply 500% loading factor for excluded risks",
            "Require manual approval for high-risk policies (SCR > 600)",
            "Establish quarterly climate risk committee",
            "Conduct annual external model audits",
            "Monitor model confidence levels continuously",
        ],
        "compliance_requirements": [
            "No full AI delegation for SCR > 600",
            "Quarterly governance reviews",
            "Annual actuarial validation",
            "Transparent exclusion communication",
        ],
        "risk_management_principles": [
            "Conservative approach to unmodelable risks",
            "Proper mitigation implementation verification",
            "Mature models requirement for coverage",
            "Governance oversight for high-risk decisions",
        ],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/smart-exclusions/governance-status")
async def get_governance_status():
    """
    Get the current governance status and recommendations
    """
    try:
        # Get all governance rules
        all_rules = smart_exclusions_service.governance_rules

        active_rules = [rule for rule in all_rules if rule.status == "active"]
        inactive_rules = [rule for rule in all_rules if rule.status == "inactive"]

        return {
            "governance_framework": {
                "total_rules": len(all_rules),
                "active_rules": len(active_rules),
                "inactive_rules": len(inactive_rules),
            },
            "manual_approval_trigger": f"SCR > {smart_exclusions_service.manual_approval_threshold}",
            "quarterly_committee_required": "Yes",
            "annual_external_audit_required": "Yes",
            "confidence_thresholds": {
                "low_confidence": smart_exclusions_service.low_confidence_threshold,
                "medium_confidence": smart_exclusions_service.medium_confidence_threshold,
            },
            "exclusion_loading_factor": smart_exclusions_service.default_excluded_loading_factor,
            "status_summary": {
                "manual_approval_rule": next(
                    (
                        rule
                        for rule in active_rules
                        if rule.rule_type.value == "aprovacao_manual_obrigatoria"
                    ),
                    None,
                )
                is not None,
                "quarterly_review_rule": next(
                    (
                        rule
                        for rule in active_rules
                        if rule.rule_type.value == "comite_risco_trimestral"
                    ),
                    None,
                )
                is not None,
                "annual_audit_rule": next(
                    (
                        rule
                        for rule in active_rules
                        if rule.rule_type.value == "auditoria_externa_anual"
                    ),
                    None,
                )
                is not None,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Governance status check failed: {str(e)}"
        )

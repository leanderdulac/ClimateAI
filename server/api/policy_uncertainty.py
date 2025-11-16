"""
API Router for Policy Uncertainty Clause Management
Implements the specific clause:
"O prêmio incorpora projeções climáticas com incerteza intrínseca de 35-60% para períodos >10 anos. 
O segurador reserva o direito de revisão anual conforme novos dados CMIP7 ou eventos de calibragem."
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.policy_uncertainty_service import (
    policy_uncertainty_service,
    create_uncertainty_clause,
    get_uncertainty_clause,
    update_clause_for_cmip_data,
    register_calibration_event,
    get_policies_requiring_review,
    calculate_adjusted_uncertainty
)

router = APIRouter()

@router.post("/policy-uncertainty/create-clause")
async def create_policy_uncertainty_clause(
    policy_id: str = Query(..., description="Policy identifier"),
    uncertainty_min: float = Query(0.35, ge=0, le=1, description="Minimum uncertainty percentage (0.35 = 35%)"),
    uncertainty_max: float = Query(0.60, ge=0, le=1, description="Maximum uncertainty percentage (0.60 = 60%)"),
    projection_horizon: int = Query(10, ge=1, description="Projection horizon in years (>10 years)"),
    cmip_source: str = Query("CMIP7", description="Climate model intercomparison project source")
):
    """
    Create a policy uncertainty clause with the specific language:
    "O prêmio incorpora projeções climáticas com incerteza intrínseca de 35-60% para períodos >10 anos. 
    O segurador reserva o direito de revisão anual conforme novos dados CMIP7 ou eventos de calibragem."
    """
    try:
        clause = create_uncertainty_clause(
            policy_id=policy_id,
            uncertainty_min=uncertainty_min,
            uncertainty_max=uncertainty_max,
            projection_horizon=projection_horizon,
            cmip_source=cmip_source
        )
        
        return {
            "policy_id": clause.policy_id,
            "uncertainty_range": f"{clause.uncertainty_range_min*100:.0f}-{clause.uncertainty_range_max*100:.0f}%",
            "uncertainty_range_decimal": {
                "min": clause.uncertainty_range_min,
                "max": clause.uncertainty_range_max
            },
            "projection_horizon": clause.projection_horizon,
            "cmip_source": clause.cmip_data_source,
            "annual_review_clause": clause.annual_review_clause,
            "calibration_events_enabled": clause.calibration_events_enabled,
            "clause_text": clause.clause_text,
            "creation_date": clause.creation_date.isoformat(),
            "last_updated": clause.last_updated.isoformat(),
            "next_review_date": clause.next_review_date.isoformat(),
            "status": "created"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uncertainty clause creation failed: {str(e)}")

@router.get("/policy-uncertainty/get-clause/{policy_id}")
async def get_policy_uncertainty_clause(policy_id: str):
    """
    Get the uncertainty clause details for a specific policy
    """
    try:
        clause = get_uncertainty_clause(policy_id)
        if not clause:
            raise HTTPException(status_code=404, detail=f"No uncertainty clause found for policy {policy_id}")
        
        return {
            "policy_id": clause.policy_id,
            "uncertainty_range": f"{clause.uncertainty_range_min*100:.0f}-{clause.uncertainty_range_max*100:.0f}%",
            "uncertainty_range_decimal": {
                "min": clause.uncertainty_range_min,
                "max": clause.uncertainty_range_max
            },
            "projection_horizon": clause.projection_horizon,
            "cmip_source": clause.cmip_data_source,
            "annual_review_clause": clause.annual_review_clause,
            "calibration_events_enabled": clause.calibration_events_enabled,
            "clause_text": clause.clause_text,
            "creation_date": clause.creation_date.isoformat(),
            "last_updated": clause.last_updated.isoformat(),
            "next_review_date": clause.next_review_date.isoformat(),
            "days_until_review": (clause.next_review_date - datetime.now()).days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uncertainty clause retrieval failed: {str(e)}")

@router.post("/policy-uncertainty/update-clause-cmip-data")
async def update_policy_clause_for_cmip_data(
    policy_id: str = Query(..., description="Policy identifier"),
    new_cmip_source: str = Query("CMIP7", description="New CMIP data source")
):
    """
    Update a policy's uncertainty clause when new CMIP data is released
    """
    try:
        clause = update_clause_for_cmip_data(policy_id, new_cmip_source)
        
        return {
            "policy_id": clause.policy_id,
            "updated_cmip_source": clause.cmip_data_source,
            "clause_text": clause.clause_text,
            "last_updated": clause.last_updated.isoformat(),
            "next_review_date": clause.next_review_date.isoformat(),
            "status": "updated"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Policy not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uncertainty clause update failed: {str(e)}")

@router.post("/policy-uncertainty/register-calibration-event")
async def register_calibration_event_endpoint(
    event_type: str = Query(..., description="Type of calibration event"),
    event_description: str = Query(..., description="Description of the calibration event"),
    policy_ids: List[str] = Query(..., description="List of policy IDs affected by this event"),
    impact_on_uncertainty: float = Query(0.1, ge=0, le=1, description="Impact on uncertainty (0.0 to 1.0)")
):
    """
    Register a calibration event that may trigger policy reviews
    """
    try:
        event = register_calibration_event(
            event_type=event_type,
            event_description=event_description,
            policies_affected=policy_ids,
            impact_on_uncertainty=impact_on_uncertainty
        )
        
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "event_description": event.event_description,
            "policies_affected": event.policies_affected,
            "impact_on_uncertainty": event.impact_on_uncertainty,
            "event_date": event.event_date.isoformat(),
            "triggered_review": event.triggered_review,
            "review_reason": event.review_reason,
            "status": "registered"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration event registration failed: {str(e)}")

@router.get("/policy-uncertainty/policies-requiring-review")
async def get_policies_requiring_review_endpoint():
    """
    Get list of policies that require review based on current date and calibration events
    """
    try:
        policies = get_policies_requiring_review()
        
        return {
            "policies_requiring_review": policies,
            "total_policies": len(policies),
            "check_date": datetime.now().isoformat(),
            "status": "review_ready"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policies requiring review check failed: {str(e)}")

@router.post("/policy-uncertainty/calculate-adjusted-uncertainty")
async def calculate_adjusted_uncertainty_endpoint(
    base_uncertainty: float = Query(..., ge=0, le=1, description="Base uncertainty value"),
    event_ids: List[str] = Query(..., description="List of calibration event IDs that may affect uncertainty")
):
    """
    Calculate adjusted uncertainty based on calibration events
    """
    try:
        # Get the calibration events
        calibration_events = []
        for event_id in event_ids:
            event = policy_uncertainty_service.calibration_events.get(event_id)
            if event:
                calibration_events.append(event)
        
        if not calibration_events:
            raise HTTPException(status_code=404, detail="No calibration events found for the provided IDs")
        
        adjusted_uncertainty = calculate_adjusted_uncertainty(base_uncertainty, calibration_events)
        
        return {
            "base_uncertainty": base_uncertainty,
            "adjusted_uncertainty": adjusted_uncertainty,
            "calibration_events_applied": len(calibration_events),
            "event_ids": event_ids,
            "adjustment_factor": adjusted_uncertainty / base_uncertainty if base_uncertainty > 0 else 1.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adjusted uncertainty calculation failed: {str(e)}")

@router.get("/policy-uncertainty/clause-specification")
async def get_uncertainty_clause_specification():
    """
    Get the specification and requirements for the uncertainty clause
    """
    return {
        "title": "Policy Uncertainty Clause Specification",
        "version": "1.0",
        "description": "Standard uncertainty clause for climate risk insurance policies",
        "required_clause_text": "O prêmio incorpora projeções climáticas com incerteza intrínseca de 35-60% para períodos >10 anos. O segurador reserva o direito de revisão anual conforme novos dados CMIP7 ou eventos de calibragem.",
        "parameters": {
            "uncertainty_range": "35-60% (0.35 to 0.60) for long-term projections",
            "projection_horizon": "Greater than 10 years",
            "cmip_source": "CMIP7 or future CMIP versions",
            "annual_review": "Insurance provider reserves right to annual review",
            "calibration_events": "Reviews triggered by new CMIP data or calibration events"
        },
        "compliance_requirements": [
            "Include specific percentage range (35-60%)",
            "Specify projection horizon (>10 years)",
            "Mention CMIP data source (currently CMIP7)",
            "State annual review right",
            "Reference calibration events"
        ],
        "calibration_event_types": [
            "CMIP data release",
            "Extreme weather event (model calibration)",
            "Climate model update",
            "Regulatory change",
            "Scientific discovery",
            "Data quality issue"
        ],
        "implementation_notes": [
            "Uncertainty range accounts for climate model limitations",
            "Annual review allows for updated risk assessment",
            "Calibration events enable responsive risk management",
            "CMIP source allows for model improvements over time"
        ],
        "timestamp": datetime.now().isoformat()
    }
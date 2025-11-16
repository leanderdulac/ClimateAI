"""
API Router for Policy Valuation and Recommendation Service
Implements notification system for valuable policies and interactive options
for improving policy valuation.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.policy_valuation_service import (
    policy_valuation_service,
    PolicyMetrics,
    ClimateRiskFactors,
    calculate_policy_valuation,
    get_interactive_policy_analysis,
    get_pending_notifications,
    get_policy_recommendations_summary,
    get_valuable_policies_summary,
    mark_notification_as_processed
)

router = APIRouter()

@router.post("/policy-valuation/valuate")
async def calculate_policy_valuation_endpoint(
    policy_id: str = Query(..., description="Policy identifier"),
    premium_amount: float = Query(..., gt=0, description="Premium amount in currency units"),
    expected_claims: float = Query(0.0, ge=0, description="Expected claims amount"),
    claim_frequency: float = Query(0.1, ge=0, le=1, description="Claim frequency (0-1)"),
    claim_severity: float = Query(10000.0, ge=0, description="Claim severity (average claim size)"),
    climate_risk_score: float = Query(500.0, ge=0, le=1000, description="Climate risk score (0-1000)"),
    physical_risk: float = Query(0.4, ge=0, le=1, description="Physical risk factor (0-1)"),
    transition_risk: float = Query(0.3, ge=0, le=1, description="Transition risk factor (0-1)"),
    mitigation_effectiveness: float = Query(0.6, ge=0, le=1, description="Mitigation effectiveness (0-1)"),
    model_confidence: float = Query(0.75, ge=0, le=1, description="Model confidence (0-1)"),
    concentration_risk: float = Query(0.2, ge=0, le=1, description="Concentration risk (0-1)"),
    geographic_factor: float = Query(0.5, ge=0, le=1, description="Geographic risk factor (0-1)"),
    regulatory_factor: float = Query(0.3, ge=0, le=1, description="Regulatory factor (0-1)"),
    economic_factor: float = Query(0.4, ge=0, le=1, description="Economic exposure factor (0-1)"),
    policy_value: float = Query(None, gt=0, description="Total policy value (optional)")
):
    """
    Calculate comprehensive policy valuation with intelligent weighting.
    Notifies administrator when valuable policies are identified.
    """
    try:
        metrics = PolicyMetrics(
            premium_amount=premium_amount,
            expected_claims=expected_claims,
            claim_frequency=claim_frequency,
            claim_severity=claim_severity,
            climate_risk_score=climate_risk_score,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            mitigation_effectiveness=mitigation_effectiveness,
            model_confidence=model_confidence,
            concentration_risk=concentration_risk,
            geographic_factor=geographic_factor,
            regulatory_factor=regulatory_factor,
            economic_factor=economic_factor
        )
        
        valuation = calculate_policy_valuation(policy_id, metrics, policy_value)
        
        return {
            "policy_valuation": {
                "policy_id": valuation.policy_id,
                "valuation_tier": valuation.valuation_tier.value,
                "valuation_score": valuation.valuation_score,
                "profitability_score": valuation.profitability_score,
                "risk_reward_ratio": valuation.risk_reward_ratio,
                "premium_efficiency": valuation.premium_efficiency,
                "improvement_potential": valuation.improvement_potential,
                "recommended_actions": valuation.recommended_actions,
                "notification_required": valuation.notification_required,
                "notification_priority": valuation.notification_priority,
                "calculation_timestamp": valuation.calculation_timestamp.isoformat()
            },
            "policy_metrics": {
                "premium_amount": metrics.premium_amount,
                "expected_claims": metrics.expected_claims,
                "claim_frequency": metrics.claim_frequency,
                "claim_severity": metrics.claim_severity,
                "climate_risk_score": metrics.climate_risk_score,
                "physical_risk": metrics.physical_risk,
                "transition_risk": metrics.transition_risk,
                "mitigation_effectiveness": metrics.mitigation_effectiveness,
                "model_confidence": metrics.model_confidence,
                "concentration_risk": metrics.concentration_risk,
                "geographic_factor": metrics.geographic_factor,
                "regulatory_factor": metrics.regulatory_factor,
                "economic_factor": metrics.economic_factor
            },
            "risk_assessment": {
                "risk_level": "high" if valuation.valuation_score < 50 else "medium" if valuation.valuation_score < 70 else "low",
                "confidence_level": "high" if valuation.calculation_timestamp >= 0.8 else "medium" if valuation.calculation_timestamp >= 0.6 else "low",
                "recommendation": "prioritize" if valuation.valuation_tier.value in ["excellent", "good"] else "review_with_caution" if valuation.valuation_tier.value == "fair" else "consider_avoiding"
            },
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy valuation calculation failed: {str(e)}")

@router.post("/policy-valuation/interactive-analysis")
async def get_interactive_policy_analysis_endpoint(
    policy_id: str = Query(..., description="Policy identifier"),
    premium_amount: float = Query(..., gt=0, description="Premium amount in currency units"),
    expected_claims: float = Query(0.0, ge=0, description="Expected claims amount"),
    claim_frequency: float = Query(0.1, ge=0, le=1, description="Claim frequency (0-1)"),
    claim_severity: float = Query(10000.0, ge=0, description="Claim severity (average claim size)"),
    climate_risk_score: float = Query(500.0, ge=0, le=1000, description="Climate risk score (0-1000)"),
    physical_risk: float = Query(0.4, ge=0, le=1, description="Physical risk factor (0-1)"),
    transition_risk: float = Query(0.3, ge=0, le=1, description="Transition risk factor (0-1)"),
    mitigation_effectiveness: float = Query(0.6, ge=0, le=1, description="Mitigation effectiveness (0-1)"),
    model_confidence: float = Query(0.75, ge=0, le=1, description="Model confidence (0-1)"),
    concentration_risk: float = Query(0.2, ge=0, le=1, description="Concentration risk (0-1)"),
    geographic_factor: float = Query(0.5, ge=0, le=1, description="Geographic risk factor (0-1)"),
    regulatory_factor: float = Query(0.3, ge=0, le=1, description="Regulatory factor (0-1)"),
    economic_factor: float = Query(0.4, ge=0, le=1, description="Economic exposure factor (0-1)"),
    policy_value: float = Query(None, gt=0, description="Total policy value (optional)"),
    max_options: int = Query(5, ge=1, le=10, description="Maximum number of improvement options to return")
):
    """
    Get interactive policy analysis with improvement options.
    Provides intelligent recommendations for improving policy valuation.
    """
    try:
        metrics = PolicyMetrics(
            premium_amount=premium_amount,
            expected_claims=expected_claims,
            claim_frequency=claim_frequency,
            claim_severity=claim_severity,
            climate_risk_score=climate_risk_score,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            mitigation_effectiveness=mitigation_effectiveness,
            model_confidence=model_confidence,
            concentration_risk=concentration_risk,
            geographic_factor=geographic_factor,
            regulatory_factor=regulatory_factor,
            economic_factor=economic_factor
        )
        
        analysis = get_interactive_policy_analysis(policy_id, metrics, policy_value, max_options)
        
        # Format improvement options
        improvement_options = []
        for option in analysis.improvement_options:
            improvement_options.append({
                "option_id": option.option_id,
                "option_name": option.option_name,
                "description": option.description,
                "cost": option.cost,
                "expected_benefit": option.expected_benefit,
                "risk_reduction": option.risk_reduction,
                "implementation_time_days": option.implementation_time_days,
                "success_probability": option.success_probability,
                "category": option.category,
                "roi_percentage": (option.expected_benefit / option.cost * 100) if option.cost > 0 else 0
            })
        
        # Format top recommendations
        top_recommendations = []
        for rec in analysis.top_recommendations:
            top_recommendations.append({
                "option_id": rec.option_id,
                "option_name": rec.option_name,
                "description": rec.description,
                "cost": rec.cost,
                "expected_benefit": rec.expected_benefit,
                "risk_reduction": rec.risk_reduction,
                "roi_percentage": (rec.expected_benefit / rec.cost * 100) if rec.cost > 0 else 0,
                "implementation_time_days": rec.implementation_time_days,
                "success_probability": rec.success_probability
            })
        
        return {
            "interactive_analysis": {
                "policy_id": analysis.policy_id,
                "current_valuation": {
                    "valuation_tier": analysis.current_valuation.valuation_tier.value,
                    "valuation_score": analysis.current_valuation.valuation_score,
                    "profitability_score": analysis.current_valuation.profitability_score,
                    "premium_efficiency": analysis.current_valuation.premium_efficiency,
                    "recommended_actions": analysis.current_valuation.recommended_actions
                },
                "improvement_options": improvement_options,
                "top_recommendations": top_recommendations,
                "estimated_roi": analysis.estimated_roi,
                "implementation_timeline": analysis.implementation_timeline,
                "confidence_level": analysis.confidence_level,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat()
            },
            "options_summary": {
                "total_options_available": len(improvement_options),
                "top_recommendations_count": len(top_recommendations),
                "highest_roi_option": max(improvement_options, key=lambda x: x['roi_percentage']) if improvement_options else None,
                "total_cost_for_top_options": sum(rec['cost'] for rec in top_recommendations),
                "total_expected_benefit": sum(rec['expected_benefit'] for rec in top_recommendations)
            },
            "strategic_recommendations": [
                "Prioritize options with ROI > 100%",
                f"Focus on top {len(top_recommendations)} recommendations for maximum impact",
                f"Expected ROI of {analysis.estimated_roi:.1f}% from implementing recommendations",
                f"Implementation timeline: {analysis.implementation_timeline}"
            ],
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interactive policy analysis failed: {str(e)}")

@router.get("/policy-valuation/notifications")
async def get_pending_notifications_endpoint():
    """
    Get all pending notifications for valuable policies.
    Administrator can review and process these notifications.
    """
    try:
        notifications = get_pending_notifications()
        
        return {
            "notifications": notifications,
            "total_pending": len(notifications),
            "notification_summary": {
                "excellent_policies": len([n for n in notifications if n['valuation_tier'] == 'excellent']),
                "good_policies": len([n for n in notifications if n['valuation_tier'] == 'good']),
                "improvement_opportunities": len([n for n in notifications if n['valuation_tier'] in ['fair', 'poor'] and any('melhoria' in action.lower() for action in n.get('recommended_actions', []))]),
                "high_priority": len([n for n in notifications if n['priority'] >= 4])
            },
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pending notifications retrieval failed: {str(e)}")

@router.post("/policy-valuation/mark-notification-processed")
async def mark_notification_as_processed_endpoint(
    notification_id: str = Query(..., description="Notification identifier to mark as processed")
):
    """
    Mark a notification as processed by the administrator.
    """
    try:
        mark_notification_as_processed(notification_id)
        
        return {
            "notification_id": notification_id,
            "status": "marked_processed",
            "message": "Notification marked as processed successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification processing marking failed: {str(e)}")

@router.get("/policy-valuation/policy-recommendations/{policy_id}")
async def get_policy_recommendations_summary_endpoint(policy_id: str):
    """
    Get summary of recommendations for a specific policy.
    """
    try:
        summary = get_policy_recommendations_summary(policy_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail=f"No recommendations found for policy {policy_id}")
        
        return {
            "policy_recommendations_summary": summary,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy recommendations summary retrieval failed: {str(e)}")

@router.get("/policy-valuation/valuable-policies")
async def get_valuable_policies_summary_endpoint(
    min_score: float = Query(70, ge=0, le=100, description="Minimum valuation score to include")
):
    """
    Get summary of all valuable policies above the specified score threshold.
    """
    try:
        valuable_policies = get_valuable_policies_summary(min_score)
        
        return {
            "valuable_policies": valuable_policies,
            "total_valuable_policies": len(valuable_policies),
            "score_threshold": min_score,
            "valuation_distribution": {
                "excellent": len([p for p in valuable_policies if p['valuation_tier'] == 'excellent']),
                "good": len([p for p in valuable_policies if p['valuation_tier'] == 'good']),
                "all_above_threshold": len(valuable_policies)
            },
            "summary_statistics": {
                "avg_valuation_score": sum(p['valuation_score'] for p in valuable_policies) / len(valuable_policies) if valuable_policies else 0,
                "max_valuation_score": max((p['valuation_score'] for p in valuable_policies), default=0),
                "min_valuation_score": min((p['valuation_score'] for p in valuable_policies), default=0),
                "total_premium_potential": sum(p.get('premium_efficiency', 0) * p.get('profitability_score', 0) / 100 for p in valuable_policies) if valuable_policies else 0
            },
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Valuable policies summary retrieval failed: {str(e)}")

@router.get("/policy-valuation/service-info")
async def get_policy_valuation_service_info():
    """
    Get information about the policy valuation service.
    """
    return {
        "service_name": "ClimateAI Policy Valuation Service",
        "description": "Intelligent policy valuation with automatic notifications and interactive recommendations",
        "features": [
            "Automatic policy valuation with tier classification",
            "Administrator notifications for valuable opportunities",
            "Interactive improvement recommendations",
            "Risk-based premium and claim calculations",
            "Climate risk integration and analytics"
        ],
        "valuation_tiers": {
            "excellent": {"min_score": 80, "description": "High value, low risk policies - prioritize acquisition"},
            "good": {"min_score": 65, "description": "Good value, moderate risk - favorable acquisition"},
            "fair": {"min_score": 50, "description": "Average value, acceptable risk - acquire with caution"},
            "poor": {"min_score": 30, "description": "Low value, high risk - consider carefully"},
            "avoid": {"min_score": 0, "description": "Should be avoided"}
        },
        "notification_logic": {
            "always_notify_excellent": True,
            "notify_good_high_confidence": "model confidence >= 70%",
            "notify_fair_improvement_potential": "improvement potential > 20%",
            "notification_priorities": {
                "1": "Low priority",
                "2": "Medium priority", 
                "3": "Normal priority",
                "4": "High priority",
                "5": "Critical priority"
            }
        },
        "improvement_categories": [
            "mitigation",
            "coverage_optimization",
            "concentration_reduction",
            "data_enhancement",
            "parametric_adjustment"
        ],
        "integration_points": [
            "Climate risk scoring",
            "Premium calculation engine",
            "Claim assessment system",
            "Microsegmentation service",
            "TCFD/ISSB reporting"
        ],
        "compliance": [
            "TCFD recommendations",
            "ISSB standards",
            "Regulatory reporting requirements",
            "Actuarial guidelines"
        ],
        "timestamp": datetime.now().isoformat()
    }
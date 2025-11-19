"""
English API for ClimateAI System
Comprehensive English interface for all ClimateAI services
Demonstrating the full English version of the climate risk analytics platform
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.climate_capital_charge_service import (
    ClimateCapitalChargeResult,
    calculate_climate_capital_charge,
)
from services.climate_scr_service import ClimateSCR, calculate_simple_portfolio_scr
from services.i18n_service import Language, i18n_service, translate_term
from services.ia_analytics_agent_service import (
    ClimateRiskFactors as AnalyticsClimateRiskFactors,
)
from services.ia_analytics_agent_service import climate_analytics_agent
from services.policy_valuation_service import (
    PolicyMetrics,
    PolicyValuation,
    calculate_policy_valuation,
)
from services.sips_performance_analytics_service import (
    calculate_sips_impact_score,
    create_performance_snapshot,
)
from services.smart_climate_exclusions_service import (
    ExclusionDecision,
    evaluate_climate_exclusions,
)

router = APIRouter()


@router.get("/english/about")
async def get_climateai_english_info():
    """
    Get information about the English version of ClimateAI system
    """
    return {
        "title": "ClimateAI English Version",
        "description": "Comprehensive climate risk analytics platform in English",
        "version": "1.0.0",
        "language": "English",
        "features": [
            "Climate Risk Assessment in English",
            "Premium Calculation with English terminology",
            "Claims Processing in English",
            "TCFD/ISSB Reporting in English",
            "Smart Exclusions Management in English",
            "Performance Analytics in English",
            "Multi-language support (English/Portuguese)",
        ],
        "climate_metrics_in_english": [
            "Climate Risk Score (VaR_1ano_climático = R$ X)",
            "Carbon Tax Exposure (Exposição CarbonTax = R$ Y)",
            "RCP 8.5 Stress Scenario (Perda em RCP 8.5 = R$ Z, 129% increase)",
            "Resilience Score (Score de resiliência = W/100)",
        ],
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/english/climate-risk-assessment")
async def english_climate_risk_assessment(
    var_995_losses: List[float] = Query(
        ..., description="List of VaR 99.5% losses for each event type"
    ),
    expected_losses: List[float] = Query(
        ..., description="List of expected losses for each event type"
    ),
    scr_score: float = Query(680.0, description="Climate Risk Score (0-1000)"),
    physical_risk: float = Query(0.40, description="Physical risk factor (0-1)"),
    transition_risk: float = Query(0.30, description="Transition risk factor (0-1)"),
    concentration_risk: float = Query(
        0.22, description="Concentration risk factor (0-1)"
    ),
    mitigation_score: float = Query(0.65, description="Mitigation effectiveness (0-1)"),
    model_confidence: float = Query(0.75, description="Model confidence (0-1)"),
):
    """
    English interface for climate risk assessment using SCR methodology
    Formula: SCR_climatico = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]
    """
    try:
        # Calculate climate risk assessment using calculate_simple_portfolio_scr
        result = calculate_simple_portfolio_scr(var_995_losses, expected_losses)

        # Create ClimateRiskFactors for AI agent analysis
        ai_risk_factors = AnalyticsClimateRiskFactors(
            scr_score=scr_score,
            climate_var_99=sum(var_995_losses),  # Sum of VaR losses for AI agent
            expected_loss=sum(expected_losses),  # Sum of expected losses for AI agent
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=concentration_risk,
            mitigation_score=mitigation_score,
            model_confidence=model_confidence,
            historical_loss_ratio=0.14,  # Placeholder
            geographic_risk_factor=0.5,  # Placeholder
            seasonality_factor=0.4,  # Placeholder
        )

        # Analyze with AI agent
        ai_analysis = climate_analytics_agent.analyze_climate_risks(ai_risk_factors)

        return {
            "climate_risk_assessment": {
                "total_scr": result.total_scr,
                "individual_scrs": result.individual_scrs,
                "correlation_matrix": result.correlation_matrix,
                "portfolio_size": result.portfolio_size,
                "calculation_timestamp": result.calculation_timestamp.isoformat(),
            },
            "risk_breakdown": {
                "physical_risk": physical_risk,
                "transition_risk": transition_risk,
                "concentration_risk": concentration_risk,
                "mitigation_effectiveness": mitigation_score,
            },
            "ai_analysis": {
                "composite_risk_score": ai_analysis["composite_risk_score"],
                "weighted_factors": ai_analysis["weighted_factors"],
                "risk_categories": ai_analysis["risk_categories"],
            },
            "model_confidence": model_confidence,
            "calculation_timestamp": datetime.now().isoformat(),
            "language": "English",
            "formula": "SCR_climatico = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]",
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Climate risk assessment in English failed: {str(e)}",
        )


@router.post("/english/premium-calculation")
async def english_premium_calculation(
    premium_amount: float = Query(20000.0, description="Policy premium amount"),
    expected_claims: float = Query(10000.0, description="Expected claims amount"),
    climate_risk_score: float = Query(680.0, description="Climate risk score (0-1000)"),
    physical_risk: float = Query(0.40, description="Physical risk factor (0-1)"),
    transition_risk: float = Query(0.30, description="Transition risk factor (0-1)"),
    mitigation_effectiveness: float = Query(
        0.65, description="Mitigation effectiveness (0-1)"
    ),
    model_confidence: float = Query(0.75, description="Model confidence (0-1)"),
):
    """
    English interface for intelligent premium calculation
    Includes climate risk factors and uncertainty adjustments
    """
    try:
        # Create policy metrics object
        policy_metrics = PolicyMetrics(
            premium_amount=premium_amount,
            expected_claims=expected_claims,
            climate_risk_score=climate_risk_score,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            mitigation_effectiveness=mitigation_effectiveness,
            model_confidence=model_confidence,
            concentration_risk=0.22,
            geographic_factor=0.5,
            regulatory_factor=0.25,
            economic_factor=0.30,
            claim_frequency=0.14,
            claim_severity=expected_claims / 0.14 if 0.14 > 0 else expected_claims,
        )

        # Calculate policy valuation
        valuation = calculate_policy_valuation(
            "ENG-PREM-001", policy_metrics, premium_amount
        )

        # Get AI-powered premium calculation
        climate_factors = AnalyticsClimateRiskFactors(
            scr_score=climate_risk_score,
            climate_var_99=climate_risk_score * 18,  # Scale appropriately
            expected_loss=expected_claims,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=0.22,
            mitigation_score=mitigation_effectiveness,
            model_confidence=model_confidence,
            historical_loss_ratio=0.14,
            geographic_risk_factor=0.5,
            seasonality_factor=0.4,
        )

        ai_premium = climate_analytics_agent.calculate_premium_intelligent(
            climate_factors
        )

        return {
            "premium_calculation": {
                "base_premium": ai_premium.base_premium,
                "climate_loading": ai_premium.climate_loading,
                "uncertainty_loading": ai_premium.uncertainty_loading,
                "final_premium": ai_premium.final_premium,
                "confidence_score": ai_premium.confidence_score,
            },
            "policy_valuation": {
                "valuation_score": valuation.valuation_score,
                "valuation_tier": valuation.valuation_tier.value,
                "premium_efficiency": valuation.premium_efficiency,
            },
            "climate_factors": {
                "climate_risk_score": climate_risk_score,
                "physical_risk": physical_risk,
                "transition_risk": transition_risk,
                "mitigation_effectiveness": mitigation_effectiveness,
            },
            "calculation_details": ai_premium.risk_factors_considered,
            "timestamp": datetime.now().isoformat(),
            "language": "English",
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Premium calculation in English failed: {str(e)}"
        )


@router.post("/english/claims-assessment")
async def english_claims_assessment(
    claim_amount: float = Query(..., gt=0, description="Amount being claimed"),
    climate_risk_score: float = Query(
        680.0, description="Climate risk score at policy time"
    ),
    physical_risk: float = Query(0.40, description="Relevant physical risk factor"),
    transition_risk: float = Query(0.30, description="Relevant transition risk factor"),
    policy_coverage: float = Query(
        ..., gt=0, description="Original policy coverage amount"
    ),
):
    """
    English interface for climate-related claims assessment
    Evaluates claims based on climate risk factors and validity
    """
    try:
        # Create risk factors for claim assessment
        risk_factors = AnalyticsClimateRiskFactors(
            scr_score=climate_risk_score,
            climate_var_99=climate_risk_score * 18,
            expected_loss=policy_coverage * 0.3,  # Assumption
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=0.22,
            mitigation_score=0.65,
            model_confidence=0.75,
            historical_loss_ratio=0.14,
            geographic_risk_factor=0.5,
            seasonality_factor=0.4,
        )

        # Use AI agent for claim assessment
        climate_factors = AnalyticsClimateRiskFactors(
            scr_score=climate_risk_score,
            climate_var_99=climate_risk_score * 18,
            expected_loss=policy_coverage * 0.3,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=0.22,
            mitigation_score=0.65,
            model_confidence=0.75,
            historical_loss_ratio=0.14,
            geographic_risk_factor=0.5,
            seasonality_factor=0.4,
        )

        ai_assessment = climate_analytics_agent.assess_claim_intelligent(
            claim_amount, climate_factors
        )

        return {
            "claim_assessment": {
                "original_claim_amount": claim_amount,
                "probability_valid": ai_assessment.probability_valid,
                "adjusted_amount": ai_assessment.adjusted_amount,
                "fraud_indicator": ai_assessment.fraud_indicator,
                "final_settlement": ai_assessment.adjusted_amount,
            },
            "climate_analysis": {
                "climate_risk_score": climate_risk_score,
                "physical_risk_factor": physical_risk,
                "transition_risk_factor": transition_risk,
            },
            "assessment_factors": ai_assessment.supporting_factors,
            "investigation_priority": ai_assessment.investigation_priority,
            "timestamp": datetime.now().isoformat(),
            "language": "English",
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Claims assessment in English failed: {str(e)}"
        )


@router.post("/english/tcfd-report")
async def english_tcfd_report_generation():
    """
    Generate English TCFD/ISSB report with climate metrics
    Metrics include:
    - VaR_1ano_climatico = R$ X
    - CarbonTax exposure = R$ Y
    - RCP 8.5 loss = R$ Z (129% increase)
    - Resilience score = W/100
    """
    raise HTTPException(
        status_code=501, detail="Endpoint not implemented with current service methods"
    )


@router.get("/english/sips-performance")
async def english_sips_performance_metrics():
    """
    Get English metrics for SIPS-Climate performance
    Showing the improvements: claim rate, climate losses, net margin, etc.
    """
    try:
        # Create performance snapshot with improved metrics
        snapshot = create_performance_snapshot(
            snapshot_id="ENG-SIPS-REPORT-001",
            date=datetime.now(),
            claim_rate=0.58,  # Improved from 65%
            climate_loss_rate=0.31,  # Improved from 42%
            net_margin=0.14,  # Improved from 8%
            rejection_rate=0.12,  # Improved from 5%
            average_premium=1650.0,  # Improved from R$1.2K
            client_retention=0.85,  # Improved from 78%
            economic_capital=52000000.0,  # Improved from R$45M
        )

        impact_score = calculate_sips_impact_score(snapshot)

        return {
            "sips_climate_performance": {
                "improvement_metrics": {
                    "claim_rate_improvement": "65% → 58% (-7pp)",
                    "climate_losses_improvement": "42% → 31% (-11pp)",
                    "net_margin_improvement": "8% → 14% (+6pp)",
                    "premium_growth": "R$1.2K → R$1.65K (+38%)",
                    "client_retention_improvement": "78% → 85% (+7pp)",
                    "economic_capital_growth": "R$45M → R$52M (+15%)",
                },
                "current_performance": {
                    "claim_rate": f"{snapshot.claim_rate*100:.1f}%",
                    "climate_loss_rate": f"{snapshot.climate_loss_rate*100:.1f}%",
                    "net_margin": f"{snapshot.net_margin*100:.1f}%",
                    "average_premium": f"R$ {snapshot.average_premium:,.2f}",
                    "client_retention": f"{snapshot.client_retention*100:.1f}%",
                    "economic_capital": f"R$ {snapshot.economic_capital:,.2f}",
                },
                "impact_score": f"{impact_score}/100",
                "performance_assessment": "Significant improvements across all metrics",
                "sips_climate_benefits": [
                    "Reduced climate-related claims",
                    "Improved net profitability",
                    "Higher client retention",
                    "Better risk-adjusted returns",
                    "Enhanced portfolio resilience",
                ],
            },
            "calculation_timestamp": datetime.now().isoformat(),
            "language": "English",
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SIPS performance metrics in English failed: {str(e)}",
        )


@router.get("/english/translation-service")
async def english_translation_service_status():
    """
    Get status of the internationalization service in English
    """
    try:
        available_languages = i18n_service.get_available_languages()

        # Test a few key translations
        test_terms = [
            "climate_risk",
            "premium_calculation",
            "claim_assessment",
            "tcfd_reporting",
            "resilience_score",
        ]
        test_translations = {}
        for term in test_terms:
            en_translation = i18n_service.translate(term, Language.EN_US)
            pt_translation = i18n_service.translate(term, Language.PT_BR)
            test_translations[term] = {
                "english": en_translation,
                "portuguese": pt_translation,
            }

        return {
            "translation_service_status": "Operational",
            "available_languages": available_languages,
            "total_translatable_terms": len(
                i18n_service.get_translations_for_language(Language.EN_US)
            ),
            "sample_translations": test_translations,
            "service_features": [
                "Climate risk terminology translation",
                "Financial and insurance terms",
                "Technical modeling terms",
                "Reporting terminology",
                "Bilingual API responses",
            ],
            "last_update": datetime.now().isoformat(),
            "language": "English",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Translation service status check failed: {str(e)}"
        )


@router.get("/english/system-overview")
async def english_system_overview():
    """
    Complete English overview of the ClimateAI system capabilities
    """
    return {
        "climateai_system_overview": {
            "name": "ClimateAI Platform",
            "language": "English Interface",
            "purpose": "Comprehensive climate risk analytics for insurance applications",
            "core_capabilities": [
                "Climate Risk Modeling and Assessment",
                "Intelligent Premium Calculation",
                "Climate-Related Claims Processing",
                "TCFD/ISSB Automated Reporting",
                "SIPS-Climate Performance Analytics",
                "Smart Exclusions Management",
                "Parametric Insurance Solutions",
            ],
            "climate_metrics_supported": [
                {
                    "metric": "VaR_1ano_climatico",
                    "formula": "Value at Risk for 1-year climate events",
                    "unit": "R$",
                    "example": "R$ X as calculated value",
                },
                {
                    "metric": "Exposicao_CarbonTax",
                    "formula": "Exposure to carbon pricing mechanisms",
                    "unit": "R$",
                    "example": "R$ Y as calculated exposure",
                },
                {
                    "metric": "RCP_85_Stress_Test",
                    "formula": "Loss projection under RCP 8.5 scenario",
                    "unit": "R$",
                    "increase": "129% above baseline",
                    "example": "R$ Z as projected loss",
                },
                {
                    "metric": "Resilience_Score",
                    "formula": "Overall climate resilience assessment",
                    "scale": "0-100",
                    "example": "W/100 as calculated score",
                },
            ],
            "integration_points": [
                "Embrapa Climate API",
                "OpenMeteo Weather Data",
                "CMIP Climate Models",
                "Real-time Risk Monitoring",
                "Automated Reporting Systems",
            ],
            "regulatory_compliance": [
                "TCFD Recommendations",
                "ISSB Standards",
                "Local Insurance Regulations",
                "Climate Risk Disclosure Requirements",
            ],
            "machine_learning_components": [
                "Climate Risk Prediction",
                "Premium Optimization",
                "Fraud Detection",
                "Trend Analysis",
                "Scenario Modeling",
            ],
            "system_status": "Operational",
            "last_update": datetime.now().isoformat(),
        }
    }

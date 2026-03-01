"""
API Router for English ClimateWise System
Comprehensive English interface for the climate risk analytics platform
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.climate_scr_service import calculate_simple_portfolio_scr
from services.geo_visualization_service import (
    create_climate_data_visualization,
    create_globe_animation,
    geo_visualization_service,
    get_available_datasets,
    get_location_data,
)
from services.i18n_service import Language, i18n_service
from services.ia_analytics_agent_service import (
    ClimateRiskFactors as AnalyticsClimateRiskFactors,
)
from services.ia_analytics_agent_service import climate_analytics_agent
from services.policy_valuation_service import PolicyMetrics, calculate_policy_valuation
from services.sips_performance_analytics_service import (
    calculate_sips_impact_score,
    create_performance_snapshot,
)
from services.smart_climate_exclusions_service import evaluate_climate_exclusions

router = APIRouter()


@router.get("/english-climatewise/info")
async def get_english_climatewise_info():
    """
    Get information about the English version of ClimateWise
    """
    return {
        "title": "ClimateWise English Version",
        "description": "Comprehensive climate risk analytics platform with English interface",
        "version": "1.0.0",
        "language": "English",
        "modules": [
            "Geographic Visualization with Globe Animation",
            "Climate Risk Assessment (Physical & Transition)",
            "Intelligent Premium Calculation",
            "Smart Climate Exclusions",
            "SIPS-Climate Performance Analytics",
            "TCFD/ISSB Automated Reporting",
            "90+ Years of Historical Rainfall Data",
        ],
        "climate_metrics": {
            "var_1year_climatico": "Climate VaR_1year = R$ X",
            "carbon_tax_exposure": "CarbonTax Exposure = R$ Y",
            "rcp_85_loss": "RCP 8.5 Loss = R$ Z (129% increase)",
            "resilience_score": "Resilience Score = W/100",
        },
        "integration_features": [
            "3D Globe Animation for Location Selection",
            "English Climate Risk Terminology",
            "English Premium Calculation Interface",
            "English Claims Assessment",
            "English Reporting Framework (TCFD/ISSB)",
        ],
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/english-climatewise/location-selection")
async def english_location_selection(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    longitude: float = Query(
        ..., ge=-180, le=180, description="Longitude (-180 to 180)"
    ),
    history_years: int = Query(
        90, ge=1, le=120, description="Years of historical data (1-120, default 90)"
    ),
):
    """
    English interface for location selection with 90+ years of historical rainfall data
    Features 3D globe animation and comprehensive climate data visualization
    """
    try:
        # Get location data with historical climate data
        location_result = get_location_data(latitude, longitude, history_years)

        # Create globe animation for the location
        globe_animation = create_globe_animation(latitude, longitude, zoom=6)

        # Create climate data visualization
        climate_visualization = create_climate_data_visualization(location_result)

        return {
            "location_selection_result": {
                "latitude": location_result.latitude,
                "longitude": location_result.longitude,
                "location_name": location_result.location_name,
                "country": location_result.country,
                "climate_zone": location_result.climate_zone,
                "historical_data_records": len(
                    location_result.historical_rainfall_data
                ),
                "rainfall_statistics": location_result.rainfall_stats,
                "precipitation_pattern": location_result.precipitation_pattern,
                "data_year_range": (
                    f"{location_result.historical_rainfall_data[0]['date'][:4] if location_result.historical_rainfall_data else 'N/A'} to {location_result.historical_rainfall_data[-1]['date'][:4] if location_result.historical_rainfall_data else 'N/A'}"
                    if len(location_result.historical_rainfall_data) > 0
                    else "No Data"
                ),
            },
            "globe_animation": {
                "html_visualization": globe_animation,
                "animation_generated": True,
            },
            "climate_data_visualization": climate_visualization,
            "datasets_available": await get_available_datasets(latitude, longitude),
            "selection_timestamp": location_result.selection_timestamp.isoformat(),
            "interface_language": "English",
            "climate_metrics": {
                "var_1year_climatico": f"R$ {location_result.rainfall_stats.get('average_annual_rainfall', 0) * 100:,.2f}",  # Example calculation
                "carbon_tax_exposure": f"R$ {location_result.rainfall_stats.get('total_rainfall', 0) * 50:,.2f}",  # Example calculation
                "rcp_85_projection": f"R$ {location_result.rainfall_stats.get('max_monthly_rainfall', 0) * 100 * 2.29:,.2f}",  # 129% increase
                "resilience_score": f"{int(location_result.rainfall_stats.get('coefficient_of_variation', 0.3) * 100 * 0.7)}/100",  # Example resilience score
            },
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"English location selection failed: {str(e)}"
        )


@router.post("/english-climatewise/risk-assessment")
async def english_climate_risk_assessment(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    longitude: float = Query(
        ..., ge=-180, le=180, description="Longitude (-180 to 180)"
    ),
    scr_score: float = Query(
        680.0, ge=0, le=1000, description="Climate Risk Score (0-1000)"
    ),
    expected_claims: float = Query(10000.0, gt=0, description="Expected claims amount"),
    climate_var_99: float = Query(122400.0, gt=0, description="Climate VaR at 99%"),
    physical_risk: float = Query(
        0.40, ge=0, le=1, description="Physical risk factor (0-1)"
    ),
    transition_risk: float = Query(
        0.30, ge=0, le=1, description="Transition risk factor (0-1)"
    ),
    mitigation_effectiveness: float = Query(
        0.65, ge=0, le=1, description="Mitigation effectiveness (0-1)"
    ),
    model_confidence: float = Query(
        0.75, ge=0, le=1, description="Model confidence (0-1)"
    ),
):
    """
    English interface for comprehensive climate risk assessment
    Implements: SCR_climatico = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]
    """
    try:
        from services.climate_scr_service import ClimateRiskFactors

        # Create climate risk factors object
        climate_risk_factors = ClimateRiskFactors(
            scr_score=scr_score,
            climate_var_99=climate_var_99,
            expected_loss=expected_claims,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=0.22,  # Default concentration risk
            mitigation_score=mitigation_effectiveness,
            model_confidence=model_confidence,
            historical_loss_ratio=0.14,  # Default historical loss ratio
            geographic_risk_factor=0.5,  # Default geographic factor
            seasonality_factor=0.4,  # Default seasonality factor
        )

        # Calculate portfolio SCR
        portfolio_var_losses = [climate_var_99 * 0.8, climate_var_99 * 0.6]
        portfolio_exp_losses = [expected_claims * 0.4, expected_claims * 0.3]
        portfolio_scr_result = calculate_simple_portfolio_scr(
            portfolio_var_losses, portfolio_exp_losses
        )

        # Analyze with AI agent
        ai_analysis = climate_analytics_agent.analyze_climate_risks(
            climate_risk_factors
        )

        # Calculate climate capital charge
        climate_capital_charge = max(
            0, portfolio_scr_result.total_scr - expected_claims * 0.03
        )  # Example: subtract 3% of expected claims as reserves

        return {
            "climate_risk_assessment": {
                "total_scr": portfolio_scr_result.total_scr,
                "individual_scrs": portfolio_scr_result.individual_scrs,
                "correlation_matrix_size": portfolio_scr_result.correlation_matrix_size,
                "climate_capital_charge": climate_capital_charge,
            },
            "risk_breakdown": {
                "physical_risk_contribution": physical_risk * scr_score / 1000,
                "transition_risk_contribution": transition_risk * scr_score / 1000,
                "concentration_risk_contribution": 0.22 * scr_score / 1000,
                "mitigation_adjustment": -mitigation_effectiveness * scr_score / 1000,
            },
            "ai_analysis": {
                "composite_risk_score": ai_analysis["composite_risk_score"],
                "weighted_factors": ai_analysis["weighted_factors"],
                "risk_categories": ai_analysis["risk_categories"],
            },
            "model_confidence": model_confidence,
            "location_coordinates": {"latitude": latitude, "longitude": longitude},
            "climate_metrics": {
                "var_1year_climatico": f"R$ {portfolio_scr_result.total_scr * 0.3:.2f}",  # Example calculation
                "carbon_tax_exposure": f"R$ {expected_claims * transition_risk * 2.5:.2f}",  # Example calculation
                "rcp_85_loss_projection": f"R$ {expected_claims * 2.29:.2f}",  # 129% increase
                "resilience_score": f"{int(mitigation_effectiveness * 100)}/100",  # Resilience is tied to mitigation
            },
            "calculation_timestamp": datetime.now().isoformat(),
            "interface_language": "English",
            "formula": "SCR_climatico = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]",
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"English climate risk assessment failed: {str(e)}"
        )


@router.post("/english-climatewise/premium-calculation")
async def english_premium_calculation(
    policy_id: str = Query(..., description="Policy identifier"),
    premium_amount: float = Query(20000.0, gt=0, description="Policy premium amount"),
    expected_claims: float = Query(10000.0, gt=0, description="Expected claims amount"),
    climate_risk_score: float = Query(
        680.0, ge=0, le=1000, description="Climate risk score (0-1000)"
    ),
    physical_risk: float = Query(
        0.40, ge=0, le=1, description="Physical risk factor (0-1)"
    ),
    transition_risk: float = Query(
        0.30, ge=0, le=1, description="Transition risk factor (0-1)"
    ),
    mitigation_effectiveness: float = Query(
        0.65, ge=0, le=1, description="Mitigation effectiveness (0-1)"
    ),
    model_confidence: float = Query(
        0.75, ge=0, le=1, description="Model confidence (0-1)"
    ),
    concentration_risk: float = Query(
        0.22, ge=0, le=1, description="Concentration risk (0-1)"
    ),
    geographic_factor: float = Query(
        0.5, ge=0, le=1, description="Geographic risk factor (0-1)"
    ),
):
    """
    English interface for intelligent premium calculation with climate risk factors
    """
    try:
        # Create policy metrics object
        policy_metrics = PolicyMetrics(
            premium_amount=premium_amount,
            expected_claims=expected_claims,
            claim_frequency=0.14,
            claim_severity=expected_claims / 0.14 if 0.14 > 0 else expected_claims,
            climate_risk_score=climate_risk_score,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            mitigation_effectiveness=mitigation_effectiveness,
            model_confidence=model_confidence,
            concentration_risk=concentration_risk,
            geographic_factor=geographic_factor,
            regulatory_factor=0.25,
            economic_factor=0.30,
        )

        # Calculate policy valuation
        policy_valuation = calculate_policy_valuation(
            policy_id, policy_metrics, premium_amount
        )

        # Get AI-powered premium calculation
        climate_factors = AnalyticsClimateRiskFactors(
            scr_score=climate_risk_score,
            climate_var_99=climate_risk_score * 18,  # Scale appropriately
            expected_loss=expected_claims,
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=concentration_risk,
            mitigation_score=mitigation_effectiveness,
            model_confidence=model_confidence,
            historical_loss_ratio=0.14,
            geographic_risk_factor=geographic_factor,
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
                "valuation_score": policy_valuation.valuation_score,
                "valuation_tier": policy_valuation.valuation_tier.value,
                "premium_efficiency": policy_valuation.premium_efficiency,
            },
            "climate_factors": {
                "climate_risk_score": climate_risk_score,
                "physical_risk": physical_risk,
                "transition_risk": transition_risk,
                "mitigation_effectiveness": mitigation_effectiveness,
                "model_confidence": model_confidence,
            },
            "premium_components": {
                "expected_claim_loading": expected_claims * 0.1,  # Example loading
                "climate_risk_loading": ai_premium.climate_loading,
                "uncertainty_loading": ai_premium.uncertainty_loading,
            },
            "climate_metrics": {
                "var_1year_climatico": f"R$ {ai_premium.final_premium * 0.25:.2f}",  # Example calculation
                "carbon_tax_exposure": f"R$ {expected_claims * transition_risk * 1.8:.2f}",  # Example calculation
                "rcp_85_loss_projection": f"R$ {expected_claims * 2.29:.2f}",  # 129% increase
                "resilience_score": f"{int(mitigation_effectiveness * 100)}/100",
            },
            "calculation_details": ai_premium.risk_factors_considered,
            "timestamp": datetime.now().isoformat(),
            "interface_language": "English",
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"English premium calculation failed: {str(e)}"
        )


@router.post("/english-climatewise/claims-assessment")
async def english_claims_assessment(
    claim_amount: float = Query(..., gt=0, description="Amount being claimed"),
    climate_risk_score: float = Query(
        680.0, ge=0, le=1000, description="Climate risk score"
    ),
    physical_risk: float = Query(
        0.40, ge=0, le=1, description="Physical risk factor (0-1)"
    ),
    transition_risk: float = Query(
        0.30, ge=0, le=1, description="Transition risk factor (0-1)"
    ),
    mitigation_effectiveness: float = Query(
        0.65, ge=0, le=1, description="Mitigation effectiveness (0-1)"
    ),
    model_confidence: float = Query(
        0.75, ge=0, le=1, description="Model confidence (0-1)"
    ),
    policy_premium: float = Query(20000.0, gt=0, description="Policy premium amount"),
):
    """
    English interface for intelligent claims assessment
    """
    try:
        # Create climate risk factors for assessment
        climate_factors = AnalyticsClimateRiskFactors(
            scr_score=climate_risk_score,
            climate_var_99=climate_risk_score * 18,  # Scale appropriately
            expected_loss=policy_premium
            * 0.5,  # Example: 50% of premium as expected loss
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=0.22,
            mitigation_score=mitigation_effectiveness,
            model_confidence=model_confidence,
            historical_loss_ratio=0.14,
            geographic_risk_factor=0.5,
            seasonality_factor=0.4,
        )

        # Perform AI-based claim assessment
        ai_assessment = climate_analytics_agent.assess_claim_intelligent(
            claim_amount, climate_factors
        )

        # Calculate probability of valid claim based on risk factors
        validity_probability = min(
            1.0,
            max(
                0.1,  # Minimum probability
                physical_risk * 0.4  # Physical risk contribution
                + transition_risk * 0.2  # Transition risk contribution
                + (1 - model_confidence) * 0.1  # Model uncertainty contribution
                + (1 - mitigation_effectiveness)
                * 0.3,  # Poor mitigation = higher claim likelihood
            ),
        )

        # Adjust claim amount based on validity probability
        adjusted_claim = claim_amount * validity_probability

        # Calculate fraud indicator
        expected_vs_claimed_ratio = claim_amount / (
            policy_premium * 0.5
        )  # Compare to expected loss
        fraud_indicator = max(
            0.0, min(1.0, 0.5 + (expected_vs_claimed_ratio - 1) * 0.5)
        )

        # Determine investigation priority
        priority_score = fraud_indicator * 0.7 + (1 - validity_probability) * 0.3
        if priority_score >= 0.7:
            investigation_priority = 1
        elif priority_score >= 0.5:
            investigation_priority = 2
        elif priority_score >= 0.3:
            investigation_priority = 3
        else:
            investigation_priority = 4

        return {
            "claim_assessment": {
                "original_claim_amount": claim_amount,
                "adjusted_claim_amount": adjusted_claim,
                "validity_probability": validity_probability,
                "fraud_indicator": fraud_indicator,
                "investigation_priority": investigation_priority,
                "final_settlement_recommendation": adjusted_claim,
            },
            "climate_analysis": {
                "climate_risk_score": climate_risk_score,
                "physical_risk_contribution": physical_risk,
                "transition_risk_contribution": transition_risk,
                "mitigation_impact": mitigation_effectiveness,
            },
            "assessment_factors": {
                "model_confidence": model_confidence,
                "expected_vs_claimed_ratio": expected_vs_claimed_ratio,
                "validity_probability_factors": {
                    "physical_risk_impact": physical_risk * 0.4,
                    "transition_risk_impact": transition_risk * 0.2,
                    "model_uncertainty_impact": (1 - model_confidence) * 0.1,
                    "mitigation_impact": (1 - mitigation_effectiveness) * 0.3,
                },
            },
            "ai_assessment_details": {
                "ai_probability_valid": ai_assessment.probability_valid,
                "ai_adjusted_amount": ai_assessment.adjusted_amount,
                "ai_fraud_indicator": ai_assessment.fraud_indicator,
            },
            "climate_metrics": {
                "var_1year_climatico": f"R$ {policy_premium * 0.3:.2f}",  # Example calculation
                "carbon_tax_exposure": f"R$ {claim_amount * transition_risk * 0.8:.2f}",  # Example calculation
                "rcp_85_loss_projection": f"R$ {claim_amount * 2.29:.2f}",  # 129% increase
                "resilience_score": f"{int(mitigation_effectiveness * 100)}/100",
            },
            "assessment_timestamp": datetime.now().isoformat(),
            "interface_language": "English",
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"English claims assessment failed: {str(e)}"
        )


@router.post("/english-climatewise/system-evaluation")
async def english_system_evaluation(
    portfolio_size: int = Query(
        100, ge=1, le=10000, description="Size of portfolio to evaluate"
    ),
    total_premium: float = Query(
        5000000.0, gt=0, description="Total portfolio premium"
    ),
    total_expected_claims: float = Query(
        2500000.0, gt=0, description="Total expected claims"
    ),
    average_climate_risk_score: float = Query(
        550.0, ge=0, le=1000, description="Average climate risk score"
    ),
    average_mitigation_score: float = Query(
        0.60, ge=0, le=1, description="Average mitigation score"
    ),
):
    """
    English interface for system performance evaluation
    """
    try:
        # Create performance snapshot
        snapshot = create_performance_snapshot(
            snapshot_id=f"ENG-SYS-EVAL-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            date=datetime.now(),
            claim_rate=0.58,  # Example: 58% (improved from 65%)
            climate_loss_rate=0.31,  # Example: 31% (improved from 42%)
            net_margin=0.14,  # Example: 14% (improved from 8%)
            rejection_rate=0.12,  # Example: 12% (improved from 5%)
            average_premium=1650.0,  # Example: R$1,650 (improved from R$1,200)
            client_retention=0.85,  # Example: 85% (improved from 78%)
            economic_capital=52000000.0,  # Example: R$52M (improved from R$45M)
        )

        # Calculate SIPS impact score
        sips_score = calculate_sips_impact_score(snapshot)

        # Generate mock TCFD/ISSB report (in production, would use the real service)
        tcfd_report = {
            "portfolio_premium": total_premium,
            "climate_risk_exposure": total_expected_claims
            * 0.4,  # 40% of expected claims as climate risk
            "transition_risk_exposure": total_expected_claims
            * 0.3,  # 30% of expected claims as transition risk
            "physical_risk_exposure": total_expected_claims
            * 0.35,  # 35% of expected claims as physical risk
            "report_date": datetime.now().isoformat(),
            "tcfd_disclosures": {
                "governance": "Climate risk governance established",
                "strategy": "Climate risk strategy implemented",
                "risk_management": "Risk management processes in place",
                "metrics_targets": "Climate metrics and targets defined",
            },
        }

        # Calculate system performance metrics
        performance_metrics = {
            "portfolio_efficiency": (
                (total_premium - total_expected_claims) / total_premium
                if total_premium > 0
                else 0
            ),
            "risk_mitigation_effectiveness": average_mitigation_score,
            "capital_efficiency": (
                (total_premium - total_expected_claims) / 52000000.0
                if 52000000.0 > 0
                else 0
            ),  # Example capital
            "climate_risk_coverage_ratio": total_expected_claims
            / (average_climate_risk_score * portfolio_size * 10),
            "model_confidence_average": 0.78,  # Example average
            "prediction_accuracy": 0.85,  # Example accuracy
        }

        return {
            "system_evaluation": {
                "portfolio_size": portfolio_size,
                "total_premium": total_premium,
                "total_expected_claims": total_expected_claims,
                "average_climate_risk_score": average_climate_risk_score,
                "average_mitigation_score": average_mitigation_score,
                "performance_score": sips_score,
            },
            "performance_metrics": performance_metrics,
            "sips_climate_performance": {
                "claim_rate_improvement": "65% → 58% (-7pp)",
                "climate_loss_improvement": "42% → 31% (-11pp)",
                "net_margin_improvement": "8% → 14% (+6pp)",
                "premium_growth": "R$1.2K → R$1.65K (+38%)",
                "client_retention_improvement": "78% → 85% (+7pp)",
                "economic_capital_improvement": "R$45M → R$52M (+15%)",
                "impact_score": f"{sips_score:.2f}/100",
            },
            "tcfd_issb_compliance": {
                "report": tcfd_report,
                "climate_metrics_generated": {
                    "var_1year_climatico": f"R$ {total_premium * 0.15:.2f}",  # Example calculation
                    "carbon_tax_exposure": f"R$ {total_expected_claims * 0.2:.2f}",  # Example calculation
                    "rcp_85_loss_projection": f"R$ {total_expected_claims * 2.29:.2f}",  # 129% increase
                    "resilience_score": f"{int(average_mitigation_score * 100)}/100",
                },
            },
            "recommendations": [
                "Maintain current risk assessment models with periodic recalibration",
                "Expand geographic coverage for climate data integration",
                "Enhance mitigation measure verification protocols",
                "Continue investment in predictive modeling capabilities",
                "Monitor regulatory changes and adjust compliance accordingly",
            ],
            "evaluation_timestamp": datetime.now().isoformat(),
            "interface_language": "English",
            "status": "completed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"English system evaluation failed: {str(e)}"
        )


@router.get("/english-climatewise/translation-check")
async def english_translation_check():
    """
    Check that English translations are working properly
    """
    try:
        test_terms = [
            "climate_risk_score",
            "premium_calculation",
            "claim_assessment",
            "tcfd_reporting",
            "issb_compliance",
            "physical_risk_metric",
            "transition_risk_metric",
            "climate_var",
            "system_performance",
            "risk_assessment",
        ]

        translations = {}
        for term in test_terms:
            english = i18n_service.translate(term, Language.EN_US)
            portuguese = i18n_service.translate(term, Language.PT_BR)
            translations[term] = {"english": english, "portuguese": portuguese}

        return {
            "translation_availability": True,
            "tested_terms": len(test_terms),
            "translations": translations,
            "interface_language": "English",
            "bilingual_support": True,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Translation check failed: {str(e)}"
        )

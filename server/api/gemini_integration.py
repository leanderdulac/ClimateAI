"""
API Router for Google Gemini Integration Service
Provides natural language processing and analysis capabilities to complement
the specialized climate risk AI system already implemented
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.gemini_integration_service import (
    GeminiAnalysisResult,
    analyze_climate_report,
    analyze_policy_language,
    chat_with_assistant,
    explain_actuarial_decision,
    gemini_integration_service,
    generate_mitigation_suggestions,
    summarize_climate_data,
)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}
    history: Optional[List[Dict[str, str]]] = []


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Interactive chat with Climate Assistant
    """
    try:
        result = await chat_with_assistant(
            request.message, request.context, request.history
        )
        return {
            "response": result.analysis_text,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-climate-report")
async def analyze_climate_report_endpoint(
    report_text: str = Query(
        ..., description="Text of the technical climate report to analyze"
    ),
    focus_area: str = Query(
        "climate_risk",
        description="Focus area: climate_risk, policy_language, mitigation_strategies",
    ),
):
    """
    Analyze technical climate reports using Gemini for natural language processing
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not configured in environment variables",
        )

    try:
        result = await analyze_climate_report(report_text, focus_area)

        return {
            "analysis_result": {
                "analysis_text": result.analysis_text,
                "confidence_level": result.confidence_level,
                "processing_timestamp": result.processing_timestamp.isoformat(),
                "analysis_type": result.analysis_type,
                "sources_considered": result.sources_considered,
                "complementary_to": result.complementary_to,
            },
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Gemini climate report analysis failed: {str(e)}"
        )


@router.post("/explain-actuarial-decision")
async def explain_actuarial_decision_endpoint(
    decision_type: str = Query(
        "premium_calculation",
        description="Type of decision: premium_calculation, claim_assessment, risk_analysis",
    ),
    decision_factors_json: str = Query(
        ..., description="JSON string of decision factors"
    ),
):
    """
    Explain actuarial decisions in natural language using Gemini
    """
    import json

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not configured in environment variables",
        )

    try:
        # Parse the JSON string
        decision_factors = json.loads(decision_factors_json)

        result = await explain_actuarial_decision(decision_factors, decision_type)

        return {
            "explanation_result": {
                "explanation_text": result.analysis_text,
                "confidence_level": result.confidence_level,
                "processing_timestamp": result.processing_timestamp.isoformat(),
                "analysis_type": result.analysis_type,
                "sources_considered": result.sources_considered,
                "complementary_to": result.complementary_to,
            },
            "requested_decision_type": decision_type,
            "factors_analyzed": list(decision_factors.keys()),
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in decision_factors: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini actuarial decision explanation failed: {str(e)}",
        )


@router.post("/generate-mitigation-suggestions")
async def generate_mitigation_suggestions_endpoint(
    asset_type: str = Query(
        "property",
        description="Asset type: property, infrastructure, agriculture, etc.",
    ),
    risk_profile_json: str = Query(..., description="JSON string of risk profile"),
):
    """
    Generate mitigation suggestions based on risk profile using Gemini
    """
    import json

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not configured in environment variables",
        )

    try:
        # Parse the JSON string
        risk_profile = json.loads(risk_profile_json)

        result = await generate_mitigation_suggestions(risk_profile, asset_type)

        return {
            "mitigation_suggestions": {
                "suggestions_text": result.analysis_text,
                "confidence_level": result.confidence_level,
                "processing_timestamp": result.processing_timestamp.isoformat(),
                "analysis_type": result.analysis_type,
                "sources_considered": result.sources_considered,
                "complementary_to": result.complementary_to,
            },
            "asset_type": asset_type,
            "profile_risks_considered": list(risk_profile.keys()),
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in risk_profile: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini mitigation suggestions generation failed: {str(e)}",
        )


@router.post("/analyze-policy-language")
async def analyze_policy_language_endpoint(
    focus_on: str = Query(
        "climate_exclusions",
        description="Focus of analysis: climate_exclusions, coverage_limits, definitions",
    ),
    policy_text: str = Query(
        ..., description="Text of the insurance policy to analyze"
    ),
):
    """
    Analyze policy language for climate-related clauses using Gemini
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not configured in environment variables",
        )

    try:
        result = await analyze_policy_language(policy_text, focus_on)

        return {
            "language_analysis": {
                "analysis_text": result.analysis_text,
                "confidence_level": result.confidence_level,
                "processing_timestamp": result.processing_timestamp.isoformat(),
                "analysis_type": result.analysis_type,
                "sources_considered": result.sources_considered,
                "complementary_to": result.complementary_to,
            },
            "analysis_focus": focus_on,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Gemini policy language analysis failed: {str(e)}"
        )


@router.post("/summarize-climate-data")
async def summarize_climate_data_endpoint(
    analysis_period: str = Query(
        "12_months",
        description="Analysis period: 6_months, 12_months, 24_months, 36_months",
    ),
    climate_data_json: str = Query(
        ..., description="JSON string of climate variables data"
    ),
):
    """
    Summarize complex climate data into human-readable interpretation using Gemini
    """
    import json

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not configured in environment variables",
        )

    try:
        # Parse the JSON string
        climate_data = json.loads(climate_data_json)

        result = await summarize_climate_data(climate_data, analysis_period)

        return {
            "data_summary": {
                "summary_text": result.analysis_text,
                "confidence_level": result.confidence_level,
                "processing_timestamp": result.processing_timestamp.isoformat(),
                "analysis_type": result.analysis_type,
                "sources_considered": result.sources_considered,
                "complementary_to": result.complementary_to,
            },
            "analysis_period": analysis_period,
            "climate_variables_analyzed": list(climate_data.keys()),
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in climate_data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini climate data summarization failed: {str(e)}",
        )


@router.get("/capabilities")
async def get_gemini_capabilities():
    """
    Get information about Gemini integration capabilities
    """
    return {
        "service_name": "ClimateAI Gemini Integration",
        "description": "Natural Language Processing integration with Google Gemini to complement specialized climate risk AI",
        "primary_use_cases": [
            "Summarize technical climate reports",
            "Explain actuarial decisions in natural language",
            "Generate mitigation suggestions",
            "Analyze policy language for climate clauses",
            "Interpret climate data trends",
        ],
        "integration_approach": "Complementary to specialized ClimateAI models",
        "models_available": ["gemini-pro", "gemini-1.5-pro"],
        "confidentiality_note": "Use with care for sensitive data - data sent to external Gemini API",
        "api_key_required": bool(os.getenv("GEMINI_API_KEY")),
        "complementary_to": [
            "Climate Risk Analysis",
            "Premium Calculation System",
            "Claim Assessment Engine",
            "System Operation Intelligence",
        ],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/configuration-status")
async def get_gemini_configuration_status():
    """
    Check if Gemini API is properly configured
    """
    api_key_set = bool(os.getenv("GEMINI_API_KEY"))

    status_info = {
        "gemini_api_configured": api_key_set,
        "service_status": "available" if api_key_set else "requires_api_key",
        "primary_function": "natural_language_analysis",
        "integration_role": "complements_specialized_climate_models",
        "recommendation": (
            "Configure GEMINI_API_KEY in .env file for full functionality"
            if not api_key_set
            else "Gemini integration ready for use"
        ),
        "security_notice": "Be cautious with sensitive data as it's processed by external API",
        "timestamp": datetime.now().isoformat(),
    }

    return status_info

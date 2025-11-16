"""
API Router for Integrated Pipeline - Complete Module Integration
Implements the complete pipeline: Proponent Data -> SCR -> AAT -> EPC -> MDS
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from services.integrated_pipeline_service import (
    run_complete_pipeline,
    PipelineInput,
    ApplicationData,
    ClimateData,
    HistoricalLossData,
    MarketData,
    RiskCategory,
    process_application,
    get_pipeline_summary
)

router = APIRouter()

@router.post("/integrated-pipeline/process")
async def process_integrated_pipeline(
    applicant_id: str = Query(..., description="Unique applicant identifier"),
    coverage_requested: float = Query(..., gt=0, description="Amount of coverage requested"),
    coverage_type: str = Query("property", description="Type of coverage (property, agriculture, infrastructure, livestock, crop)"),
    asset_value: float = Query(..., gt=0, description="Value of the asset to be insured"),
    latitude: float = Query(..., ge=-90, le=90, description="Latitude of the insured asset"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude of the insured asset"),
    climate_data_input: Dict[str, Any] = None,
    loss_history: List[Dict[str, Any]] = None,
    market_conditions: Dict[str, Any] = None
):
    """
    Complete integrated pipeline processing:
    Proponent Data -> Score Climático de Risco (SCR) -> Análise Atuarial Tradicional (AAT) 
    -> Engine de Precificação Comercial (EPC) -> Matriz de Decisão de Subscrição (MDS)
    -> OUTPUT: Decisão + Prêmio + Condições + Justificativa
    """
    if climate_data_input is None:
        climate_data_input = {}
    if loss_history is None:
        loss_history = []
    if market_conditions is None:
        market_conditions = {}
    
    try:
        result = await run_complete_pipeline(
            applicant_id=applicant_id,
            coverage_requested=coverage_requested,
            coverage_type=coverage_type,
            asset_value=asset_value,
            location_coordinates=(latitude, longitude),
            climate_data_input=climate_data_input,
            loss_history=loss_history,
            market_conditions=market_conditions
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

@router.post("/integrated-pipeline/process-direct")
async def process_integrated_pipeline_direct(pipeline_input: PipelineInput):
    """
    Direct interface to the integrated pipeline with complete input structure
    """
    try:
        result = process_application(pipeline_input)
        summary = get_pipeline_summary(result)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

@router.get("/integrated-pipeline/info")
async def integrated_pipeline_info():
    """
    Get information about the integrated pipeline system
    """
    return {
        "description": "Integrated Insurance Underwriting Pipeline",
        "modules": [
            {
                "name": "SCR (Score Climático de Risco)",
                "function": "Climate risk assessment and scoring"
            },
            {
                "name": "AAT (Análise Atuarial Tradicional)", 
                "function": "Traditional actuarial analysis and premium calculation"
            },
            {
                "name": "EPC (Engine de Precificação Comercial)",
                "function": "Commercial pricing with market and competitive factors"
            },
            {
                "name": "MDS (Matriz de Decisão de Subscrição)",
                "function": "Underwriting decision matrix with conditions"
            }
        ],
        "process_flow": "Proponent Data -> SCR -> AAT -> EPC -> MDS -> Decision + Premium + Conditions + Justification",
        "output_fields": [
            "final_decision",
            "final_premium", 
            "coverage_amount",
            "risk_score",
            "profit_margin",
            "underwriting_conditions",
            "pricing_strategy",
            "market_position",
            "confidence_level"
        ],
        "features": [
            "End-to-end automation",
            "Climate risk integration",
            "Actuarial soundness",
            "Commercial viability",
            "Regulatory compliance",
            "Real-time processing"
        ]
    }

# Individual module endpoints for testing and debugging

@router.post("/scr/assess")
async def scr_assess(
    temperature_data: List[Dict[str, float]] = None,
    precipitation_data: List[Dict[str, float]] = None,
    wind_data: List[Dict[str, float]] = None,
    location_coordinates: Tuple[float, float] = (-23.5507, -46.6339)  # Default to São Paulo
):
    """
    Direct interface to Score Climático de Risco module
    """
    if temperature_data is None:
        temperature_data = []
    if precipitation_data is None:
        precipitation_data = []
    if wind_data is None:
        wind_data = []
    
    from services.scr_module_service import ClimateData, calculate_climate_risk_score
    
    climate_data = ClimateData(
        temperature_data=temperature_data,
        precipitation_data=precipitation_data,
        wind_data=wind_data,
        historical_extremes={},
        climate_projections=[],
        location_coordinates=location_coordinates,
        coverage_period_months=12,
        asset_value=100000.0
    )
    
    try:
        result = calculate_climate_risk_score(climate_data)
        return {
            "overall_score": result.overall_score,
            "risk_breakdown": result.risk_breakdown,
            "temporal_trend": result.temporal_trend,
            "confidence_level": result.confidence_level,
            "risk_assessment_date": result.risk_assessment_date.isoformat(),
            "climate_indices": result.climate_indices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SCR assessment failed: {str(e)}")

@router.post("/aat/analyze")
async def aat_analyze(
    claims_history: List[Dict[str, Any]] = None,
    total_exposure: float = 1000000.0,
    asset_value: float = 500000.0
):
    """
    Direct interface to Análise Atuarial Tradicional module
    """
    if claims_history is None:
        claims_history = []
    
    from services.aat_module_service import HistoricalLossData, RiskCategory, perform_actuarial_analysis
    
    loss_data = HistoricalLossData(
        claims_history=claims_history,
        exposure_data=[],
        policy_count=max(1, len(claims_history)),
        total_exposure=total_exposure,
        coverage_type=RiskCategory.PROPERTY,
        location_coordinates=(-23.5507, -46.6339),
        asset_value=asset_value,
        coverage_period_years=3.0
    )
    
    try:
        result = perform_actuarial_analysis(loss_data)
        return {
            "pure_premium": result.pure_premium,
            "total_premium": result.total_premium,
            "frequency": result.frequency,
            "severity": result.severity,
            "expected_loss": result.expected_loss,
            "risk_classification": result.risk_classification,
            "actuarial_indicators": result.actuarial_indicators
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AAT analysis failed: {str(e)}")

@router.post("/epc/price")
async def epc_price(
    actuarial_premium: float = Query(5000.0, description="Base actuarial premium"),
    climate_risk_score: float = Query(0.3, description="Climate risk score"),
    market_conditions: Dict[str, Any] = None
):
    """
    Direct interface to Engine de Precificação Comercial module
    """
    if market_conditions is None:
        market_conditions = {}
    
    from services.epe_module_service import RiskAdjustedPremium, MarketData, PricingStrategy, calculate_commercial_pricing
    
    risk_adjusted = RiskAdjustedPremium(
        actuarial_premium=actuarial_premium,
        climate_risk_adjustment=climate_risk_score * 0.1,
        total_adjusted_premium=actuarial_premium * (1 + climate_risk_score * 0.1),
        risk_score=climate_risk_score,
        risk_components={}
    )
    
    market_data = MarketData(
        competitor_rates=market_conditions.get('competitor_rates', {}),
        market_average_rate=market_conditions.get('market_average_rate', actuarial_premium),
        market_std_rate=market_conditions.get('market_std_rate', actuarial_premium * 0.2),
        market_growth_rate=market_conditions.get('market_growth_rate', 0.05),
        market_size=market_conditions.get('market_size', 10000),
        market_penetration=market_conditions.get('market_penetration', 0.15),
        economic_indicators=market_conditions.get('economic_indicators', {'inflation': 0.03, 'gdp_growth': 0.02}),
        regulatory_factors=market_conditions.get('regulatory_factors', {}),
        seasonal_factors=market_conditions.get('seasonal_factors', {}),
        region_premiums=market_conditions.get('region_premiums', {}),
        customer_segments=market_conditions.get('customer_segments', {})
    )
    
    try:
        result = calculate_commercial_pricing(
            risk_adjusted,
            market_data,
            PricingStrategy.MARKET_MATCHING
        )
        return {
            "base_premium": result.base_premium,
            "final_premium": result.final_premium,
            "market_factor": result.market_factor,
            "competition_factor": result.competition_factor,
            "pricing_strategy": result.pricing_strategy,
            "market_position": result.market_position
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EPC pricing failed: {str(e)}")

@router.post("/mds/decide")
async def mds_decide(
    applicant_id: str,
    coverage_requested: float,
    climate_risk_score: float,
    actuarial_premium: float,
    commercial_premium: float
):
    """
    Direct interface to Matriz de Decisão de Subscrição module
    """
    from services.mds_module_service import ApplicationData, ModuleInputs, make_underwriting_decision
    
    application = ApplicationData(
        applicant_id=applicant_id,
        coverage_requested=coverage_requested,
        coverage_type="property",
        asset_value=coverage_requested * 1.2,  # Assumed asset value
        location_coordinates=(-23.5507, -46.6339),
        applicant_profile={},
        policy_features={},
        historical_claims=[]
    )
    
    module_inputs = ModuleInputs(
        climate_risk_score=climate_risk_score,
        climate_risk_breakdown={'overall': climate_risk_score},
        actuarial_premium=actuarial_premium,
        actuarial_indicators={'loss_ratio': 0.7},
        commercial_premium=commercial_premium,
        market_position="competitive",
        pricing_strategy="market_matching"
    )
    
    try:
        result = make_underwriting_decision(application, module_inputs)
        return {
            "decision": result.decision.value,
            "conditions": [c.value for c in result.conditions],
            "risk_score": result.risk_score,
            "profit_margin": result.profit_margin,
            "justification": result.justification,
            "confidence_level": result.confidence_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MDS decision failed: {str(e)}")
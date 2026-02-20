"""
Integração dos Módulos - Complete Pipeline Integration
Implements the complete pipeline connecting SCR -> AAT -> EPC -> MDS modules.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from services.aat_module_service import (
    ActuarialAnalysisResult,
    HistoricalLossData,
    RiskCategory,
    AATModuleService,
    calculate_reinsurance_requirements,
    perform_actuarial_analysis,
)
from services.epe_module_service import (
    EPEModuleService,
    CommercialPricingResult,
    MarketData,
    PricingStrategy,
    RiskAdjustedPremium,
    calculate_commercial_pricing,
    get_pricing_strategy_recommendation,
)
from services.mds_module_service import (
    ApplicationData,
    ModuleInputs,
    UnderwritingDecision,
    MDSModuleService,
    apply_policy_rules,
    make_underwriting_decision,
)

# Import all module services
from services.scr_module_service import (
    ClimateData,
    ClimateRiskScore,
    SCRModuleService,
    calculate_climate_risk_score,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete result from the integrated pipeline"""

    application_id: str
    scr_result: ClimateRiskScore
    aat_result: ActuarialAnalysisResult
    epc_result: CommercialPricingResult
    mds_result: UnderwritingDecision
    final_decision: str
    final_premium: float
    coverage_amount: float
    risk_score: float
    profit_margin: float
    processing_timestamp: datetime
    pipeline_duration: float  # in seconds


@dataclass
class PipelineInput:
    """Input for the complete pipeline"""

    application_data: ApplicationData
    climate_data: ClimateData
    loss_data: HistoricalLossData
    market_data: MarketData


class IntegratedPipeline:
    """
    Complete integrated pipeline connecting all four modules:
    Proponent Data -> SCR -> AAT -> EPC -> MDS -> Decision + Premium + Conditions + Justification
    """

    def __init__(self):
        self.scr_engine = SCRModuleService()
        self.aat_engine = AATModuleService()
        self.epe_engine = EPEModuleService()
        self.mds_engine = MDSModuleService()

    def process_application(self, pipeline_input: PipelineInput) -> PipelineResult:
        """
        Process an application through the complete pipeline

        Args:
            pipeline_input: Complete input data for the application

        Returns:
            PipelineResult with complete decision and analysis
        """
        start_time = datetime.now()

        # Step 1: Score Climático de Risco (SCR)
        logger.info(
            f"Starting SCR analysis for application {pipeline_input.application_data.applicant_id}"
        )
        scr_result = calculate_climate_risk_score(pipeline_input.climate_data)

        # Step 2: Análise Atuarial Tradicional (AAT)
        logger.info("Starting AAT analysis")
        aat_result = perform_actuarial_analysis(pipeline_input.loss_data)

        # Step 3: Engine de Precificação Comercial (EPC)
        logger.info("Starting EPC analysis")
        # Prepare risk-adjusted premium input for EPC
        risk_adjusted_premium = RiskAdjustedPremium(
            actuarial_premium=aat_result.total_premium,
            climate_risk_adjustment=scr_result.overall_score * 0.1,  # Climate factor
            total_adjusted_premium=aat_result.total_premium
            * (1 + scr_result.overall_score * 0.1),
            risk_score=scr_result.overall_score,
            risk_components=scr_result.risk_breakdown,
        )

        epc_result = calculate_commercial_pricing(
            risk_adjusted_premium, pipeline_input.market_data
        )

        # Step 4: Matriz de Decisão de Subscrição (MDS)
        logger.info("Starting MDS analysis")
        # Prepare inputs for MDS
        module_inputs = ModuleInputs(
            climate_risk_score=scr_result.overall_score,
            climate_risk_breakdown=scr_result.risk_breakdown,
            actuarial_premium=aat_result.total_premium,
            actuarial_indicators=aat_result.actuarial_indicators,
            commercial_premium=epc_result.final_premium,
            market_position=epc_result.market_position,
            pricing_strategy=epc_result.pricing_strategy,
        )

        mds_result = make_underwriting_decision(
            pipeline_input.application_data, module_inputs
        )

        # Apply policy rules
        policy_rule_results = apply_policy_rules(
            pipeline_input.application_data, module_inputs
        )

        # Calculate final metrics
        final_premium = epc_result.final_premium
        risk_score = scr_result.overall_score
        profit_margin = epc_result.target_profit_margin

        # Determine final decision
        final_decision = mds_result.decision.value

        # Calculate processing duration
        duration = (datetime.now() - start_time).total_seconds()

        # Create final result
        result = PipelineResult(
            application_id=pipeline_input.application_data.applicant_id,
            scr_result=scr_result,
            aat_result=aat_result,
            epc_result=epc_result,
            mds_result=mds_result,
            final_decision=final_decision,
            final_premium=final_premium,
            coverage_amount=pipeline_input.application_data.coverage_requested,
            risk_score=risk_score,
            profit_margin=profit_margin,
            processing_timestamp=datetime.now(),
            pipeline_duration=duration,
        )

        logger.info(
            f"Pipeline processing completed for application {result.application_id} in {duration:.2f}s"
        )
        return result

    def process_batch_applications(
        self, pipeline_inputs: List[PipelineInput]
    ) -> List[PipelineResult]:
        """
        Process multiple applications in batch

        Args:
            pipeline_inputs: List of pipeline input data

        Returns:
            List of pipeline results
        """
        results = []
        for pipeline_input in pipeline_inputs:
            try:
                result = self.process_application(pipeline_input)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Error processing application {pipeline_input.application_data.applicant_id}: {str(e)}"
                )
                # In a real implementation, we might want to return error results
                continue

        return results

    def get_pipeline_summary(self, pipeline_result: PipelineResult) -> Dict[str, Any]:
        """
        Generate a summary of the pipeline processing

        Args:
            pipeline_result: Result from pipeline processing

        Returns:
            Dictionary with summary information
        """
        return {
            "application_id": pipeline_result.application_id,
            "final_decision": pipeline_result.final_decision,
            "final_premium": pipeline_result.final_premium,
            "coverage_amount": pipeline_result.coverage_amount,
            "risk_score": pipeline_result.risk_score,
            "profit_margin": pipeline_result.profit_margin,
            "processing_time": pipeline_result.pipeline_duration,
            "climate_risk_breakdown": pipeline_result.scr_result.risk_breakdown,
            "market_position": pipeline_result.epc_result.market_position,
            "pricing_strategy": pipeline_result.epc_result.pricing_strategy,
            "underwriting_conditions": [
                c.value for c in pipeline_result.mds_result.conditions
            ],
            "confidence_level": pipeline_result.mds_result.confidence_level,
            "requires_review": pipeline_result.mds_result.review_required,
            "scr_temporal_trend": pipeline_result.scr_result.temporal_trend,
            "aat_risk_classification": pipeline_result.aat_result.risk_classification,
            "epc_elasticity_impact": pipeline_result.epc_result.price_elasticity_impact,
        }


# Global instance
integration_engine = IntegratedPipeline()


def process_application(pipeline_input: PipelineInput) -> PipelineResult:
    """Convenience function to process a single application through the pipeline"""
    return integration_engine.process_application(pipeline_input)


def process_batch_applications(
    pipeline_inputs: List[PipelineInput],
) -> List[PipelineResult]:
    """Convenience function to process multiple applications"""
    return integration_engine.process_batch_applications(pipeline_inputs)


def get_pipeline_summary(pipeline_result: PipelineResult) -> Dict[str, Any]:
    """Convenience function to get pipeline summary"""
    return integration_engine.get_pipeline_summary(pipeline_result)


# API endpoint for the complete pipeline
async def run_complete_pipeline(
    applicant_id: str,
    coverage_requested: float,
    coverage_type: str,
    asset_value: float,
    location_coordinates: Tuple[float, float],
    climate_data_input: Dict[str, Any],  # Temperature, precipitation, wind data
    loss_history: List[Dict[str, Any]],  # Historical loss data
    market_conditions: Dict[str, Any],  # Market and competitor data
) -> Dict[str, Any]:
    """
    API endpoint for the complete integrated pipeline

    Args:
        applicant_id: Unique applicant identifier
        coverage_requested: Amount of coverage requested
        coverage_type: Type of coverage (property, agriculture, etc.)
        asset_value: Value of the asset to be insured
        location_coordinates: (latitude, longitude) of the insured asset
        climate_data_input: Climate data for risk assessment
        loss_history: Historical loss data for actuarial analysis
        market_conditions: Market conditions for commercial pricing

    Returns:
        Complete pipeline result as dictionary
    """
    # Prepare ApplicationData
    application_data = ApplicationData(
        applicant_id=applicant_id,
        coverage_requested=coverage_requested,
        coverage_type=coverage_type,
        asset_value=asset_value,
        location_coordinates=location_coordinates,
        applicant_profile={},  # Could be expanded with actual profile data
        policy_features={},  # Could be expanded with actual policy features
        historical_claims=loss_history,
    )

    # Prepare ClimateData
    climate_data = ClimateData(
        temperature_data=climate_data_input.get("temperature_data", []),
        precipitation_data=climate_data_input.get("precipitation_data", []),
        wind_data=climate_data_input.get("wind_data", []),
        historical_extremes=climate_data_input.get("historical_extremes", {}),
        climate_projections=climate_data_input.get("climate_projections", []),
        location_coordinates=location_coordinates,
        coverage_period_months=12,  # Default 1 year
        asset_value=asset_value,
    )

    # Prepare HistoricalLossData
    loss_data = HistoricalLossData(
        claims_history=loss_history,
        exposure_data=[],  # Could be expanded with exposure data
        policy_count=1,
        total_exposure=asset_value,
        coverage_type=(
            RiskCategory.PROPERTY
            if "property" in coverage_type.lower()
            else RiskCategory.AGRICULTURE
        ),
        location_coordinates=location_coordinates,
        asset_value=asset_value,
        coverage_period_years=3.0,  # Use 3 years of history if available
    )

    # Prepare MarketData
    market_data = MarketData(
        competitor_rates=market_conditions.get("competitor_rates", {}),
        market_average_rate=market_conditions.get("market_average_rate", 1000.0),
        market_std_rate=market_conditions.get("market_std_rate", 200.0),
        market_growth_rate=market_conditions.get("market_growth_rate", 0.05),
        market_size=market_conditions.get("market_size", 10000),
        market_penetration=market_conditions.get("market_penetration", 0.15),
        economic_indicators=market_conditions.get(
            "economic_indicators", {"inflation": 0.03, "gdp_growth": 0.02}
        ),
        regulatory_factors=market_conditions.get("regulatory_factors", {}),
        seasonal_factors=market_conditions.get("seasonal_factors", {}),
        region_premiums=market_conditions.get("region_premiums", {}),
        customer_segments=market_conditions.get("customer_segments", {}),
    )

    # Prepare pipeline input
    pipeline_input = PipelineInput(
        application_data=application_data,
        climate_data=climate_data,
        loss_data=loss_data,
        market_data=market_data,
    )

    # Process through pipeline
    result = process_application(pipeline_input)

    # Return as dictionary for API response
    summary = get_pipeline_summary(result)
    return summary

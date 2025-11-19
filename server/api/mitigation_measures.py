"""
API Router for Mitigation Measures Calculation Service
Implements: M_mitigação = Σ_k w_k·log(1 + efetividade_k)

Medidas ponderadas:
- Sistema de drenagem: 0.25 × ln(1 + capacidade_drenagem/area)
- Resistência estrutural: 0.30 × ln(1 + classe_resistência_vento)
- Sistema de monitoramento: 0.20 × ln(1 + sensores IoT)
- Cobertura vegetal: 0.15 × ln(1 + NDVI_local)
- Distância de refúgio: 0.10 × ln(1 + d_refugio)

Score Final: SCR = max(0, 1000 × (R_físico + R_transição + R_concentração) × (1 - M_mitigação))
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query

from services.mitigation_measures_service import (
    ClimateRiskComponents,
    MitigationCalculator,
    MitigationMeasures,
    calculate_cost_benefit_ratio,
    calculate_final_scr_score,
    calculate_mitigation_score,
    evaluate_mitigation_portfolio,
)

router = APIRouter()


@router.post("/mitigation/calculate-score")
async def calculate_mitigation_score_endpoint(
    drainage_capacity: float = Query(
        0.1, ge=0, description="Drainage capacity in m³/s per m² of area"
    ),
    area_drained: float = Query(
        10000, gt=0, description="Total area served by drainage system (m²)"
    ),
    structural_resistance_class: float = Query(
        5.0, ge=1, le=10, description="Wind/flood structural resistance class (1-10)"
    ),
    iot_sensors_count: int = Query(
        5, ge=0, description="Number of IoT sensors and monitoring devices"
    ),
    local_ndvi: float = Query(
        0.4,
        ge=0,
        le=1,
        description="Normalized Difference Vegetation Index (0-1 scale)",
    ),
    refuge_distance_km: float = Query(
        2.0, ge=0, description="Distance to nearest refuge in km"
    ),
    effectiveness_rating: float = Query(
        0.7, ge=0, le=1, description="Overall effectiveness rating (0-1 scale)"
    ),
    implementation_date: str = Query(
        None, description="Implementation date (YYYY-MM-DD)"
    ),
    maintenance_schedule: str = Query("quarterly", description="Maintenance schedule"),
):
    """
    Calculate mitigation score based on implemented measures
    M_mitigação = Σ_k w_k·log(1 + efetividade_k)
    """
    try:
        # Validate inputs
        if local_ndvi > 1.0 or local_ndvi < 0:
            raise HTTPException(status_code=400, detail="NDVI must be between 0 and 1")

        if structural_resistance_class < 1 or structural_resistance_class > 10:
            raise HTTPException(
                status_code=400,
                detail="Structural resistance class must be between 1 and 10",
            )

        # Parse implementation date
        parsed_date = datetime.now()
        if implementation_date:
            try:
                parsed_date = datetime.strptime(implementation_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
                )

        # Create mitigation measures object
        measures = MitigationMeasures(
            drainage_capacity=drainage_capacity,
            area_drained=area_drained,
            structural_resistance_class=structural_resistance_class,
            iot_sensors_count=iot_sensors_count,
            local_ndvi=local_ndvi,
            refuge_distance_km=refuge_distance_km,
            implementation_date=parsed_date,
            effectiveness_rating=effectiveness_rating,
            maintenance_schedule=maintenance_schedule,
        )

        # Calculate mitigation score
        result = calculate_mitigation_score(measures)

        return {
            "mitigation_score": result.mitigation_score,
            "mitigation_components": result.mitigation_components,
            "weighted_measure_factors": result.weighted_measure_factors,
            "risk_reduction_percentage": result.risk_reduction_percentage,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "mitigation_measures_summarized": {
                "drainage_capacity": measures.drainage_capacity,
                "area_drained": measures.area_drained,
                "structural_resistance_class": measures.structural_resistance_class,
                "iot_sensors_count": measures.iot_sensors_count,
                "local_ndvi": measures.local_ndvi,
                "refuge_distance_km": measures.refuge_distance_km,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Mitigation score calculation failed: {str(e)}"
        )


@router.post("/mitigation/calculate-final-scr-score")
async def calculate_final_scr_score_endpoint(
    # Risk components
    physical_risk: float = Query(..., ge=0, description="Physical risk (R_físico)"),
    transition_risk: float = Query(
        ..., ge=0, description="Transition risk (R_transição)"
    ),
    concentration_risk: float = Query(
        ..., ge=0, description="Concentration risk (R_concentração)"
    ),
    # Mitigation measure parameters
    drainage_capacity: float = Query(
        0.1, ge=0, description="Drainage capacity in m³/s per m² of area"
    ),
    area_drained: float = Query(
        10000, gt=0, description="Total area served by drainage system (m²)"
    ),
    structural_resistance_class: float = Query(
        5.0, ge=1, le=10, description="Wind/flood structural resistance class (1-10)"
    ),
    iot_sensors_count: int = Query(
        5, ge=0, description="Number of IoT sensors and monitoring devices"
    ),
    local_ndvi: float = Query(
        0.4,
        ge=0,
        le=1,
        description="Normalized Difference Vegetation Index (0-1 scale)",
    ),
    refuge_distance_km: float = Query(
        2.0, ge=0, description="Distance to nearest refuge in km"
    ),
    effectiveness_rating: float = Query(
        0.7, ge=0, le=1, description="Overall effectiveness rating (0-1 scale)"
    ),
    maintenance_schedule: str = Query("quarterly", description="Maintenance schedule"),
):
    """
    Calculate final climate risk score with mitigation:
    SCR = max(0, 1000 × (R_físico + R_transição + R_concentração) × (1 - M_mitigação))
    """
    try:
        # Validate inputs
        if local_ndvi > 1.0 or local_ndvi < 0:
            raise HTTPException(status_code=400, detail="NDVI must be between 0 and 1")

        if structural_resistance_class < 1 or structural_resistance_class > 10:
            raise HTTPException(
                status_code=400,
                detail="Structural resistance class must be between 1 and 10",
            )

        # Create risk components object
        risk_components = ClimateRiskComponents(
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=concentration_risk,
        )

        # Create mitigation measures object
        measures = MitigationMeasures(
            drainage_capacity=drainage_capacity,
            area_drained=area_drained,
            structural_resistance_class=structural_resistance_class,
            iot_sensors_count=iot_sensors_count,
            local_ndvi=local_ndvi,
            refuge_distance_km=refuge_distance_km,
            implementation_date=datetime.now(),
            effectiveness_rating=effectiveness_rating,
            maintenance_schedule=maintenance_schedule,
        )

        # Calculate final SCR score
        result = calculate_final_scr_score(risk_components, measures)

        return {
            "final_scr_score": result.final_scr_score,
            "mitigation_score": result.mitigation_score,
            "original_total_risk": result.original_total_risk,
            "mitigated_total_risk": result.mitigated_total_risk,
            "risk_reduction_percentage": result.risk_reduction_percentage,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "risk_components": {
                "physical_risk": risk_components.physical_risk,
                "transition_risk": risk_components.transition_risk,
                "concentration_risk": risk_components.concentration_risk,
            },
            "mitigation_measures": {
                "drainage_capacity": measures.drainage_capacity,
                "area_drained": measures.area_drained,
                "structural_resistance_class": measures.structural_resistance_class,
                "iot_sensors_count": measures.iot_sensors_count,
                "local_ndvi": measures.local_ndvi,
                "refuge_distance_km": measures.refuge_distance_km,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Final SCR score calculation failed: {str(e)}"
        )


@router.post("/mitigation/portfolio-evaluation")
async def portfolio_evaluation_endpoint(
    drainage_capacity: float = Query(
        0.1, ge=0, description="Drainage capacity in m³/s per m² of area"
    ),
    area_drained: float = Query(
        10000, gt=0, description="Total area served by drainage system (m²)"
    ),
    structural_resistance_class: float = Query(
        5.0, ge=1, le=10, description="Wind/flood structural resistance class (1-10)"
    ),
    iot_sensors_count: int = Query(
        5, ge=0, description="Number of IoT sensors and monitoring devices"
    ),
    local_ndvi: float = Query(
        0.4,
        ge=0,
        le=1,
        description="Normalized Difference Vegetation Index (0-1 scale)",
    ),
    refuge_distance_km: float = Query(
        2.0, ge=0, description="Distance to nearest refuge in km"
    ),
    effectiveness_rating: float = Query(
        0.7, ge=0, le=1, description="Overall effectiveness rating (0-1 scale)"
    ),
    desired_risk_reduction: float = Query(
        0.3, ge=0, le=1, description="Target risk reduction percentage (0-1)"
    ),
    maintenance_schedule: str = Query("quarterly", description="Maintenance schedule"),
):
    """
    Evaluate mitigation portfolio against desired risk reduction
    """
    try:
        # Validate inputs
        if local_ndvi > 1.0 or local_ndvi < 0:
            raise HTTPException(status_code=400, detail="NDVI must be between 0 and 1")

        if structural_resistance_class < 1 or structural_resistance_class > 10:
            raise HTTPException(
                status_code=400,
                detail="Structural resistance class must be between 1 and 10",
            )

        if desired_risk_reduction > 1.0 or desired_risk_reduction < 0:
            raise HTTPException(
                status_code=400, detail="Desired risk reduction must be between 0 and 1"
            )

        # Create mitigation measures object
        measures = MitigationMeasures(
            drainage_capacity=drainage_capacity,
            area_drained=area_drained,
            structural_resistance_class=structural_resistance_class,
            iot_sensors_count=iot_sensors_count,
            local_ndvi=local_ndvi,
            refuge_distance_km=refuge_distance_km,
            implementation_date=datetime.now(),
            effectiveness_rating=effectiveness_rating,
            maintenance_schedule=maintenance_schedule,
        )

        # Evaluate mitigation portfolio
        result = evaluate_mitigation_portfolio(measures, desired_risk_reduction)

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Mitigation portfolio evaluation failed: {str(e)}"
        )


@router.post("/mitigation/cost-benefit-analysis")
async def cost_benefit_analysis_endpoint(
    # Risk components
    physical_risk: float = Query(..., ge=0, description="Physical risk (R_físico)"),
    transition_risk: float = Query(
        ..., ge=0, description="Transition risk (R_transição)"
    ),
    concentration_risk: float = Query(
        ..., ge=0, description="Concentration risk (R_concentração)"
    ),
    # Mitigation measures
    drainage_capacity: float = Query(
        0.1, ge=0, description="Drainage capacity in m³/s per m² of area"
    ),
    area_drained: float = Query(
        10000, gt=0, description="Total area served by drainage system (m²)"
    ),
    structural_resistance_class: float = Query(
        5.0, ge=1, le=10, description="Wind/flood structural resistance class (1-10)"
    ),
    iot_sensors_count: int = Query(
        5, ge=0, description="Number of IoT sensors and monitoring devices"
    ),
    local_ndvi: float = Query(
        0.4,
        ge=0,
        le=1,
        description="Normalized Difference Vegetation Index (0-1 scale)",
    ),
    refuge_distance_km: float = Query(
        2.0, ge=0, description="Distance to nearest refuge in km"
    ),
    effectiveness_rating: float = Query(
        0.7, ge=0, le=1, description="Overall effectiveness rating (0-1 scale)"
    ),
    mitigation_cost: float = Query(
        ..., ge=0, description="Total cost of implementing mitigation measures"
    ),
    maintenance_schedule: str = Query("quarterly", description="Maintenance schedule"),
):
    """
    Calculate cost-benefit ratio of mitigation measures
    """
    try:
        # Validate inputs
        if local_ndvi > 1.0 or local_ndvi < 0:
            raise HTTPException(status_code=400, detail="NDVI must be between 0 and 1")

        if structural_resistance_class < 1 or structural_resistance_class > 10:
            raise HTTPException(
                status_code=400,
                detail="Structural resistance class must be between 1 and 10",
            )

        # Create risk components object
        risk_components = ClimateRiskComponents(
            physical_risk=physical_risk,
            transition_risk=transition_risk,
            concentration_risk=concentration_risk,
        )

        # Create mitigation measures object
        measures = MitigationMeasures(
            drainage_capacity=drainage_capacity,
            area_drained=area_drained,
            structural_resistance_class=structural_resistance_class,
            iot_sensors_count=iot_sensors_count,
            local_ndvi=local_ndvi,
            refuge_distance_km=refuge_distance_km,
            implementation_date=datetime.now(),
            effectiveness_rating=effectiveness_rating,
            maintenance_schedule=maintenance_schedule,
        )

        # Calculate cost-benefit ratio
        result = calculate_cost_benefit_ratio(
            measures, risk_components, mitigation_cost
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Cost-benefit analysis failed: {str(e)}"
        )


@router.get("/mitigation/info")
async def mitigation_info():
    """
    Get information about the mitigation measures calculation service
    """
    return {
        "description": "Mitigation Measures Calculation Service",
        "formula": "M_mitigação = Σ_k w_k·log(1 + efetividade_k)",
        "weighted_measures": {
            "drainage_system": "0.25 × ln(1 + capacidade_drenagem/area)",
            "structural_resistance": "0.30 × ln(1 + classe_resistência_vento)",
            "monitoring_system": "0.20 × ln(1 + sensores IoT)",
            "vegetation_cover": "0.15 × ln(1 + NDVI_local)",
            "refuge_distance": "0.10 × ln(1 + d_refugio)",
        },
        "final_score_formula": "SCR = max(0, 1000 × (R_físico + R_transição + R_concentração) × (1 - M_mitigação))",
        "methodology": "Climate Risk Mitigation Assessment",
        "features": [
            "Comprehensive mitigation measure evaluation",
            "Weighted scoring system for different measures",
            "Final SCR score calculation with mitigation discount",
            "Portfolio evaluation against desired risk reduction",
            "Cost-benefit analysis for mitigation investments",
            "Recommendation system for improving mitigation",
        ],
        "weights": {
            "drainage_system": 0.25,
            "structural_resistance": 0.30,
            "monitoring_system": 0.20,
            "vegetation_cover": 0.15,
            "refuge_distance": 0.10,
        },
        "input_requirements": {
            "drainage": "Capacity in m³/s per m² and area served in m²",
            "structural_resistance": "Class rating from 1-10 scale",
            "monitoring": "Number of IoT sensors deployed",
            "vegetation": "NDVI value between 0-1",
            "refuge": "Distance to nearest refuge in km",
        },
    }

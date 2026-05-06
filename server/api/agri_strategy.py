"""
Agricultural climate adaptation strategy API.
"""

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session
from services.agri_strategy_service import agri_strategy_service

router = APIRouter(prefix="/agri-strategy", tags=["agri-strategy"])


class FarmProfile(BaseModel):
    irrigation_available: bool = False
    drainage_level: Literal["low", "medium", "high"] = "medium"
    soil_cover_level: Literal["low", "medium", "high"] = "medium"
    farm_size_hectares: Optional[float] = Field(default=None, ge=0)


class AgriStrategyRequest(BaseModel):
    crop_type: str = Field(..., description="Crop type (e.g., soybean, corn, coffee)")
    phenological_stage: str = Field(
        ..., description="Crop stage (planning, planting, vegetative, flowering, grain_fill, harvest)"
    )
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    planning_horizon_days: int = Field(default=120, ge=7, le=365)
    risk_tolerance: Literal["low", "medium", "high"] = "medium"
    farm_profile: Optional[FarmProfile] = None


class AgriStrategyResponse(BaseModel):
    crop_type: str
    phenological_stage: str
    planning_horizon_days: int
    risk_tolerance: str
    climate_outlook: Dict[str, Any]
    exposure_scores: Dict[str, float]
    operational_actions: List[Dict[str, Any]]
    financial_actions: List[Dict[str, Any]]
    alert_triggers: List[Dict[str, Any]]
    supported_crops: List[str]
    supported_stages: List[str]


PLAN_REQUEST_EXAMPLE = {
    "crop_type": "soybean",
    "phenological_stage": "flowering",
    "latitude": -23.55,
    "longitude": -46.63,
    "planning_horizon_days": 120,
    "risk_tolerance": "medium",
    "farm_profile": {
        "irrigation_available": False,
        "drainage_level": "medium",
        "soil_cover_level": "high",
        "farm_size_hectares": 180,
    },
}

PLAN_RESPONSE_EXAMPLE = {
    "crop_type": "soybean",
    "phenological_stage": "flowering",
    "planning_horizon_days": 120,
    "risk_tolerance": "medium",
    "climate_outlook": {
        "enso": {
            "source": "database",
            "regime_label": "la_nina",
            "regime_confidence": "high",
            "impact_risk_modifier": 1.08,
            "reference_date": "2026-04-01",
        },
        "forecast_source": "NOAA/NWS",
    },
    "exposure_scores": {
        "heat": 0.42,
        "drought": 0.38,
        "excess_rain": 0.74,
        "flood": 0.69,
        "wind": 0.41,
        "disease": 0.63,
    },
    "operational_actions": [
        {
            "horizon": "0-14d",
            "category": "drainage",
            "priority": "high",
            "action": "Clear drainage channels and prepare runoff diversion",
            "rationale": "Excess water and flooding risk can damage root systems and delay operations.",
        }
    ],
    "financial_actions": [
        {
            "type": "parametric_insurance",
            "priority": "high",
            "strategy": "Use cumulative rainfall and flood-day triggers",
            "expected_benefit": "Protect revenue against excess-rain events",
        }
    ],
    "alert_triggers": [
        {
            "name": "excess_rain_7d",
            "condition": "accumulated_rainfall_7d > climatology_p80",
            "recommended_response": "Activate drainage protocol and disease prevention",
        }
    ],
    "supported_crops": ["soybean", "corn", "coffee"],
    "supported_stages": ["planning", "planting", "vegetative", "flowering", "grain_fill", "harvest"],
}


@router.post(
    "/plan",
    response_model=AgriStrategyResponse,
    summary="Generate agricultural adaptation plan",
    responses={
        200: {
            "description": "Strategy plan generated successfully",
            "content": {
                "application/json": {
                    "example": PLAN_RESPONSE_EXAMPLE,
                }
            },
        },
        422: {"description": "Invalid request payload"},
        500: {"description": "Internal strategy generation error"},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": PLAN_REQUEST_EXAMPLE,
                }
            }
        }
    },
)
async def generate_agri_strategy_plan(
    payload: AgriStrategyRequest,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        response = await agri_strategy_service.generate_plan(
            crop_type=payload.crop_type,
            phenological_stage=payload.phenological_stage,
            latitude=payload.latitude,
            longitude=payload.longitude,
            planning_horizon_days=payload.planning_horizon_days,
            risk_tolerance=payload.risk_tolerance,
            farm_profile=payload.farm_profile.model_dump() if payload.farm_profile else None,
            db=db,
        )
        return response
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate strategy plan: {exc}")


@router.get("/catalog")
async def get_strategy_catalog():
    return {
        "supported_crops": agri_strategy_service.supported_crops,
        "supported_stages": agri_strategy_service.supported_stages,
        "risk_dimensions": ["heat", "drought", "excess_rain", "flood", "wind", "disease"],
    }


@router.get("/health")
async def health_agri_strategy():
    return {"status": "healthy", "module": "agri-strategy", "version": "1.0.0"}

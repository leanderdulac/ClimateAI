"""
Router for Climate Data Endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from models.schemas import ClimaData
from services.advanced_actuarial_service import AdvancedActuarialService
from services.climate_insight_service import climate_insight_service
from services.embrapa_service import embrapa_service
from services.openmeteo_service import OpenMeteoService

router = APIRouter()
openmeteo_service = OpenMeteoService()
advanced_actuarial_service = AdvancedActuarialService()


@router.get("/historico", tags=["Climate Data"])
async def get_historical_climate(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    data_inicio: str = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="End date (YYYY-MM-DD)"),
    variable: Optional[str] = Query(None),
):
    """
    Get historical climate data for a specific location.

    - **latitude**: Latitude of the location (-90 to 90)
    - **longitude**: Longitude of the location (-180 to 180)
    - **data_inicio**: Start date for the data query (YYYY-MM-DD)
    - **data_fim**: End date for the data query (YYYY-MM-DD)
    - **variable**: Filter by a specific variable (optional)
    """
    try:
        # Parse dates safely
        start_date_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
        end_date_obj = datetime.strptime(data_fim, "%Y-%m-%d")
        
        # Use Embrapa with a fallback to OpenMeteo if needed
        data = await embrapa_service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            start_date=data_inicio,
            end_date=data_fim,
        )
        return {
            "data": data,
            "source": "Embrapa",
            "period": {
                "start": start_date_obj.strftime("%Y-%m-%d"),
                "end": end_date_obj.strftime("%Y-%m-%d"),
            },
        }
    except Exception as e:
        # Specific error handling could be improved here
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "message": "Failed to retrieve historical data.",
                "suggestion": "Try reducing the time span or using another data source.",
            },
        )


@router.get("/atual", response_model=ClimaData, tags=["Climate Data"])
async def get_current_climate(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """
    Get current weather conditions for a specific location.
    """
    try:
        now = datetime.now()
        data = await embrapa_service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            start_date=now.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d"),
        )
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current climate data not found.",
            )
        return data[0]
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get("/previsao", tags=["Climate Data"])
async def get_climate_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=16),
):
    """
    Get weather forecast for the next few days using OpenMeteo.
    """
    try:
        forecast_data = await openmeteo_service.get_forecast(
            latitude=latitude, longitude=longitude, days=days
        )
        return {
            "forecast": forecast_data,
            "location": {"latitude": latitude, "longitude": longitude},
            "period_days": days,
            "source": "OpenMeteo",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching forecast: {str(e)}",
        )


@router.get("/agricultural-zoning", tags=["Agricultural Analysis"])
async def get_agricultural_zoning(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    crop: str = Query(...),
):
    """
    Get agricultural climate risk zoning (ZARC).
    """
    try:
        return await embrapa_service.get_agricultural_zoning(
            latitude=latitude, longitude=longitude, crop=crop
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/risk-analysis", tags=["Agricultural Analysis"])
async def get_risk_analysis(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """
    Get climate risk analysis.
    """
    try:
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None
        return await embrapa_service.get_risk_analysis(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date_str,
            end_date=end_date_str,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/insights", tags=["Climate Data"])
async def get_climate_insights(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """
    Get analyzed climate insights and predominant extreme event risks for a location.
    Analyzes the last 2 years of historical data.
    """
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        # Fetch historical data
        climate_data = await embrapa_service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        # Analyze insights
        insights = climate_insight_service.analyze_location_insights(climate_data)

        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao gerar insights climáticos: {str(e)}"
        )


@router.post("/advanced-premium-calculation", tags=["Actuarial Science"])
async def calculate_advanced_premium(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    frequency: float = Query(..., ge=0, le=100),
    severity: float = Query(..., gt=0),
    asset_value: float = Query(..., gt=0),
    confidence_level: float = Query(95, ge=50, le=99.9),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """
    Advanced premium calculation using sophisticated mathematical techniques:
    - Fractal analysis, Monte Carlo simulation, Fuzzy logic, Statistical Physics, and Actuarial calculations.
    """
    try:
        if start_date and end_date:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
        else:
            end_date_str = datetime.now().strftime("%Y-%m-%d")
            start_date_str = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        if not embrapa_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Actuarial analysis service is not configured. Set EMBRAPA_API_KEY in the .env file.",
            )

        climate_data = await embrapa_service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date_str,
            end_date=end_date_str,
        )

        premium_result = advanced_actuarial_service.calculate_comprehensive_premium(
            frequency=frequency,
            severity=severity,
            asset_value=asset_value,
            confidence_level=confidence_level,
            climate_data=climate_data,
        )

        return {
            "pure_premium": round(premium_result.pure_premium, 2),
            "loading_premium": round(premium_result.loading_premium, 2),
            "risk_margin": round(premium_result.risk_margin, 2),
            "total_premium": round(premium_result.total_premium, 2),
            "confidence_interval": {
                "lower": round(premium_result.confidence_interval[0], 2),
                "upper": round(premium_result.confidence_interval[1], 2),
            },
            "fractal_analysis": {
                "dimension": round(premium_result.fractal_dimension.dimension, 3),
                "lacunarity": round(premium_result.fractal_dimension.lacunarity, 3),
                "persistence": round(premium_result.fractal_dimension.persistence, 3),
            },
            "fuzzy_risk": {
                "very_low": round(premium_result.fuzzy_risk.very_low, 3),
                "low": round(premium_result.fuzzy_risk.low, 3),
                "medium": round(premium_result.fuzzy_risk.medium, 3),
                "high": round(premium_result.fuzzy_risk.high, 3),
                "very_high": round(premium_result.fuzzy_risk.very_high, 3),
            },
            "input_parameters": {
                "latitude": latitude,
                "longitude": longitude,
                "frequency": frequency,
                "severity": severity,
                "asset_value": asset_value,
                "confidence_level": confidence_level,
                "analysis_period": {"start": start_date_str, "end": end_date_str},
            },
            "methodology": {
                "monte_carlo_iterations": advanced_actuarial_service.monte_carlo_iterations,
                "techniques_used": [
                    "Fractal Calculation (Box-counting)",
                    "Advanced Monte Carlo Simulation",
                    "Fuzzy Logic",
                    "Statistical Physics",
                    "Insurance Industry Actuarial Calculations",
                ],
            },
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "message": "Failed in advanced premium calculation.",
                "suggestion": "Check the input parameters and try again.",
            },
        )

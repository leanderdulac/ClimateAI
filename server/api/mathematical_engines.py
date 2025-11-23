"""
Router for advanced mathematical engines and extreme value analysis
Implements GEV/GPD, spatial statistics, and stochastic processes for climate risk modeling
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from services.extreme_value_service import (
    block_maxima_analysis,
    calculate_climate_adapted_gev_params,
    calculate_extreme_event_probability,
    calculate_return_level_with_climate_adaptation,
    combined_gev_gpd_analysis,
    extreme_value_service,
    gev_distribution_cdf,
    peaks_over_threshold_analysis,
)
from services.spatial_statistics_service import (
    calculate_kernel_density_estimation,
    calculate_spatial_correlation,
    combined_spatial_risk_assessment,
    geospatial_clustering,
    predict_at_new_locations,
    spatial_gaussian_process_model,
    spatial_statistics_service,
)
from services.stochastic_process_service import (
    fit_arima_model,
    fit_copula_model,
    forecast_arima,
    multivariate_climate_modeling,
    regime_switching_model,
    stochastic_process_service,
)

router = APIRouter()


@router.post("/extreme-value-analysis/gev")
async def extreme_value_gev_analysis(
    data: List[float], return_period: float = Query(50.0, ge=1.0, le=1000.0)
):
    """
    Perform Generalized Extreme Value (GEV) analysis for block maxima
    """
    try:
        if len(data) < 10:
            raise HTTPException(
                status_code=400, detail="Need at least 10 data points for GEV analysis"
            )

        result = block_maxima_analysis(data, block_size=min(365, len(data) // 10))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GEV analysis failed: {str(e)}")


@router.post("/extreme-value-analysis/gpd")
async def extreme_value_gpd_analysis(
    data: List[float], threshold: Optional[float] = Query(None)
):
    """
    Perform Generalized Pareto Distribution (GPD) analysis for exceedances
    """
    try:
        if len(data) < 5:
            raise HTTPException(
                status_code=400, detail="Need at least 5 data points for GPD analysis"
            )

        # Use 90th percentile as default threshold if not provided
        if threshold is None:
            threshold = float(np.percentile(data, 90))

        result = peaks_over_threshold_analysis(data, threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPD analysis failed: {str(e)}")


@router.post("/extreme-value-analysis/combined")
async def extreme_value_combined_analysis(
    data: List[float], threshold: Optional[float] = Query(None)
):
    """
    Perform combined GEV and GPD analysis for comprehensive extreme value modeling
    """
    try:
        if len(data) < 20:
            raise HTTPException(
                status_code=400,
                detail="Need at least 20 data points for combined analysis",
            )

        result = combined_gev_gpd_analysis(data, threshold)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Combined analysis failed: {str(e)}"
        )


@router.post("/extreme-value-analysis/gev-cdf")
async def gev_distribution_cdf_endpoint(
    z: float,
    mu: float = Query(..., description="Location parameter (μ)"),
    sigma: float = Query(..., ge=0, description="Scale parameter (σ)"),
    xi: float = Query(..., description="Shape parameter (ξ)"),
):
    """
    Calculate CDF of Generalized Extreme Value distribution using the formula:
    G(z) = exp{ -[1 + ξ((z-μ)/σ)]^(-1/ξ) }
    """
    try:
        result = gev_distribution_cdf(z, mu, sigma, xi)
        return {
            "cdf_value": result,
            "z": z,
            "parameters": {"mu": mu, "sigma": sigma, "xi": xi},
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"GEV CDF calculation failed: {str(e)}"
        )


@router.post("/extreme-value-analysis/climate-adapted-gev")
async def calculate_climate_adapted_gev_endpoint(
    base_location: float = Query(..., description="Base location parameter (μ₀)"),
    base_scale: float = Query(..., ge=0, description="Base scale parameter (σ₀)"),
    base_shape: float = Query(..., description="Base shape parameter (ξ₀)"),
    delta_temperature: float = Query(0.0, description="Change in temperature (ΔT)"),
    delta_precipitation: float = Query(
        0.0, description="Change in precipitation (ΔPrecip)"
    ),
    co2_level: float = Query(420.0, description="CO2 concentration level"),
    alpha: float = Query(0.02, description="Temperature sensitivity (α)"),
    beta: float = Query(0.01, description="Precipitation sensitivity (β)"),
    gamma: float = Query(0.001, description="CO2 sensitivity (γ)"),
):
    """
    Calculate climate-adapted GEV parameters using the model:
    μ_t = μ_0 × (1 + α·ΔT_t + β·ΔPrecip_t)
    σ_t = σ_0 × exp(γ·CO2_t)
    """
    try:
        from services.extreme_value_service import GEVParameters

        base_params = GEVParameters(
            location=base_location,
            scale=base_scale,
            shape=base_shape,
            return_period=100.0,  # Default to 100-year return period
            confidence_interval=(0.0, 0.0),  # Placeholder
        )

        result = calculate_climate_adapted_gev_params(
            base_params,
            delta_temperature,
            delta_precipitation,
            co2_level,
            alpha,
            beta,
            gamma,
        )

        return {
            "base_parameters": {
                "location": base_location,
                "scale": base_scale,
                "shape": base_shape,
            },
            "adapted_parameters": {
                "location": result.location,
                "scale": result.scale,
                "shape": result.shape,
            },
            "climate_factors": {
                "delta_temperature": delta_temperature,
                "delta_precipitation": delta_precipitation,
                "co2_level": co2_level,
                "alpha": alpha,
                "beta": beta,
                "gamma": gamma,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Climate-adapted GEV calculation failed: {str(e)}"
        )


@router.post("/extreme-value-analysis/climate-adapted-return-level")
async def calculate_climate_adapted_return_level_endpoint(
    base_location: float = Query(..., description="Base location parameter (μ₀)"),
    base_scale: float = Query(..., ge=0, description="Base scale parameter (σ₀)"),
    base_shape: float = Query(..., description="Base shape parameter (ξ₀)"),
    delta_temperature: float = Query(0.0, description="Change in temperature (ΔT)"),
    delta_precipitation: float = Query(
        0.0, description="Change in precipitation (ΔPrecip)"
    ),
    co2_level: float = Query(420.0, description="CO2 concentration level"),
    return_period: float = Query(100.0, ge=1.0, description="Return period"),
    alpha: float = Query(0.02, description="Temperature sensitivity (α)"),
    beta: float = Query(0.01, description="Precipitation sensitivity (β)"),
    gamma: float = Query(0.001, description="CO2 sensitivity (γ)"),
):
    """
    Calculate return level accounting for climate adaptation
    """
    try:
        from services.extreme_value_service import GEVParameters

        base_params = GEVParameters(
            location=base_location,
            scale=base_scale,
            shape=base_shape,
            return_period=return_period,
            confidence_interval=(0.0, 0.0),  # Placeholder
        )

        result = calculate_return_level_with_climate_adaptation(
            base_params,
            delta_temperature,
            delta_precipitation,
            co2_level,
            return_period,
            alpha,
            beta,
            gamma,
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Climate-adapted return level calculation failed: {str(e)}",
        )


@router.post("/spatial-analysis/gaussian-process")
async def spatial_gaussian_process_endpoint(
    coordinates: List[List[float]],  # List of [lat, lon] pairs
    observations: List[float],
    covariates: Optional[List[List[float]]] = None,
    nugget: float = Query(0.1, ge=0.0, description="Nugget effect parameter (η²)"),
    range_param: float = Query(1.0, ge=0.1, description="Range parameter (φ)"),
    variance_param: float = Query(1.0, ge=0.1, description="Variance parameter (σ²)"),
):
    """
    Fit a spatial Gaussian Process model:
    Z(s) = X(s)β + W(s) + ε(s)
    W(s) ~ Gaussian Process(0, Σ(θ))
    Σ_ij = σ² exp(-||s_i - s_j||/φ) + η²·I(i=j)
    """
    try:
        # Validate coordinates format
        for coord in coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]",
                )

        # Convert coordinates to tuples
        coord_tuples = [(coord[0], coord[1]) for coord in coordinates]

        if len(coord_tuples) != len(observations):
            raise HTTPException(
                status_code=400,
                detail="Coordinates and observations must have same length",
            )

        result = spatial_gaussian_process_model(
            coord_tuples, observations, covariates, nugget, range_param, variance_param
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Spatial Gaussian Process model fitting failed: {str(e)}",
        )


@router.post("/spatial-analysis/gaussian-process-prediction")
async def predict_at_new_locations_endpoint(
    fitted_model: Dict[str, Any],
    new_coordinates: List[List[float]],  # List of [lat, lon] pairs
    new_covariates: Optional[List[List[float]]] = None,
):
    """
    Predict at new locations using a fitted spatial GP model
    """
    try:
        # Validate coordinates format
        for coord in new_coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]",
                )

        # Convert coordinates to tuples
        new_coord_tuples = [(coord[0], coord[1]) for coord in new_coordinates]

        result = predict_at_new_locations(
            fitted_model, new_coord_tuples, new_covariates
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Spatial Gaussian Process prediction failed: {str(e)}",
        )


@router.post("/extreme-value-analysis/event-probability")
async def calculate_extreme_event_probability_endpoint(
    data: List[float], threshold: float, event_magnitude: float
):
    """
    Calculate probability of extreme events using GPD model
    """
    try:
        result = calculate_extreme_event_probability(data, threshold, event_magnitude)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Event probability calculation failed: {str(e)}"
        )


@router.post("/spatial-analysis/kde")
async def spatial_kde_analysis(
    coordinates: List[List[float]],  # List of [lat, lon] pairs
    values: Optional[List[float]] = None,
    bandwidth: float = Query(0.5, ge=0.1, le=5.0),
):
    """
    Perform Kernel Density Estimation for spatial exposure modeling
    """
    try:
        if len(coordinates) < 2:
            raise HTTPException(
                status_code=400, detail="Need at least 2 coordinates for KDE analysis"
            )

        # Validate coordinates format
        for coord in coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]",
                )

        # Convert to tuples of (lat, lon)
        coord_tuples = [(coord[0], coord[1]) for coord in coordinates]

        result = calculate_kernel_density_estimation(coord_tuples, values, bandwidth)
        return {"kde_values": result.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KDE analysis failed: {str(e)}")


@router.post("/spatial-analysis/correlation")
async def spatial_correlation_analysis(
    coordinates: List[List[float]],  # List of [lat, lon] pairs
    values: List[float],
    max_distance: float = Query(100.0, ge=10.0, le=1000.0),
):
    """
    Calculate spatial correlation using geographic distances
    """
    try:
        if len(coordinates) < 2 or len(coordinates) != len(values):
            raise HTTPException(
                status_code=400,
                detail="Need same number of coordinates and values, at least 2 points",
            )

        # Validate coordinates format
        for coord in coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]",
                )

        # Convert to tuples of (lat, lon)
        coord_tuples = [(coord[0], coord[1]) for coord in coordinates]

        result = calculate_spatial_correlation(coord_tuples, values, max_distance)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Spatial correlation analysis failed: {str(e)}"
        )


@router.post("/spatial-analysis/clustering")
async def spatial_clustering_analysis(
    coordinates: List[List[float]],  # List of [lat, lon] pairs
    values: Optional[List[float]] = None,
    eps: float = Query(5.0, ge=0.1, le=50.0),
    min_samples: int = Query(3, ge=1, le=10),
):
    """
    Perform geospatial clustering to identify risk zones
    """
    try:
        if len(coordinates) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 coordinates for clustering analysis",
            )

        # Validate coordinates format
        for coord in coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]",
                )

        # Convert to tuples of (lat, lon)
        coord_tuples = [(coord[0], coord[1]) for coord in coordinates]

        result = geospatial_clustering(
            coord_tuples, values, eps=eps, min_samples=min_samples
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Clustering analysis failed: {str(e)}"
        )


@router.post("/spatial-analysis/combined-risk")
async def combined_spatial_risk_assessment_endpoint(
    coordinates: List[List[float]],  # List of [lat, lon] pairs
    asset_values: List[float],
    risk_scores: List[float],
):
    """
    Perform combined spatial risk assessment using all methods
    """
    try:
        if (
            len(coordinates) < 2
            or len(coordinates) != len(asset_values)
            or len(coordinates) != len(risk_scores)
        ):
            raise HTTPException(
                status_code=400,
                detail="Need same number of coordinates, asset_values, and risk_scores, at least 2 points",
            )

        # Validate coordinates format
        for coord in coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]",
                )

        # Convert to tuples of (lat, lon)
        coord_tuples = [(coord[0], coord[1]) for coord in coordinates]

        result = combined_spatial_risk_assessment(
            coord_tuples, asset_values, risk_scores
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Combined spatial risk assessment failed: {str(e)}"
        )


@router.post("/stochastic-processes/arima-fit")
async def fit_arima_model_endpoint(
    time_series: List[float],
    max_p: int = Query(5, ge=0, le=10),
    max_d: int = Query(2, ge=0, le=3),
    max_q: int = Query(5, ge=0, le=10),
):
    """
    Fit ARIMA model using AIC/BIC criteria for order selection
    """
    try:
        if len(time_series) < 10:
            raise HTTPException(
                status_code=400,
                detail="Need at least 10 observations for ARIMA modeling",
            )

        result = fit_arima_model(time_series, max_p, max_d, max_q)
        return {
            "p": result.p,
            "d": result.d,
            "q": result.q,
            "coefficients": result.coefficients,
            "aic": result.aic,
            "bic": result.bic,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ARIMA fitting failed: {str(e)}")


@router.post("/stochastic-processes/arima-forecast")
async def forecast_arima_endpoint(
    time_series: List[float],
    steps: int = Query(10, ge=1, le=100),
    p: int = Query(1, ge=0, le=10),
    d: int = Query(0, ge=0, le=3),
    q: int = Query(1, ge=0, le=10),
):
    """
    Generate forecasts using fitted ARIMA model
    """
    try:
        if len(time_series) < 10:
            raise HTTPException(
                status_code=400,
                detail="Need at least 10 observations for ARIMA forecasting",
            )

        # Create ARIMA parameters object
        from services.stochastic_process_service import ARIMAModelParams

        arima_params = ARIMAModelParams(
            p=p, d=d, q=q, coefficients=[], aic=0.0, bic=0.0
        )

        result = forecast_arima(time_series, steps, arima_params)
        return {"forecasts": result}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"ARIMA forecasting failed: {str(e)}"
        )


@router.post("/stochastic-processes/copula-fit")
async def fit_copula_model_endpoint(
    data1: List[float],
    data2: List[float],
    copula_type: str = Query("gaussian", regex="^(gaussian|clayton|gumbel|frank)$"),
):
    """
    Fit copula model to capture dependence structure between two variables
    """
    try:
        if len(data1) != len(data2):
            raise HTTPException(
                status_code=400, detail="Both datasets must have same length"
            )

        if len(data1) < 5:
            raise HTTPException(
                status_code=400,
                detail="Need at least 5 observations for copula fitting",
            )

        result = fit_copula_model(data1, data2, copula_type)
        return {
            "type": result.type,
            "parameter": result.parameter,
            "kendall_tau": result.kendall_tau,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copula fitting failed: {str(e)}")


@router.post("/stochastic-processes/regime-switching")
async def regime_switching_model_endpoint(
    time_series: List[float], n_states: int = Query(2, ge=2, le=5)
):
    """
    Fit a regime-switching model to identify climate states
    """
    try:
        if len(time_series) < 20:
            raise HTTPException(
                status_code=400,
                detail="Need at least 20 observations for regime switching model",
            )

        result = regime_switching_model(time_series, n_states)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Regime switching model failed: {str(e)}"
        )


@router.post("/stochastic-processes/multivariate-modeling")
async def multivariate_climate_modeling_endpoint(
    climate_variables: Dict[str, List[float]],
):
    """
    Perform multivariate climate modeling using copulas and ARIMA
    """
    try:
        if len(climate_variables) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 climate variables for multivariate modeling",
            )

        # Check that all series have the same length
        lengths = [len(series) for series in climate_variables.values()]
        if len(set(lengths)) > 1:
            raise HTTPException(
                status_code=400,
                detail="All climate variable series must have the same length",
            )

        result = multivariate_climate_modeling(climate_variables)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Multivariate climate modeling failed: {str(e)}"
        )


@router.post("/advanced-analysis/comprehensive-risk")
async def comprehensive_climate_risk_analysis(
    time_series_data: Dict[str, List[float]],  # Climate variables over time
    spatial_coordinates: List[List[float]],  # Location coordinates
    asset_exposures: List[float],  # Asset values at each location
    risk_exposures: List[float],  # Risk scores at each location
):
    """
    Perform comprehensive climate risk analysis using all four mathematical engines:
    1. Extreme Value Theory (GEV/GPD)
    2. Spatial Statistics (KDE, correlation, clustering)
    3. Stochastic Processes (ARIMA, copulas, regime-switching)
    4. Integrated Risk Modeling
    """
    try:
        # Validate inputs
        if len(time_series_data) < 1:
            raise HTTPException(
                status_code=400, detail="Need at least one time series for analysis"
            )

        if len(spatial_coordinates) < 2:
            raise HTTPException(
                status_code=400, detail="Need at least 2 spatial locations for analysis"
            )

        if len(spatial_coordinates) != len(asset_exposures) or len(
            spatial_coordinates
        ) != len(risk_exposures):
            raise HTTPException(
                status_code=400,
                detail="Spatial coordinates, asset exposures, and risk exposures must have same length",
            )

        # Validate coordinates format
        for coord in spatial_coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]",
                )

        # 1. Perform extreme value analysis on the first climate variable
        first_var_name = list(time_series_data.keys())[0]
        first_var_series = time_series_data[first_var_name]

        if len(first_var_series) >= 20:
            ext_val_result = combined_gev_gpd_analysis(first_var_series)
        else:
            ext_val_result = {"error": "Insufficient data for extreme value analysis"}

        # 2. Perform spatial analysis
        coord_tuples = [(coord[0], coord[1]) for coord in spatial_coordinates]
        spatial_result = combined_spatial_risk_assessment(
            coord_tuples, asset_exposures, risk_exposures
        )

        # 3. Perform stochastic process modeling
        stochastic_result = multivariate_climate_modeling(time_series_data)

        # 4. Combine all results
        comprehensive_result = {
            "analysis_timestamp": datetime.now().isoformat(),
            "extreme_value_analysis": ext_val_result,
            "spatial_analysis": spatial_result,
            "stochastic_process_analysis": stochastic_result,
            "input_summary": {
                "n_time_series": len(time_series_data),
                "n_spatial_locations": len(spatial_coordinates),
                "total_asset_exposure": float(sum(asset_exposures)),
                "average_risk_score": float(np.mean(risk_exposures)),
            },
            "integrated_risk_metrics": {
                "max_return_level": (
                    ext_val_result.get("risk_metrics", {}).get("var_995", 0.0)
                    if isinstance(ext_val_result, dict)
                    and "risk_metrics" in ext_val_result
                    else 0.0
                ),
                "spatial_correlation": spatial_result.get(
                    "spatial_correlation_analysis", {}
                ).get("spatial_correlation", 0.0),
                "volatility_clustering": (
                    stochastic_result.get("univariate_models", {})
                    .get(first_var_name, {})
                    .get("volatility_clustering_parameter", 0.0)
                    if isinstance(stochastic_result, dict)
                    and "univariate_models" in stochastic_result
                    else 0.0
                ),
                "regime_probability": (
                    stochastic_result.get("regime_probabilities", [0.0])[0]
                    if isinstance(stochastic_result, dict)
                    else 0.0
                ),
            },
        }

        return comprehensive_result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Comprehensive risk analysis failed: {str(e)}"
        )

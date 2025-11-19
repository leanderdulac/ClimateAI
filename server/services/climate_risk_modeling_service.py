"""
Advanced Climate Risk Modeling Service with Regularized Loss Functions
Implements the loss function L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f) where Ω(f) = γT + ½λ||w||²
and includes advanced climate features like SPI, RWI, synoptic circulation patterns, and temperature gradients
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Lasso, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class ClimateRiskModelingService:
    """
    Service implementing advanced climate risk modeling with regularized loss functions
    and specialized climate features
    """

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}

    def calculate_standardized_precipitation_index(
        self, precipitation_data: List[float], window_months: int = 3
    ) -> List[float]:
        """
        Calculate Standardized Precipitation Index (SPI) for different time windows

        Args:
            precipitation_data: Historical precipitation data
            window_months: Aggregation window in months (3, 6, 12)

        Returns:
            SPI values for the requested window
        """
        if len(precipitation_data) < window_months * 30:  # Assuming daily data
            raise ValueError(
                f"Need at least {window_months * 30} days of data for {window_months}-month SPI"
            )

        # Aggregate precipitation data to monthly values
        monthly_data = []
        for i in range(0, len(precipitation_data) - (window_months - 1) * 30, 30):
            monthly_sum = sum(precipitation_data[i : i + 30])  # Sum of 30 days
            monthly_data.append(monthly_sum)

        # Calculate SPI using gamma distribution fitting
        spi_values = []
        for i in range(len(monthly_data) - window_months + 1):
            # Sum precipitation over the window
            window_sum = sum(monthly_data[i : i + window_months])

            # Fit gamma distribution to historical data for this window
            # For simplicity, using method of moments to estimate parameters
            historical_window_means = [
                sum(monthly_data[j : j + window_months])
                for j in range(len(monthly_data) - window_months + 1)
            ]

            if len(historical_window_means) > 5:  # Need sufficient data
                mean_val = np.mean(historical_window_means)
                std_val = np.std(historical_window_means)

                if std_val > 0:
                    # Standardize using normal distribution approximation
                    # In reality, SPI uses gamma distribution for fitting
                    z_score = (window_sum - mean_val) / std_val
                    spi_values.append(z_score)
                else:
                    spi_values.append(0.0)
            else:
                spi_values.append(0.0)

        return spi_values

    def calculate_relative_wetness_index(
        self, precipitation: List[float], temperature: List[float]
    ) -> List[float]:
        """
        Calculate Relative Wetness Index (RWI) based on precipitation and temperature

        Args:
            precipitation: Precipitation values
            temperature: Temperature values

        Returns:
            RWI values
        """
        if len(precipitation) != len(temperature):
            raise ValueError("Precipitation and temperature must have same length")

        rwi_values = []
        for i in range(len(precipitation)):
            # RWI = P / (T + 10) where P is precipitation and T is temperature
            # Adding 10 to avoid division by zero and represent base temperature
            rwi = precipitation[i] / (max(0, temperature[i]) + 10)
            rwi_values.append(rwi)

        return rwi_values

    def extract_synoptic_circulation_patterns(
        self,
        pressure_data: List[float],
        wind_data: List[Tuple[float, float]],  # (speed, direction)
        lat_lon_data: List[Tuple[float, float]],
    ) -> List[Dict[str, float]]:
        """
        Extract synoptic circulation patterns based on pressure and wind data

        Args:
            pressure_data: Atmospheric pressure values
            wind_data: Wind (speed, direction) tuples
            lat_lon_data: Latitude/longitude coordinates

        Returns:
            Dictionary of circulation pattern indices
        """
        patterns = []

        for i in range(len(pressure_data)):
            # Calculate basic circulation indices
            pressure = pressure_data[i]
            wind_speed, wind_dir = wind_data[i]
            lat, lon = lat_lon_data[i]

            pattern_features = {
                # Pressure-based indices
                "pressure_anomaly": pressure - 1013.25,  # Standard pressure (hPa)
                "low_pressure_system": (
                    1 if pressure < 1000 else 0
                ),  # Low pressure indicator
                # Wind-based indices
                "meridional_flow": wind_speed
                * np.cos(np.radians(wind_dir)),  # North-south component
                "zonal_flow": wind_speed
                * np.sin(np.radians(wind_dir)),  # East-west component
                "wind_intensity": wind_speed,
                # Latitude-based circulation patterns
                "polar_front_influence": (
                    1 if abs(lat) > 60 else 0
                ),  # Polar front region
                "subtropical_high": (
                    1 if 20 < abs(lat) < 40 else 0
                ),  # Subtropical high region
            }

            patterns.append(pattern_features)

        return patterns

    def calculate_vertical_temperature_gradient(
        self, temperature_data: List[List[float]]
    ) -> List[float]:
        """
        Calculate vertical temperature gradient (instability indicator)
        Each inner list represents temperature at different pressure levels at a time point

        Args:
            temperature_data: List of [temp_surface, temp_850hpa, temp_700hpa, temp_500hpa, ...]

        Returns:
            Temperature gradient (lapse rate) values indicating atmospheric instability
        """
        gradients = []

        for temp_profile in temperature_data:
            if len(temp_profile) >= 2:
                # Calculate lapse rate between surface and upper level
                # Negative values indicate stable atmosphere, positive indicate unstable
                surface_temp = temp_profile[0]  # Surface temperature
                upper_temp = temp_profile[-1]  # Temperature at highest level

                # Height difference approximation (in km)
                height_diff = (
                    5.0  # Approximate height difference (surface to 500 hPa ~ 5.5 km)
                )

                # Lapse rate in °C/km (negative for normal lapse rate)
                lapse_rate = (upper_temp - surface_temp) / height_diff
                gradients.append(lapse_rate)
            else:
                gradients.append(0.0)  # Default for insufficient data

        return gradients

    def create_climate_feature_matrix(
        self,
        precipitation_data: List[float],
        temperature_data: List[float],
        pressure_data: List[float],
        wind_data: List[Tuple[float, float]],
        lat_lon_data: List[Tuple[float, float]],
        temp_profile_data: List[List[float]],
    ) -> np.ndarray:
        """
        Create comprehensive climate feature matrix including SPI, RWI, circulation patterns, etc.

        Args:
            precipitation_data: Precipitation time series
            temperature_data: Temperature time series
            pressure_data: Pressure time series
            wind_data: Wind (speed, direction) time series
            lat_lon_data: Latitude/longitude time series
            temp_profile_data: Temperature profile at different pressure levels

        Returns:
            Feature matrix with all climate features
        """
        n_samples = len(precipitation_data)

        # Calculate SPI for different time windows, handling insufficient data gracefully
        spi_3m = []
        spi_6m = []
        spi_12m = []

        if len(precipitation_data) >= 90:  # At least 3 months
            try:
                spi_3m = self.calculate_standardized_precipitation_index(
                    precipitation_data, window_months=3
                )
            except ValueError:
                spi_3m = []  # Handle case where insufficient data despite check
        if len(precipitation_data) >= 180:  # At least 6 months
            try:
                spi_6m = self.calculate_standardized_precipitation_index(
                    precipitation_data, window_months=6
                )
            except ValueError:
                spi_6m = []  # Handle case where insufficient data despite check
        if len(precipitation_data) >= 360:  # At least 12 months
            try:
                spi_12m = self.calculate_standardized_precipitation_index(
                    precipitation_data, window_months=12
                )
            except ValueError:
                spi_12m = []  # Handle case where insufficient data despite check

        # Calculate RWI
        rwi = self.calculate_relative_wetness_index(
            precipitation_data, temperature_data
        )

        # Extract circulation patterns
        circulation_patterns = self.extract_synoptic_circulation_patterns(
            pressure_data[:n_samples], wind_data[:n_samples], lat_lon_data[:n_samples]
        )

        # Calculate vertical temperature gradients
        temp_gradients = self.calculate_vertical_temperature_gradient(temp_profile_data)

        # Align all features to the same length (minimum of all feature series)
        # Only include non-empty series in the min calculation
        lengths_to_consider = [len(rwi), len(circulation_patterns), len(temp_gradients)]
        if spi_3m:
            lengths_to_consider.append(len(spi_3m))
        if spi_6m:
            lengths_to_consider.append(len(spi_6m))
        if spi_12m:
            lengths_to_consider.append(len(spi_12m))

        min_length = min(lengths_to_consider) if lengths_to_consider else 0

        # Create feature matrix
        features = []
        for i in range(min_length):
            # Basic climate features
            feature_row = [
                precipitation_data[i],
                temperature_data[i],
                pressure_data[i],
                wind_data[i][0],  # Wind speed
                wind_data[i][1],  # Wind direction
                rwi[i],
                temp_gradients[i] if i < len(temp_gradients) else 0,
                # SPI values (use the latest available)
                spi_3m[i] if i < len(spi_3m) else 0,
                spi_6m[i] if i < len(spi_6m) else 0,
                spi_12m[i] if i < len(spi_12m) else 0,
            ]

            # Add circulation pattern features
            if i < len(circulation_patterns):
                cp = circulation_patterns[i]
                feature_row.extend(
                    [
                        cp["pressure_anomaly"],
                        cp["low_pressure_system"],
                        cp["meridional_flow"],
                        cp["zonal_flow"],
                        cp["wind_intensity"],
                        cp["polar_front_influence"],
                        cp["subtropical_high"],
                    ]
                )

            features.append(feature_row)

        return np.array(features)

    def regularized_loss_function(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_weights: np.ndarray,
        gamma: float = 1.0,
        lambda_reg: float = 0.01,
        loss_type: str = "mse",
    ) -> float:
        """
        Calculate regularized loss function: L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f)
        where Ω(f) = γT + ½λ||w||²

        Args:
            y_true: True target values
            y_pred: Predicted values
            model_weights: Model weights for regularization term
            gamma: Time penalty coefficient (γT)
            lambda_reg: Regularization coefficient (λ)
            loss_type: Type of primary loss function ('mse', 'mae', 'huber')

        Returns:
            Total regularized loss
        """
        # Calculate primary loss l(y_i, ŷ_i)
        if loss_type == "mse":
            primary_loss = np.mean((y_true - y_pred) ** 2)
        elif loss_type == "mae":
            primary_loss = np.mean(np.abs(y_true - y_pred))
        elif loss_type == "huber":
            # Simplified Huber loss
            delta = 1.0
            errors = np.abs(y_true - y_pred)
            quadratic = np.minimum(errors, delta)
            linear = errors - quadratic
            primary_loss = np.mean(0.5 * quadratic**2 + delta * linear)
        else:
            raise ValueError(f"Unsupported loss type: {loss_type}")

        # Calculate regularization term Ω(f) = γT + ½λ||w||²
        # For now, T (time) factor is set to 1, could be made dynamic
        time_penalty = gamma * 1.0  # Simple time penalty, can be made more complex
        weight_penalty = 0.5 * lambda_reg * np.sum(model_weights**2)
        regularization_term = time_penalty + weight_penalty

        # Total loss
        total_loss = primary_loss + regularization_term

        return total_loss

    def fit_regularized_climate_model(
        self,
        feature_matrix: np.ndarray,
        target_values: np.ndarray,
        model_type: str = "ridge",
        gamma: float = 0.1,
        lambda_reg: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Fit a climate model using regularized loss function

        Args:
            feature_matrix: Climate feature matrix
            target_values: Target climate risk values
            model_type: Type of model ('ridge', 'lasso', 'elastic_net', 'rf', 'gbm')
            gamma: Time penalty coefficient
            lambda_reg: Regularization coefficient

        Returns:
            Dictionary with model results and metrics
        """
        if len(feature_matrix) != len(target_values):
            raise ValueError("Feature matrix and target values must have same length")

        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(feature_matrix)

        # Initialize model based on type
        if model_type == "ridge":
            model = Ridge(alpha=lambda_reg)
        elif model_type == "lasso":
            model = Lasso(alpha=lambda_reg)
        elif model_type == "elastic_net":
            model = ElasticNet(alpha=lambda_reg, l1_ratio=0.5)
        elif model_type == "rf":
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == "gbm":
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        # Fit the model
        model.fit(X_scaled, target_values)

        # Make predictions
        y_pred = model.predict(X_scaled)

        # Calculate weights for regularization (for linear models)
        if hasattr(model, "coef_"):
            model_weights = model.coef_
        else:
            # For tree-based models, use feature importances as proxy for weights
            model_weights = (
                model.feature_importances_
                if hasattr(model, "feature_importances_")
                else np.ones(X_scaled.shape[1])
            )

        # Calculate regularized loss
        reg_loss = self.regularized_loss_function(
            target_values, y_pred, model_weights, gamma, lambda_reg
        )

        # Calculate traditional metrics
        mse = mean_squared_error(target_values, y_pred)
        mae = mean_absolute_error(target_values, y_pred)

        # Store model and scaler
        model_id = f"climate_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.models[model_id] = {
            "model": model,
            "scaler": scaler,
            "model_type": model_type,
            "features_used": X_scaled.shape[1],
            "n_samples": len(target_values),
        }

        return {
            "model_id": model_id,
            "model_type": model_type,
            "regularized_loss": reg_loss,
            "mse": mse,
            "mae": mae,
            "predictions": y_pred.tolist(),
            "residuals": (target_values - y_pred).tolist(),
            "feature_importance": getattr(
                model,
                "feature_importances_",
                getattr(model, "coef_", np.ones(len(model_weights))),
            ).tolist(),
            "n_features": X_scaled.shape[1],
            "n_samples": len(target_values),
        }

    def predict_with_climate_model(
        self, model_id: str, feature_matrix: np.ndarray
    ) -> Dict[str, Any]:
        """
        Make predictions using a fitted climate model

        Args:
            model_id: ID of the fitted model
            feature_matrix: Climate feature matrix for prediction

        Returns:
            Dictionary with predictions and uncertainty estimates
        """
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        model_info = self.models[model_id]
        model = model_info["model"]
        scaler = model_info["scaler"]

        # Standardize features
        X_scaled = scaler.transform(feature_matrix)

        # Make predictions
        predictions = model.predict(X_scaled)

        # For ensemble models, estimate uncertainty
        uncertainty = [0.0] * len(
            predictions
        )  # Placeholder, could be more sophisticated

        if model_info["model_type"] in ["rf", "gbm"]:
            # Calculate uncertainty using ensemble methods
            if model_info["model_type"] == "rf":
                # Use out-of-bag error as uncertainty proxy
                # This is a simplification - in practice would use cross-validation
                n_estimators = len(model.estimators_)
                pred_matrix = np.array(
                    [est.predict(X_scaled) for est in model.estimators_]
                )
                uncertainty = np.std(pred_matrix, axis=0).tolist()

        return {
            "model_id": model_id,
            "predictions": predictions.tolist(),
            "uncertainty": uncertainty,
            "n_predictions": len(predictions),
        }

    def comprehensive_climate_risk_assessment(
        self,
        precipitation_data: List[float],
        temperature_data: List[float],
        pressure_data: List[float],
        wind_data: List[Tuple[float, float]],
        lat_lon_data: List[Tuple[float, float]],
        temp_profile_data: List[List[float]],
        target_values: List[float],
        gamma: float = 0.1,
        lambda_reg: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive climate risk assessment using all the advanced features

        Args:
            precipitation_data: Precipitation time series
            temperature_data: Temperature time series
            pressure_data: Pressure time series
            wind_data: Wind (speed, direction) time series
            lat_lon_data: Latitude/longitude time series
            temp_profile_data: Temperature profile at different pressure levels
            target_values: Target climate risk values
            gamma: Time penalty coefficient
            lambda_reg: Regularization coefficient

        Returns:
            Comprehensive risk assessment results
        """
        # Create comprehensive feature matrix
        feature_matrix = self.create_climate_feature_matrix(
            precipitation_data,
            temperature_data,
            pressure_data,
            wind_data,
            lat_lon_data,
            temp_profile_data,
        )

        # Fit regularized climate model
        model_results = self.fit_regularized_climate_model(
            feature_matrix,
            np.array(target_values),
            model_type="rf",  # Using Random Forest by default
            gamma=gamma,
            lambda_reg=lambda_reg,
        )

        # Calculate SPI values for different time windows, handling insufficient data gracefully
        spi_3m = []
        spi_6m = []

        if len(precipitation_data) >= 90:  # At least 3 months
            try:
                spi_3m = self.calculate_standardized_precipitation_index(
                    precipitation_data, 3
                )
            except ValueError:
                spi_3m = []
        if len(precipitation_data) >= 180:  # At least 6 months
            try:
                spi_6m = self.calculate_standardized_precipitation_index(
                    precipitation_data, 6
                )
            except ValueError:
                spi_6m = []

        # Calculate RWI
        rwi = self.calculate_relative_wetness_index(
            precipitation_data, temperature_data
        )

        # Extract circulation patterns
        circulation_patterns = self.extract_synoptic_circulation_patterns(
            pressure_data[: len(precipitation_data)],
            wind_data[: len(precipitation_data)],
            lat_lon_data[: len(precipitation_data)],
        )

        return {
            "model_results": model_results,
            "climate_features": {
                "spi_3m": spi_3m[-10:],  # Last 10 values
                "spi_6m": spi_6m[-10:],  # Last 10 values
                "rwi": rwi[-10:],  # Last 10 values
                "n_features_total": feature_matrix.shape[1],
                "n_samples": feature_matrix.shape[0],
            },
            "synoptic_patterns": {
                "low_pressure_systems": sum(
                    1 for cp in circulation_patterns if cp["low_pressure_system"] > 0
                ),
                "polar_front_influence": sum(
                    1 for cp in circulation_patterns if cp["polar_front_influence"] > 0
                ),
                "subtropical_high_influence": sum(
                    1 for cp in circulation_patterns if cp["subtropical_high"] > 0
                ),
            },
            "risk_assessment": {
                "predicted_risk_level": float(np.mean(model_results["predictions"])),
                "risk_uncertainty": float(np.std(model_results["predictions"])),
                "model_confidence": 1.0
                - (model_results["mae"] / (1.0 + np.mean(np.abs(target_values)))),
            },
            "loss_function_params": {
                "gamma": gamma,
                "lambda": lambda_reg,
                "regularized_loss": model_results["regularized_loss"],
            },
        }


# Global instance
climate_risk_modeling_service = ClimateRiskModelingService()


# Convenience functions for API integration
def calculate_standardized_precipitation_index(
    precipitation_data: List[float], window_months: int = 3
) -> List[float]:
    """Calculate Standardized Precipitation Index (SPI) for different time windows"""
    return climate_risk_modeling_service.calculate_standardized_precipitation_index(
        precipitation_data, window_months
    )


def calculate_relative_wetness_index(
    precipitation: List[float], temperature: List[float]
) -> List[float]:
    """Calculate Relative Wetness Index (RWI) based on precipitation and temperature"""
    return climate_risk_modeling_service.calculate_relative_wetness_index(
        precipitation, temperature
    )


def extract_synoptic_circulation_patterns(
    pressure_data: List[float],
    wind_data: List[Tuple[float, float]],
    lat_lon_data: List[Tuple[float, float]],
) -> List[Dict[str, float]]:
    """Extract synoptic circulation patterns based on pressure and wind data"""
    return climate_risk_modeling_service.extract_synoptic_circulation_patterns(
        pressure_data, wind_data, lat_lon_data
    )


def calculate_vertical_temperature_gradient(
    temperature_data: List[List[float]],
) -> List[float]:
    """Calculate vertical temperature gradient (instability indicator)"""
    return climate_risk_modeling_service.calculate_vertical_temperature_gradient(
        temperature_data
    )


def regularized_loss_function(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_weights: np.ndarray,
    gamma: float = 1.0,
    lambda_reg: float = 0.01,
    loss_type: str = "mse",
) -> float:
    """Calculate regularized loss function: L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f)"""
    return climate_risk_modeling_service.regularized_loss_function(
        y_true, y_pred, model_weights, gamma, lambda_reg, loss_type
    )


def comprehensive_climate_risk_assessment(
    precipitation_data: List[float],
    temperature_data: List[float],
    pressure_data: List[float],
    wind_data: List[Tuple[float, float]],
    lat_lon_data: List[Tuple[float, float]],
    temp_profile_data: List[List[float]],
    target_values: List[float],
    gamma: float = 0.1,
    lambda_reg: float = 0.01,
) -> Dict[str, Any]:
    """Perform comprehensive climate risk assessment using advanced features"""
    return climate_risk_modeling_service.comprehensive_climate_risk_assessment(
        precipitation_data,
        temperature_data,
        pressure_data,
        wind_data,
        lat_lon_data,
        temp_profile_data,
        target_values,
        gamma,
        lambda_reg,
    )

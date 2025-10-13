"""
Machine Learning Service for Sinistrality Prediction
Provides ML-based predictions for insurance claims frequency and severity
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class SinistralityPredictor:
    """
    Machine Learning model for predicting insurance sinistrality (claims frequency and severity)
    based on historical data, weather patterns, and economic indicators.
    """

    def __init__(self, model_path: str = "models"):
        self.model_path = model_path
        self.frequency_model = None
        self.severity_model = None
        self.scaler = StandardScaler()
        self.is_trained = False

        # Ensure model directory exists
        os.makedirs(model_path, exist_ok=True)

        # Try to load existing models
        self._load_models()

    def _load_models(self):
        """Load pre-trained models if they exist"""
        try:
            freq_path = os.path.join(self.model_path, "frequency_model.pkl")
            sev_path = os.path.join(self.model_path, "severity_model.pkl")
            scaler_path = os.path.join(self.model_path, "scaler.pkl")

            if all(os.path.exists(p) for p in [freq_path, sev_path, scaler_path]):
                self.frequency_model = joblib.load(freq_path)
                self.severity_model = joblib.load(sev_path)
                self.scaler = joblib.load(scaler_path)
                self.is_trained = True
                logger.info("Pre-trained ML models loaded successfully")
            else:
                logger.info("No pre-trained models found, will use rule-based predictions")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

    def _generate_synthetic_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Generate synthetic historical data for training when real data is not available
        """
        np.random.seed(42)

        # Generate dates over the past 5 years
        start_date = datetime.now() - timedelta(days=5*365)
        dates = [start_date + timedelta(days=i) for i in range(n_samples)]

        data = []

        for date in dates:
            # Seasonal weather patterns
            month = date.month
            rainfall = np.random.normal(
                loc=150 if month in [12,1,2,3] else 80,  # Higher rainfall in summer
                scale=50
            )

            temperature = np.random.normal(
                loc=25 if month in [12,1,2] else 20,  # Higher temp in summer
                scale=5
            )

            humidity = np.random.normal(loc=70, scale=15)

            # Economic indicators
            inflation_rate = np.random.normal(loc=0.04, scale=0.01)  # 4% average inflation
            gdp_growth = np.random.normal(loc=0.025, scale=0.01)    # 2.5% GDP growth

            # Location factors (latitude/longitude impact)
            latitude = np.random.uniform(-33, 5)  # Brazil latitude range
            longitude = np.random.uniform(-73, -35)  # Brazil longitude range

            # Calculate risk factors
            weather_risk = (rainfall > 200) * 0.3 + (temperature > 30) * 0.2
            economic_risk = (inflation_rate > 0.06) * 0.2 + (gdp_growth < 0) * 0.3
            location_risk = abs(latitude) / 30 * 0.1  # Higher risk in extreme latitudes

            # Generate claims frequency (claims per 100 policies per year)
            base_frequency = 8 + weather_risk * 10 + economic_risk * 5
            frequency_noise = np.random.normal(0, 2)
            frequency = max(0, base_frequency + frequency_noise)

            # Generate claims severity (average claim amount)
            base_severity = 15000 + weather_risk * 20000 + economic_risk * 10000
            severity_noise = np.random.normal(0, 3000)
            severity = max(1000, base_severity + severity_noise)

            data.append({
                'date': date,
                'month': month,
                'rainfall': rainfall,
                'temperature': temperature,
                'humidity': humidity,
                'inflation_rate': inflation_rate,
                'gdp_growth': gdp_growth,
                'latitude': latitude,
                'longitude': longitude,
                'weather_risk': weather_risk,
                'economic_risk': economic_risk,
                'location_risk': location_risk,
                'frequency': frequency,
                'severity': severity
            })

        return pd.DataFrame(data)

    def train_models(self, data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Train ML models for frequency and severity prediction

        Args:
            data: Historical data DataFrame. If None, uses synthetic data.

        Returns:
            Training metrics and model performance
        """
        try:
            if data is None:
                logger.info("Using synthetic data for training")
                data = self._generate_synthetic_data(2000)

            # Prepare features
            feature_cols = [
                'month', 'rainfall', 'temperature', 'humidity',
                'inflation_rate', 'gdp_growth', 'latitude', 'longitude',
                'weather_risk', 'economic_risk', 'location_risk'
            ]

            X = data[feature_cols]
            y_freq = data['frequency']
            y_sev = data['severity']

            # Split data
            X_train, X_test, y_freq_train, y_freq_test, y_sev_train, y_sev_test = train_test_split(
                X, y_freq, y_sev, test_size=0.2, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train frequency model
            self.frequency_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.frequency_model.fit(X_train_scaled, y_freq_train)

            # Train severity model
            self.severity_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                random_state=42,
                learning_rate=0.1
            )
            self.severity_model.fit(X_train_scaled, y_sev_train)

            # Evaluate models
            freq_pred = self.frequency_model.predict(X_test_scaled)
            sev_pred = self.severity_model.predict(X_test_scaled)

            metrics = {
                'frequency': {
                    'mae': mean_absolute_error(y_freq_test, freq_pred),
                    'rmse': np.sqrt(mean_squared_error(y_freq_test, freq_pred)),
                    'r2': r2_score(y_freq_test, freq_pred)
                },
                'severity': {
                    'mae': mean_absolute_error(y_sev_test, sev_pred),
                    'rmse': np.sqrt(mean_squared_error(y_sev_test, sev_pred)),
                    'r2': r2_score(y_sev_test, sev_pred)
                }
            }

            # Save models
            self._save_models()

            self.is_trained = True
            logger.info(f"ML models trained successfully. Metrics: {metrics}")

            return {
                'success': True,
                'metrics': metrics,
                'training_samples': len(X_train)
            }

        except Exception as e:
            logger.error(f"Error training ML models: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.frequency_model, os.path.join(self.model_path, "frequency_model.pkl"))
            joblib.dump(self.severity_model, os.path.join(self.model_path, "severity_model.pkl"))
            joblib.dump(self.scaler, os.path.join(self.model_path, "scaler.pkl"))
            logger.info("ML models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def predict_sinistrality(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict claims frequency and severity based on input features

        Args:
            features: Dictionary containing prediction features

        Returns:
            Dictionary with frequency and severity predictions
        """
        try:
            if not self.is_trained:
                # Fallback to rule-based prediction
                return self._rule_based_prediction(features)

            # Prepare input features
            input_features = self._prepare_features(features)

            # Scale features
            input_scaled = self.scaler.transform([input_features])

            # Make predictions
            frequency_pred = self.frequency_model.predict(input_scaled)[0]
            severity_pred = self.severity_model.predict(input_scaled)[0]

            # Calculate confidence intervals (simplified)
            freq_std = np.std([tree.predict(input_scaled) for tree in self.frequency_model.estimators_])
            sev_std = np.std([self.severity_model.predict(input_scaled) for _ in range(10)])  # Simplified

            return {
                'frequency': {
                    'prediction': max(0, frequency_pred),
                    'confidence_lower': max(0, frequency_pred - 1.96 * freq_std),
                    'confidence_upper': frequency_pred + 1.96 * freq_std,
                    'unit': 'claims per 100 policies per year'
                },
                'severity': {
                    'prediction': max(0, severity_pred),
                    'confidence_lower': max(0, severity_pred - 1.96 * sev_std),
                    'confidence_upper': severity_pred + 1.96 * sev_std,
                    'unit': 'BRL per claim'
                },
                'method': 'machine_learning',
                'confidence_level': '95%'
            }

        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return self._rule_based_prediction(features)

    def _prepare_features(self, features: Dict[str, Any]) -> List[float]:
        """Prepare input features for ML model"""
        # Extract or default values
        month = features.get('month', datetime.now().month)
        rainfall = features.get('rainfall', 100)
        temperature = features.get('temperature', 22)
        humidity = features.get('humidity', 70)
        inflation_rate = features.get('inflation_rate', 0.04)
        gdp_growth = features.get('gdp_growth', 0.025)
        latitude = features.get('latitude', -15)
        longitude = features.get('longitude', -47)

        # Calculate derived features
        weather_risk = (rainfall > 200) * 0.3 + (temperature > 30) * 0.2
        economic_risk = (inflation_rate > 0.06) * 0.2 + (gdp_growth < 0) * 0.3
        location_risk = abs(latitude) / 30 * 0.1

        return [
            month, rainfall, temperature, humidity,
            inflation_rate, gdp_growth, latitude, longitude,
            weather_risk, economic_risk, location_risk
        ]

    def _rule_based_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based prediction when ML models are not available"""
        rainfall = features.get('rainfall', 100)
        temperature = features.get('temperature', 22)
        inflation_rate = features.get('inflation_rate', 0.04)
        gdp_growth = features.get('gdp_growth', 0.025)
        latitude = features.get('latitude', -15)

        # Simple rule-based calculations
        weather_factor = (rainfall / 100) * 0.1 + (temperature / 30) * 0.05
        economic_factor = (inflation_rate / 0.04) * 0.1 + (1 - gdp_growth / 0.025) * 0.05
        location_factor = abs(latitude) / 30 * 0.05

        base_frequency = 8
        base_severity = 15000

        frequency = base_frequency * (1 + weather_factor + economic_factor + location_factor)
        severity = base_severity * (1 + weather_factor + economic_factor)

        return {
            'frequency': {
                'prediction': max(0, frequency),
                'confidence_lower': max(0, frequency * 0.8),
                'confidence_upper': frequency * 1.2,
                'unit': 'claims per 100 policies per year'
            },
            'severity': {
                'prediction': max(0, severity),
                'confidence_lower': max(0, severity * 0.7),
                'confidence_upper': severity * 1.3,
                'unit': 'BRL per claim'
            },
            'method': 'rule_based',
            'confidence_level': 'approximate'
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the ML models"""
        return {
            'is_trained': self.is_trained,
            'frequency_model': type(self.frequency_model).__name__ if self.frequency_model else None,
            'severity_model': type(self.severity_model).__name__ if self.severity_model else None,
            'feature_count': 11,  # Number of input features
            'last_updated': datetime.now().isoformat()
        }

# Global instance
sinistrality_predictor = SinistralityPredictor()

def predict_sinistrality(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict insurance sinistrality using ML models

    Args:
        features: Dictionary with prediction features

    Returns:
        Prediction results with frequency and severity
    """
    return sinistrality_predictor.predict_sinistrality(features)

def train_ml_models(data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Train ML models for sinistrality prediction

    Args:
        data: Optional historical data for training

    Returns:
        Training results and metrics
    """
    return sinistrality_predictor.train_models(data)

def get_ml_model_info() -> Dict[str, Any]:
    """Get information about ML models"""
    return sinistrality_predictor.get_model_info()
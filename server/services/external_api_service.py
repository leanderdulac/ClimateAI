"""
External API Service for Real-time Data Integration
Integrates with weather APIs, economic indicators, and other external data sources
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class ExternalAPIService:
    """
    Service for integrating with external APIs to get real-time data
    including weather, economic indicators, and market data.
    """

    def __init__(self):
        # API Keys from environment variables
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.fred_api_key = os.getenv(
            "FRED_API_KEY", ""
        )  # Federal Reserve Economic Data

        # Cache for API responses
        self.cache = {}
        self.cache_timeout = 1800  # 30 minutes

        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # Minimum 1 second between requests

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key in self.cache:
            timestamp, _ = self.cache[key]
            return time.time() - timestamp < self.cache_timeout
        return False

    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if self._is_cache_valid(key):
            _, data = self.cache[key]
            return data
        return None

    def _set_cached_data(self, key: str, data: Any) -> None:
        """Store data in cache"""
        self.cache[key] = (time.time(), data)

    def _rate_limit_check(self, api_name: str) -> bool:
        """Check if we can make a request to this API"""
        current_time = time.time()
        if api_name in self.last_request_time:
            time_diff = current_time - self.last_request_time[api_name]
            if time_diff < self.min_request_interval:
                return False
        self.last_request_time[api_name] = current_time
        return True

    async def get_weather_data(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """
        Get real-time weather data from OpenWeatherMap API

        Args:
            latitude: Location latitude
            longitude: Location longitude

        Returns:
            Weather data including temperature, precipitation, humidity, etc.
        """
        if not self.openweather_api_key:
            logger.warning("OpenWeather API key not configured, using mock data")
            return self._get_mock_weather_data(latitude, longitude)

        cache_key = f"weather_{latitude}_{longitude}"

        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        if not self._rate_limit_check("openweather"):
            logger.warning("Rate limit exceeded for OpenWeather API")
            return self._get_mock_weather_data(latitude, longitude)

        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.openweather_api_key,
                "units": "metric",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Transform to our format
            weather_data = {
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "precipitation": data.get("rain", {}).get(
                    "1h", 0
                ),  # Last hour precipitation
                "wind_speed": data["wind"]["speed"],
                "wind_direction": data["wind"].get("deg", 0),
                "description": (
                    data["weather"][0]["description"] if data["weather"] else ""
                ),
                "timestamp": datetime.now().isoformat(),
                "source": "openweather",
            }

            self._set_cached_data(cache_key, weather_data)
            return weather_data

        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return self._get_mock_weather_data(latitude, longitude)

    def _get_mock_weather_data(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """Generate mock weather data for testing"""
        import random

        # Simple mock based on latitude (Brazil climate patterns)
        base_temp = 25 - abs(latitude) * 0.1  # Cooler in south
        seasonal_adjustment = 5 * (datetime.now().month - 6) / 12  # Seasonal variation

        return {
            "temperature": base_temp + seasonal_adjustment + random.uniform(-3, 3),
            "humidity": random.uniform(60, 90),
            "pressure": random.uniform(1000, 1020),
            "precipitation": random.uniform(0, 10),
            "wind_speed": random.uniform(0, 15),
            "wind_direction": random.uniform(0, 360),
            "description": "Mock weather data",
            "timestamp": datetime.now().isoformat(),
            "source": "mock",
        }

    async def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Get economic indicators from FRED API

        Returns:
            Economic data including inflation, GDP growth, etc.
        """
        if not self.fred_api_key:
            logger.warning("FRED API key not configured, using mock data")
            return self._get_mock_economic_data()

        cache_key = "economic_indicators"

        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        if not self._rate_limit_check("fred"):
            logger.warning("Rate limit exceeded for FRED API")
            return self._get_mock_economic_data()

        try:
            # Get CPI (inflation) and GDP data
            indicators = {}

            # CPI data (Brazil)
            cpi_url = "https://api.stlouisfed.org/fred/series/observations"
            cpi_params = {
                "series_id": "BRACPIALLMINMEI",  # Brazil CPI
                "api_key": self.fred_api_key,
                "file_type": "json",
                "limit": 1,
                "sort_order": "desc",
            }

            cpi_response = requests.get(cpi_url, params=cpi_params, timeout=10)
            if cpi_response.status_code == 200:
                cpi_data = cpi_response.json()
                if cpi_data.get("observations"):
                    latest_cpi = cpi_data["observations"][0]
                    indicators["inflation_rate"] = (
                        float(latest_cpi.get("value", 0)) / 100
                    )

            # GDP growth (Brazil)
            gdp_url = "https://api.stlouisfed.org/fred/series/observations"
            gdp_params = {
                "series_id": "MKTGDPBRA646NWDB",  # Brazil GDP
                "api_key": self.fred_api_key,
                "file_type": "json",
                "limit": 12,  # Last 12 months for YoY calculation
                "sort_order": "desc",
            }

            gdp_response = requests.get(gdp_url, params=gdp_params, timeout=10)
            if gdp_response.status_code == 200:
                gdp_data = gdp_response.json()
                if gdp_data.get("observations") and len(gdp_data["observations"]) >= 12:
                    current_gdp = float(gdp_data["observations"][0].get("value", 0))
                    previous_gdp = float(gdp_data["observations"][11].get("value", 0))
                    if previous_gdp > 0:
                        indicators["gdp_growth"] = (
                            current_gdp - previous_gdp
                        ) / previous_gdp

            economic_data = {
                "inflation_rate": indicators.get("inflation_rate", 0.04),  # Default 4%
                "gdp_growth": indicators.get("gdp_growth", 0.025),  # Default 2.5%
                "timestamp": datetime.now().isoformat(),
                "source": "fred",
            }

            self._set_cached_data(cache_key, economic_data)
            return economic_data

        except Exception as e:
            logger.error(f"Error fetching economic data: {e}")
            return self._get_mock_economic_data()

    def _get_mock_economic_data(self) -> Dict[str, Any]:
        """Generate mock economic data"""
        import random

        return {
            "inflation_rate": 0.04 + random.uniform(-0.01, 0.01),  # Around 4%
            "gdp_growth": 0.025 + random.uniform(-0.005, 0.005),  # Around 2.5%
            "timestamp": datetime.now().isoformat(),
            "source": "mock",
        }

    async def get_commodity_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get commodity prices from Alpha Vantage API

        Args:
            symbols: List of commodity symbols

        Returns:
            Current prices for requested commodities
        """
        if not self.alpha_vantage_api_key:
            logger.warning("Alpha Vantage API key not configured, using mock data")
            return self._get_mock_commodity_data(symbols)

        results = {}

        for symbol in symbols:
            cache_key = f"commodity_{symbol}"

            # Check cache first
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                results[symbol] = cached_data
                continue

            if not self._rate_limit_check("alphavantage"):
                logger.warning("Rate limit exceeded for Alpha Vantage API")
                results[symbol] = self._get_mock_commodity_data([symbol])[symbol]
                continue

            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": self.alpha_vantage_api_key,
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                if "Global Quote" in data:
                    quote = data["Global Quote"]
                    commodity_data = {
                        "price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": float(
                            quote.get("10. change percent", "0%").strip("%")
                        ),
                        "volume": int(quote.get("06. volume", 0)),
                        "timestamp": datetime.now().isoformat(),
                        "source": "alphavantage",
                    }
                    results[symbol] = commodity_data
                    self._set_cached_data(cache_key, commodity_data)
                else:
                    results[symbol] = self._get_mock_commodity_data([symbol])[symbol]

            except Exception as e:
                logger.error(f"Error fetching commodity data for {symbol}: {e}")
                results[symbol] = self._get_mock_commodity_data([symbol])[symbol]

        return results

    def _get_mock_commodity_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Generate mock commodity data"""
        import random

        mock_prices = {
            "CORN": 180 + random.uniform(-10, 10),  # Corn
            "SOYBEAN": 450 + random.uniform(-20, 20),  # Soybean
            "WHEAT": 220 + random.uniform(-15, 15),  # Wheat
            "COFFEE": 120 + random.uniform(-8, 8),  # Coffee
            "SUGAR": 85 + random.uniform(-5, 5),  # Sugar
        }

        results = {}
        for symbol in symbols:
            base_price = mock_prices.get(symbol, 100)
            results[symbol] = {
                "price": base_price,
                "change": random.uniform(-5, 5),
                "change_percent": random.uniform(-3, 3),
                "volume": random.randint(1000, 10000),
                "timestamp": datetime.now().isoformat(),
                "source": "mock",
            }

        return results

    async def get_real_time_data(
        self, latitude: float, longitude: float, commodities: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive real-time data from all external APIs

        Args:
            latitude: Location latitude
            longitude: Location longitude
            commodities: List of commodity symbols to fetch

        Returns:
            Combined real-time data from all sources
        """
        try:
            # Run API calls concurrently
            weather_task = self.get_weather_data(latitude, longitude)
            economic_task = self.get_economic_indicators()
            commodity_task = self.get_commodity_prices(
                commodities or ["CORN", "SOYBEAN"]
            )

            weather_data, economic_data, commodity_data = await asyncio.gather(
                weather_task, economic_task, commodity_task
            )

            return {
                "weather": weather_data,
                "economic": economic_data,
                "commodities": commodity_data,
                "timestamp": datetime.now().isoformat(),
                "location": {"latitude": latitude, "longitude": longitude},
            }

        except Exception as e:
            logger.error(f"Error fetching real-time data: {e}")
            return {
                "weather": self._get_mock_weather_data(latitude, longitude),
                "economic": self._get_mock_economic_data(),
                "commodities": self._get_mock_commodity_data(
                    commodities or ["CORN", "SOYBEAN"]
                ),
                "timestamp": datetime.now().isoformat(),
                "location": {"latitude": latitude, "longitude": longitude},
                "error": str(e),
            }


# Global instance
external_api_service = ExternalAPIService()


# Convenience functions
async def get_weather_data(latitude: float, longitude: float) -> Dict[str, Any]:
    """Get weather data for a location"""
    return await external_api_service.get_weather_data(latitude, longitude)


async def get_economic_indicators() -> Dict[str, Any]:
    """Get current economic indicators"""
    return await external_api_service.get_economic_indicators()


async def get_commodity_prices(symbols: List[str]) -> Dict[str, Any]:
    """Get commodity prices"""
    return await external_api_service.get_commodity_prices(symbols)


async def get_real_time_data(
    latitude: float, longitude: float, commodities: List[str] = None
) -> Dict[str, Any]:
    """Get comprehensive real-time data"""
    return await external_api_service.get_real_time_data(
        latitude, longitude, commodities
    )

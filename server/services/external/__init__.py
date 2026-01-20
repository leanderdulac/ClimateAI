"""
External Services Subpackage
Contains services for external API integrations.
"""

from services.embrapa_service import EmbrapaService
from services.external_api_service import (
    get_commodity_prices,
    get_economic_indicators,
    get_real_time_data,
    get_weather_data,
)
from services.geocoding_service import GeocodingService
from services.openmeteo_service import OpenMeteoService
from services.xweather_service import XWeatherService

__all__ = [
    "get_weather_data",
    "get_economic_indicators",
    "get_commodity_prices",
    "get_real_time_data",
    "EmbrapaService",
    "OpenMeteoService",
    "XWeatherService",
    "GeocodingService",
]

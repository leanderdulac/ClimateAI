"""
Serviço de integração com NOAA (National Oceanic and Atmospheric Administration)
Fornece acesso a dados climáticos históricos e meteorológicos
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from fastapi import HTTPException

from config.config import settings
from services.embrapa_service import EmbrapaService
from services.geocoding_service import GeocodingService
from lib.resilient_http_client import create_resilient_client
from lib.redis_cache import external_api_cache

logger = logging.getLogger(__name__)


class NOAAService:
    """
    Serviço para integração com APIs do NOAA
    """

    def __init__(self):
        self.api_key = settings.NOAA_API_KEY
        self.use_mock = not self.api_key

        # URLs das APIs do NOAA
        self.base_urls = {
            "climate_data": "https://www.ncdc.noaa.gov/cdo-web/api/v2",
            "weather_forecast": "https://api.weather.gov",
            "satellite_data": "https://www.nesdis.noaa.gov"
        }

        # Clientes resilientes (Tier 1)
        self.climate_client = create_resilient_client(
            "noaa_climate", 
            self.base_urls["climate_data"],
            api_key=self.api_key,
            api_key_header="token"
        )
        self.forecast_client = create_resilient_client(
            "noaa_forecast",
            self.base_urls["weather_forecast"]
        )

        # Serviço de fallback Embrapa
        self.embrapa_service = EmbrapaService()

        # Serviço de geocodificação
        self.geocoding_service = GeocodingService()

    @external_api_cache("noaa_climate", ttl=86400) # Cache de 24h para dados históricos
    async def get_climate_data(self, location: str, start_date: str, end_date: str,
                        data_type: str = "TMAX") -> Dict[str, Any]:
        """
        Busca dados climáticos históricos do NOAA com fallback para Embrapa

        Args:
            location: Localização (cidade, estado)
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            data_type: Tipo de dado (TMAX, TMIN, PRCP, etc.)
        """
        if self.use_mock:
            return self._mock_climate_data(location, start_date, end_date, data_type)

        try:
            # Primeiro, geocodificar a localização para obter coordenadas
            geo_data = await self.geocoding_service.geocode_address(location)
            latitude = geo_data["latitude"]
            longitude = geo_data["longitude"]

            # Tentar NOAA primeiro
            # Buscar o station ID para a localização usando as coordenadas
            station_id = await self._get_station_id(latitude, longitude)

            if not station_id:
                logger.warning(f"Estação meteorológica não encontrada para {location} ({latitude}, {longitude}). Tentando busca genérica.")
                station_id = await self._get_station_id(latitude, longitude, radius=100) # Expande o raio

            if not station_id:
                raise HTTPException(
                    status_code=404,
                    detail=f"Estação meteorológica não encontrada para {location}"
                )

            # Buscar dados climáticos
            params = {
                "datasetid": "GHCND",  # Global Historical Climatology Network Daily
                "stationid": station_id,
                "startdate": start_date,
                "enddate": end_date,
                "datatypeid": data_type,
                "limit": 1000
            }

            # Buscar dados climáticos (Tier 1 Resilient)
            response = await self.climate_client.get("/data", params=params)
            response.raise_for_status()
            data = response.json()

            return {
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "data_type": data_type,
                "period": f"{start_date} to {end_date}",
                "station_id": station_id,
                "results": data.get("results", []),
                "count": data.get("metadata", {}).get("resultset", {}).get("count", 0),
                "source": "NOAA Climate Data Online",
                "timestamp": datetime.now().isoformat()
            }

        except (requests.RequestException, HTTPException) as e:
            logger.warning(f"Erro na API do NOAA: {e}. Tentando fallback Embrapa.")
            # Fallback para Embrapa - tentar geocodificar novamente se necessário
            try:
                # Se geocoding já foi feito, usar as coordenadas
                if 'latitude' in locals() and 'longitude' in locals():
                    pass  # Usar latitude e longitude já obtidas
                else:
                    # Tentar geocodificar novamente
                    geo_data = await self.geocoding_service.geocode_address(location)
                    latitude = geo_data["latitude"]
                    longitude = geo_data["longitude"]

                embrapa_data = await self.embrapa_service.get_climate_data(
                    latitude, longitude, start_date, end_date
                )
                return {
                    "location": location,
                    "latitude": latitude if 'latitude' in locals() else None,
                    "longitude": longitude if 'longitude' in locals() else None,
                    "data_type": data_type,
                    "period": f"{start_date} to {end_date}",
                    "results": embrapa_data,
                    "count": len(embrapa_data),
                    "source": "Embrapa (NOAA fallback)",
                    "timestamp": datetime.now().isoformat(),
                    "fallback_used": True,
                    "original_error": str(e)
                }
            except Exception as embrapa_error:
                logger.error(f"Erro no fallback Embrapa: {embrapa_error}")
                return self._mock_climate_data(location, start_date, end_date, data_type)

    async def _get_station_id(self, latitude: float, longitude: float, radius: int = 25) -> Optional[str]:
        """
        Busca o ID da estação meteorológica mais próxima usando coordenadas.
        A API do NOAA CDO suporta 'extent' (minlat, minlon, maxlat, maxlon).
        """
        try:
            # Definir a caixa delimitadora (bounding box) baseada no raio (aproximado)
            # 0.1 grau é aproximadamente 11km
            delta = (radius / 111.0)
            extent = f"{latitude-delta},{longitude-delta},{latitude+delta},{longitude+delta}"
            
            params = {
                "datasetid": "GHCND",
                "extent": extent,
                "limit": 10
            }

            response = await self.climate_client.get("/stations", params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                # Retorna a primeira estação encontrada (geralmente a mais próxima se ordenado por NOAA)
                return data["results"][0]["id"]

        except Exception as e:
            logger.error(f"Erro ao buscar station ID por coordenadas: {e}")

        return None

    async def get_weather_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Busca previsão do tempo usando a API do National Weather Service com fallback para Embrapa
        """
        if self.use_mock:
            return self._mock_weather_forecast(latitude, longitude)

        try:
            # Primeiro, obter o escritório do NWS para as coordenadas (Tier 1 Resilient)
            point_response = await self.forecast_client.get(f"/points/{latitude},{longitude}")
            point_response.raise_for_status()
            point_data = point_response.json()

            # Obter a previsão
            forecast_url_full = point_data["properties"]["forecast"]
            forecast_path = forecast_url_full.replace(self.base_urls["weather_forecast"], "")
            
            forecast_response = await self.forecast_client.get(forecast_path)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            return {
                "latitude": latitude,
                "longitude": longitude,
                "forecast": forecast_data.get("properties", {}).get("periods", []),
                "updated": forecast_data.get("properties", {}).get("updated"),
                "source": "National Weather Service",
                "timestamp": datetime.now().isoformat()
            }

        except requests.RequestException as e:
            logger.warning(f"Erro na API do Weather Forecast: {e}. Tentando fallback Embrapa.")
            # Fallback para Embrapa
            try:
                embrapa_forecast = await self.embrapa_service.get_weather_forecast(
                    latitude, longitude, days=7
                )
                return {
                    "latitude": latitude,
                    "longitude": longitude,
                    "forecast": embrapa_forecast.get("previsao", []),
                    "updated": embrapa_forecast.get("timestamp"),
                    "source": "Embrapa (NOAA fallback)",
                    "timestamp": datetime.now().isoformat(),
                    "fallback_used": True,
                    "original_error": str(e)
                }
            except Exception as embrapa_error:
                logger.error(f"Erro no fallback Embrapa forecast: {embrapa_error}")
                return self._mock_weather_forecast(latitude, longitude)

    def _mock_climate_data(self, location: str, start_date: str, end_date: str,
                          data_type: str) -> Dict[str, Any]:
        """
        Dados mock para quando a API não está disponível
        """
        import random

        # Gerar dados simulados baseados no tipo
        data_points = []
        current_date = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        while current_date <= end:
            if data_type == "TMAX":
                value = random.uniform(15, 35)  # Temperatura em Celsius
            elif data_type == "TMIN":
                value = random.uniform(5, 20)
            elif data_type == "PRCP":
                value = random.uniform(0, 50)  # Precipitação em mm
            else:
                value = random.uniform(0, 100)

            data_points.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "datatype": data_type,
                "station": f"MOCK_STATION_{location.upper().replace(' ', '_')}",
                "value": round(value, 2),
                "attributes": ",,N,"
            })

            current_date += timedelta(days=1)

        return {
            "location": location,
            "data_type": data_type,
            "period": f"{start_date} to {end_date}",
            "station_id": f"MOCK_STATION_{location.upper().replace(' ', '_')}",
            "results": data_points[:100],  # Limitar a 100 pontos
            "count": len(data_points),
            "source": "NOAA Climate Data (MOCK MODE)",
            "timestamp": datetime.now().isoformat(),
            "note": "Dados simulados - API key não configurada ou serviço indisponível"
        }

    def _mock_weather_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Previsão mock para quando a API não está disponível
        """
        import random

        periods = []
        current_time = datetime.now()

        for i in range(14):  # 14 períodos (2 semanas)
            period_start = current_time + timedelta(hours=i*12)

            periods.append({
                "number": i + 1,
                "name": f"Period {i + 1}",
                "startTime": period_start.isoformat(),
                "endTime": (period_start + timedelta(hours=12)).isoformat(),
                "isDaytime": i % 2 == 0,
                "temperature": random.randint(15, 35),
                "temperatureUnit": "C",
                "temperatureTrend": None,
                "windSpeed": f"{random.randint(5, 25)} km/h",
                "windDirection": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
                "icon": "https://api.weather.gov/icons/land/day/skc",
                "shortForecast": random.choice([
                    "Sunny", "Partly Cloudy", "Mostly Cloudy", "Light Rain",
                    "Heavy Rain", "Thunderstorms", "Clear", "Overcast"
                ]),
                "detailedForecast": f"Weather forecast for period {i + 1}. Conditions are expected to be variable with temperatures around {random.randint(15, 35)}°C."
            })

        return {
            "latitude": latitude,
            "longitude": longitude,
            "forecast": periods,
            "updated": datetime.now().isoformat(),
            "source": "National Weather Service (MOCK MODE)",
            "timestamp": datetime.now().isoformat(),
            "note": "Previsão simulada - API não disponível"
        }

    def get_service_status(self) -> Dict[str, Any]:
        """
        Verifica o status do serviço NOAA
        """
        return {
            "service": "NOAA Integration",
            "api_key_configured": bool(self.api_key),
            "mock_mode": self.use_mock,
            "available_apis": list(self.base_urls.keys()),
            "status": "active" if self.api_key else "mock_mode",
            "timestamp": datetime.now().isoformat()
        }
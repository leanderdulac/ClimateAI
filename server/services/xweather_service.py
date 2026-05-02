"""
XWeather API Integration Service
Provides real-time weather conditions and forecasts
API: https://www.xweather.com/
"""

import logging
import urllib.request
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from services.embrapa_service import EmbrapaService
from config.config import settings

logger = logging.getLogger(__name__)


@dataclass
class XWeatherCondition:
    """Condições climáticas atuais do XWeather"""
    location: str
    latitude: float
    longitude: float
    temperature: float
    feels_like: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    visibility: float
    dew_point: float
    weather_code: int
    weather_description: str
    precip_1hr: float
    precip_24hr: float
    snow_1hr: float
    snow_24hr: float
    solar_radiation: float
    uv_index: float
    ceiling: float
    observation_time: str
    source: str = "XWeather"


@dataclass
class XWeatherForecast:
    """Previsão do XWeather"""
    location: str
    latitude: float
    longitude: float
    forecast_date: str
    temperature_high: float
    temperature_low: float
    humidity: int
    precipitation: float
    precipitation_probability: float
    wind_speed: float
    wind_direction: int
    weather_code: int
    weather_description: str
    sunrise: str
    sunset: str
    source: str = "XWeather"


class XWeatherService:
    """
    Serviço de integração com XWeather API
    Documentação: https://www.xweather.com/develop
    """
    
    # XWeather API credentials (loaded from settings/env)
    CLIENT_ID = settings.XWEATHER_CLIENT_ID
    CLIENT_SECRET = settings.XWEATHER_CLIENT_SECRET
    
    # API endpoints
    BASE_URL = "https://data.api.xweather.com"
    CONDITIONS_ENDPOINT = "/conditions/:auto"
    FORECAST_ENDPOINT = "/forecast/:auto"
    
    def __init__(self):
        self.use_mock = False
        self.embrapa_service = EmbrapaService()
        logger.info("XWeather Service initialized")
    
    def _build_url(self, endpoint: str, params: Dict = None) -> str:
        """Construir URL da API XWeather"""
        base = f"{self.BASE_URL}{endpoint}"
        
        # Adicionar parâmetros de autenticação
        auth_params = {
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'format': 'geojson'
        }
        
        if params:
            auth_params.update(params)
        
        # Construir query string
        query_string = '&'.join([f"{k}={v}" for k, v in auth_params.items()])
        return f"{base}?{query_string}"
    
    def _make_request(self, url: str, timeout: int = 10) -> Optional[Dict]:
        """
        Fazer requisição para API XWeather
        
        Args:
            url: URL completa da API
            timeout: Timeout em segundos
        
        Returns:
            Dict com resposta ou None em caso de erro
        """
        try:
            # Security: reject non-HTTPS URLs to prevent file:/ or custom-scheme abuse (B310)
            if not url.startswith("https://"):
                logger.error("XWeather: URL rejected — only HTTPS is permitted")
                return None
            # Log only the path, never the query string (which contains client_secret)
            safe_log_url = url.split("?")[0]
            logger.info(f"XWeather API request: {safe_log_url}")
            request = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'ClimateWise/1.0',
                    'Accept': 'application/json'
                }
            )
            
            with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 — HTTPS enforced above
                data = response.read()
                result = json.loads(data)
                
                if result.get('success'):
                    logger.info("XWeather API request successful")
                    return result
                else:
                    error_msg = result.get('error', {}).get('description', 'Unknown error')
                    logger.error(f"XWeather API error: {error_msg}")
                    return None
                    
        except urllib.error.HTTPError as e:
            logger.error(f"XWeather HTTP Error {e.code}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"XWeather URL Error: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"XWeather JSON Decode Error: {e}")
            return None
        except Exception as e:
            logger.error(f"XWeather unexpected error: {e}")
            return None
    
    def get_current_conditions(
        self,
        latitude: float,
        longitude: float,
        limit: int = 1
    ) -> Optional[XWeatherCondition]:
        """
        Obter condições climáticas atuais
        
        Args:
            latitude: Latitude da localização
            longitude: Longitude da localização
            limit: Número de estações para retornar
        
        Returns:
            XWeatherCondition ou None em caso de erro
        """
        try:
            # Construir endpoint com coordenadas
            endpoint = self.CONDITIONS_ENDPOINT.replace(':auto', f'{latitude},{longitude}')
            
            # Parâmetros da requisição
            params = {
                'plimit': str(limit),
                'filter': '1min'
            }
            
            url = self._build_url(endpoint, params)
            result = self._make_request(url)
            
            if result and result.get('success'):
                # Extrair dados da resposta
                features = result.get('features', [])
                if features:
                    feature = features[0]
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    coordinates = geometry.get('coordinates', [0, 0])
                    
                    # Mapear para XWeatherCondition
                    condition = XWeatherCondition(
                        location=properties.get('place', f'{latitude},{longitude}'),
                        latitude=coordinates[1] if len(coordinates) > 1 else latitude,
                        longitude=coordinates[0] if len(coordinates) > 0 else longitude,
                        temperature=properties.get('temperature', 0),
                        feels_like=properties.get('feelsLike', 0),
                        humidity=properties.get('humidity', 0),
                        pressure=properties.get('pressure', 0),
                        wind_speed=properties.get('windSpeed', 0),
                        wind_direction=properties.get('windDirection', 0),
                        visibility=properties.get('visibility', 0),
                        dew_point=properties.get('dewPoint', 0),
                        weather_code=properties.get('weatherCode', 0),
                        weather_description=properties.get('weatherDescription', ''),
                        precip_1hr=properties.get('precip1HR', 0),
                        precip_24hr=properties.get('precip24HR', 0),
                        snow_1hr=properties.get('snow1HR', 0),
                        snow_24hr=properties.get('snow24HR', 0),
                        solar_radiation=properties.get('solarRadiation', 0),
                        uv_index=properties.get('uvIndex', 0),
                        ceiling=properties.get('ceiling', 0),
                        observation_time=properties.get('observationTime', ''),
                        source="XWeather"
                    )
                    
                    logger.info(f"XWeather conditions retrieved: {condition.temperature}°C")
                    return condition
            
            logger.warning("XWeather returned no data")
            return None
            
        except Exception as e:
            logger.error(f"Error getting XWeather conditions: {e}")
            return None
    
    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7
    ) -> Optional[List[XWeatherForecast]]:
        """
        Obter previsão climática
        
        Args:
            latitude: Latitude da localização
            longitude: Longitude da localização
            days: Número de dias de previsão
        
        Returns:
            Lista de XWeatherForecast ou None
        """
        try:
            # Construir endpoint com coordenadas
            endpoint = self.FORECAST_ENDPOINT.replace(':auto', f'{latitude},{longitude}')
            
            # Parâmetros da requisição
            params = {
                'plimit': str(days)
            }
            
            url = self._build_url(endpoint, params)
            result = self._make_request(url)
            
            if result and result.get('success'):
                features = result.get('features', [])
                forecasts = []
                
                for feature in features:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    coordinates = geometry.get('coordinates', [0, 0])
                    
                    forecast = XWeatherForecast(
                        location=properties.get('place', f'{latitude},{longitude}'),
                        latitude=coordinates[1] if len(coordinates) > 1 else latitude,
                        longitude=coordinates[0] if len(coordinates) > 0 else longitude,
                        forecast_date=properties.get('validTime', '').split('T')[0],
                        temperature_high=properties.get('temperatureHigh', 0),
                        temperature_low=properties.get('temperatureLow', 0),
                        humidity=properties.get('humidity', 0),
                        precipitation=properties.get('precipAmount', 0),
                        precipitation_probability=properties.get('precipProbability', 0),
                        wind_speed=properties.get('windSpeed', 0),
                        wind_direction=properties.get('windDirection', 0),
                        weather_code=properties.get('weatherCode', 0),
                        weather_description=properties.get('weatherDescription', ''),
                        sunrise=properties.get('sunrise', ''),
                        sunset=properties.get('sunset', ''),
                        source="XWeather"
                    )
                    forecasts.append(forecast)
                
                logger.info(f"XWeather forecast retrieved: {len(forecasts)} days")
                return forecasts
            
            logger.warning("XWeather forecast returned no data")
            return None
            
        except Exception as e:
            logger.error(f"Error getting XWeather forecast: {e}")
            return None
    
    def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Obter dados climáticos completos (atuais + previsão)
        Método principal para integração com ClimateWise
    
        Args:
            latitude: Latitude
            longitude: Longitude
            days: Dias de previsão
        
        Returns:
            Dict com dados atuais e previsão
        """
        result = {
            'success': False,
            'source': 'XWeather',
            'current': None,
            'forecast': [],
            'error': None
        }
        
        try:
            # Obter condições atuais
            current = self.get_current_conditions(latitude, longitude)
            if current:
                result['current'] = {
                    'temperature': current.temperature,
                    'feels_like': current.feels_like,
                    'humidity': current.humidity,
                    'pressure': current.pressure,
                    'wind_speed': current.wind_speed,
                    'wind_direction': current.wind_direction,
                    'weather_code': current.weather_code,
                    'weather_description': current.weather_description,
                    'precipitation': current.precip_1hr,
                    'observation_time': current.observation_time,
                    'source': current.source
                }
            
            # Obter previsão
            forecast = self.get_forecast(latitude, longitude, days)
            if forecast:
                result['forecast'] = [
                    {
                        'date': f.forecast_date,
                        'temperature_high': f.temperature_high,
                        'temperature_low': f.temperature_low,
                        'humidity': f.humidity,
                        'precipitation': f.precipitation,
                        'precipitation_probability': f.precipitation_probability,
                        'wind_speed': f.wind_speed,
                        'wind_direction': f.wind_direction,
                        'weather_code': f.weather_code,
                        'weather_description': f.weather_description,
                        'source': f.source
                    }
                    for f in forecast
                ]
            
            result['success'] = bool(current or forecast)
            
            if not result['success']:
                result['error'] = 'No data available from XWeather'
                logger.warning("XWeather returned no data, falling back to Embrapa")
                
                # Fallback para Embrapa
                embrapa_data = self.embrapa_service.obter_historico(
                    latitude, longitude,
                    datetime.now(), datetime.now()
                )
                if embrapa_data:
                    result['current'] = {
                        'temperature': embrapa_data[0].temperatura,
                        'humidity': embrapa_data[0].umidade,
                        'precipitation': embrapa_data[0].precipitacao,
                        'wind_speed': embrapa_data[0].vento_velocidade,
                        'wind_direction': embrapa_data[0].vento_direcao,
                        'source': 'Embrapa (fallback)'
                    }
                    result['success'] = True
                    result['source'] = 'Embrapa (fallback)'
            
            return result
            
        except Exception as e:
            logger.error(f"Error in get_weather_data: {e}")
            result['error'] = str(e)
            return result
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Obter status do serviço XWeather
        
        Returns:
            Dict com status do serviço
        """
        return {
            'service': 'XWeather Integration',
            'status': 'active',
            'api_key_configured': bool(settings.XWEATHER_CLIENT_ID and settings.XWEATHER_CLIENT_SECRET),
            'base_url': self.BASE_URL,
            'endpoints': [
                'conditions',
                'forecast'
            ],
            'features': [
                'current_conditions',
                'weather_forecast',
                'real_time_data',
                'solar_radiation',
                'uv_index'
            ],
            'fallback': 'Embrapa/OpenMeteo',
            'timestamp': datetime.now().isoformat()
        }

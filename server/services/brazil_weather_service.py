"""
Brazilian Weather Data Services
Serviços alternativos para dados meteorológicos do Brasil

Fontes:
1. OpenMeteo (com foco no Brasil) - Mais confiável que INMET
2. WeatherAPI (cobertura global)
3. HG Brasil Weather API (API brasileira comercial)

Nota: A API oficial do INMET (apitempo.inmet.gov.br) está frequentemente
indisponível. Estas alternativas usam as mesmas fontes (estações INMET)
mas com infraestrutura mais confiável.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class BrazilWeatherData:
    """Dados meteorológicos para Brasil"""
    location: str
    state: str
    latitude: float
    longitude: float
    date: str
    temperature_max: float  # °C
    temperature_min: float  # °C
    temperature_avg: float  # °C
    precipitation: float  # mm
    humidity: float  # %
    wind_speed: float  # km/h
    wind_direction: int  # graus
    pressure: float  # hPa
    source: str  # 'openmeteo', 'weatherapi', 'hgbrazil'


class BrazilWeatherService:
    """
    Serviço unificado para dados meteorológicos do Brasil
    
    Prioridade de fontes:
    1. OpenMeteo (gratuito, confiável, usa estações INMET)
    2. WeatherAPI (comercial, mais preciso)
    3. HG Brasil (API brasileira, comercial)
    """
    
    # OpenMeteo API (gratuito, usa dados INMET)
    OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
    
    # WeatherAPI (comercial)
    WEATHERAPI_URL = "https://api.weatherapi.com/v1"
    
    # HG Brasil Weather (comercial brasileiro)
    HGBRASIL_URL = "https://api.hgbrasil.com/weather"
    
    def __init__(self, weatherapi_key: str = None, hgbrazil_key: str = None):
        """
        Inicializar serviço
        
        Args:
            weatherapi_key: API key para WeatherAPI
            hgbrazil_key: API key para HG Brasil
        """
        self.weatherapi_key = weatherapi_key or os.getenv('WEATHERAPI_KEY')
        self.hgbrazil_key = hgbrazil_key or os.getenv('HGBRASIL_KEY')
        
        logger.info("BrazilWeatherService initialized")
    
    def get_historical_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        source: str = 'openmeteo'
    ) -> List[BrazilWeatherData]:
        """
        Obter dados históricos
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Data inicial
            end_date: Data final
            source: Fonte de dados ('openmeteo', 'weatherapi', 'hgbrazil')
        
        Returns:
            Lista de dados meteorológicos
        """
        if source == 'openmeteo':
            return self._get_openmeteo_historical(latitude, longitude, start_date, end_date)
        elif source == 'weatherapi' and self.weatherapi_key:
            return self._get_weatherapi_historical(latitude, longitude, start_date, end_date)
        elif source == 'hgbrazil' and self.hgbrazil_key:
            return self._get_hgbrazil_historical(latitude, longitude, start_date, end_date)
        else:
            # Fallback para OpenMeteo
            logger.warning(f"Source {source} not available, using OpenMeteo")
            return self._get_openmeteo_historical(latitude, longitude, start_date, end_date)
    
    def _get_openmeteo_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> List[BrazilWeatherData]:
        """
        Obter dados históricos do OpenMeteo
        
        OpenMeteo usa dados de estações INMET para Brasil
        """
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation,relativehumidity_2m,windspeed_10m,winddirection_10m,surface_pressure',
                'timezone': 'America/Sao_Paulo'
            }
            
            response = requests.get(self.OPENMETEO_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Processar dados
            daily = data.get('daily', {})
            results = []
            
            for i in range(len(daily.get('time', []))):
                results.append(BrazilWeatherData(
                    location=f"{latitude},{longitude}",
                    state='',
                    latitude=latitude,
                    longitude=longitude,
                    date=daily['time'][i],
                    temperature_max=daily.get('temperature_2m_max', [None] * len(daily['time']))[i] or 0,
                    temperature_min=daily.get('temperature_2m_min', [None] * len(daily['time']))[i] or 0,
                    temperature_avg=daily.get('temperature_2m_mean', [None] * len(daily['time']))[i] or 0,
                    precipitation=daily.get('precipitation', [None] * len(daily['time']))[i] or 0,
                    humidity=daily.get('relativehumidity_2m', [None] * len(daily['time']))[i] or 0,
                    wind_speed=daily.get('windspeed_10m', [None] * len(daily['time']))[i] or 0,
                    wind_direction=daily.get('winddirection_10m', [None] * len(daily['time']))[i] or 0,
                    pressure=daily.get('surface_pressure', [None] * len(daily['time']))[i] or 0,
                    source='openmeteo'
                ))
            
            logger.info(f"Retrieved {len(results)} days from OpenMeteo")
            return results
            
        except Exception as e:
            logger.error(f"Error getting OpenMeteo data: {e}")
            return []
    
    def _get_weatherapi_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> List[BrazilWeatherData]:
        """
        Obter dados históricos do WeatherAPI
        """
        if not self.weatherapi_key:
            logger.warning("WeatherAPI key not configured")
            return []
        
        try:
            results = []
            current_date = start_date
            
            while current_date <= end_date:
                params = {
                    'key': self.weatherapi_key,
                    'q': f"{latitude},{longitude}",
                    'dt': current_date.strftime('%Y-%m-%d'),
                    'lang': 'pt'
                }
                
                response = requests.get(
                    f"{self.WEATHERAPI_URL}/history.json",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Processar dados diários
                if 'forecast' in data and 'forecastday' in data['forecast']:
                    for day in data['forecast']['forecastday']:
                        astro = day.get('astro', {})
                        day_data = day.get('day', {})
                        
                        results.append(BrazilWeatherData(
                            location=data.get('location', {}).get('name', ''),
                            state=data.get('location', {}).get('region', ''),
                            latitude=latitude,
                            longitude=longitude,
                            date=day['date'],
                            temperature_max=day_data.get('maxtemp_c', 0),
                            temperature_min=day_data.get('mintemp_c', 0),
                            temperature_avg=day_data.get('avgtemp_c', 0),
                            precipitation=day_data.get('totalprecip_mm', 0),
                            humidity=day_data.get('avghumidity', 0),
                            wind_speed=day_data.get('maxwind_kph', 0),
                            wind_direction=0,  # WeatherAPI não fornece direção no histórico diário
                            pressure=0,  # WeatherAPI não fornece pressão no histórico diário
                            source='weatherapi'
                        ))
                
                current_date += timedelta(days=1)
            
            logger.info(f"Retrieved {len(results)} days from WeatherAPI")
            return results
            
        except Exception as e:
            logger.error(f"Error getting WeatherAPI data: {e}")
            return []
    
    def _get_hgbrazil_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> List[BrazilWeatherData]:
        """
        Obter dados históricos da HG Brasil
        API brasileira com dados de estações locais
        """
        if not self.hgbrazil_key:
            logger.warning("HG Brasil key not configured")
            return []
        
        try:
            results = []
            current_date = start_date
            
            while current_date <= end_date:
                params = {
                    'key': self.hgbrazil_key,
                    'lat': latitude,
                    'lon': longitude,
                    'start_date': current_date.strftime('%Y-%m-%d'),
                    'end_date': current_date.strftime('%Y-%m-%d'),
                    'lang': 'pt'
                }
                
                response = requests.get(self.HGBRASIL_URL, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('valid_key') and 'results' in data:
                    results_data = data['results']
                    
                    results.append(BrazilWeatherData(
                        location=results_data.get('city_name', ''),
                        state=results_data.get('state', ''),
                        latitude=latitude,
                        longitude=longitude,
                        date=current_date.strftime('%Y-%m-%d'),
                        temperature_max=results_data.get('max_temp', 0),
                        temperature_min=results_data.get('min_temp', 0),
                        temperature_avg=results_data.get('temp', 0),
                        precipitation=results_data.get('rain', 0),
                        humidity=results_data.get('humidity', 0),
                        wind_speed=results_data.get('wind_speed', 0),
                        wind_direction=results_data.get('wind_direction', 0),
                        pressure=results_data.get('pressure', 0),
                        source='hgbrazil'
                    ))
                
                current_date += timedelta(days=1)
            
            logger.info(f"Retrieved {len(results)} days from HG Brasil")
            return results
            
        except Exception as e:
            logger.error(f"Error getting HG Brasil data: {e}")
            return []
    
    def get_current_conditions(
        self,
        latitude: float,
        longitude: float,
        source: str = 'openmeteo'
    ) -> Optional[BrazilWeatherData]:
        """
        Obter condições atuais
        
        Args:
            latitude: Latitude
            longitude: Longitude
            source: Fonte de dados
        
        Returns:
            Dados meteorológicos atuais ou None
        """
        # OpenMeteo não tem endpoint de "current" gratuito, usar WeatherAPI
        if source == 'weatherapi' and self.weatherapi_key:
            try:
                params = {
                    'key': self.weatherapi_key,
                    'q': f"{latitude},{longitude}",
                    'lang': 'pt'
                }
                
                response = requests.get(
                    f"{self.WEATHERAPI_URL}/current.json",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                
                if 'current' in data:
                    current = data['current']
                    
                    return BrazilWeatherData(
                        location=data.get('location', {}).get('name', ''),
                        state=data.get('location', {}).get('region', ''),
                        latitude=latitude,
                        longitude=longitude,
                        date=datetime.now().strftime('%Y-%m-%d'),
                        temperature_max=current.get('temp_c', 0),
                        temperature_min=current.get('temp_c', 0),
                        temperature_avg=current.get('temp_c', 0),
                        precipitation=0,
                        humidity=current.get('humidity', 0),
                        wind_speed=current.get('wind_kph', 0),
                        wind_direction=current.get('wind_dir', 0),
                        pressure=current.get('pressure_mb', 0),
                        source='weatherapi'
                    )
                
            except Exception as e:
                logger.error(f"Error getting current conditions: {e}")
        
        # Fallback: usar dados mais recentes do OpenMeteo
        return self._get_latest_openmeteo_data(latitude, longitude)
    
    def _get_latest_openmeteo_data(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[BrazilWeatherData]:
        """
        Obter dados mais recentes do OpenMeteo (últimos 7 dias)
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            data = self._get_openmeteo_historical(latitude, longitude, start_date, end_date)
            
            if data:
                # Retornar último dia
                return data[-1]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest OpenMeteo data: {e}")
            return None
    
    def calculate_rainfall_percentiles(
        self,
        latitude: float,
        longitude: float,
        percentiles: List[int] = [95, 99],
        historical_years: int = 30
    ) -> Dict[str, float]:
        """
        Calcular percentis de chuva para uma localização
        
        Args:
            latitude: Latitude
            longitude: Longitude
            percentiles: Percentis para calcular
            historical_years: Anos de histórico
        
        Returns:
            Dict com percentis
        """
        import numpy as np
        
        # Obter dados históricos
        end_date = datetime.now()
        start_date = end_date - timedelta(days=historical_years * 365)
        
        data = self._get_openmeteo_historical(latitude, longitude, start_date, end_date)
        
        if not data:
            return {f'p{p}': 0.0 for p in percentiles}
        
        # Extrair precipitação
        precipitation_values = [d.precipitation for d in data if d.precipitation is not None]
        
        if not precipitation_values:
            return {f'p{p}': 0.0 for p in percentiles}
        
        # Calcular percentis
        result = {}
        for p in percentiles:
            result[f'p{p}'] = float(np.percentile(precipitation_values, p))
        
        logger.info(f"Calculated rainfall percentiles: {result}")
        return result
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Obter status dos serviços
        
        Returns:
            Dict com status de cada fonte
        """
        return {
            'service': 'BrazilWeatherService',
            'sources': {
                'openmeteo': {
                    'status': 'active',
                    'url': self.OPENMETEO_URL,
                    'cost': 'free',
                    'reliability': 'high',
                    'data_source': 'INMET stations via OpenMeteo'
                },
                'weatherapi': {
                    'status': 'active' if self.weatherapi_key else 'inactive',
                    'url': self.WEATHERAPI_URL,
                    'cost': 'commercial',
                    'reliability': 'very_high',
                    'data_source': 'Global + INMET'
                },
                'hgbrazil': {
                    'status': 'active' if self.hgbrazil_key else 'inactive',
                    'url': self.HGBRASIL_URL,
                    'cost': 'commercial',
                    'reliability': 'high',
                    'data_source': 'Brazilian stations'
                }
            },
            'recommended_source': 'openmeteo',
            'timestamp': datetime.now().isoformat()
        }

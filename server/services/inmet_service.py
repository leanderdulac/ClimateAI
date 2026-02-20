"""
INMET (Instituto Nacional de Meteorologia - Brasil) Service
Fornece dados meteorológicos oficiais do Brasil

Fontes:
- Estações meteorológicas automáticas (EMA)
- Estações meteorológicas de superfície (EMS)
- Dados históricos e em tempo real

API: https://portal.inmet.gov.br/
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class INMETStation:
    """Estação meteorológica do INMET"""
    station_id: str
    station_name: str
    state: str
    city: str
    latitude: float
    longitude: float
    altitude: float
    station_type: str  # EMA (automática) or EMS (convencional)


@dataclass
class INMETObservation:
    """Observação meteorológica do INMET"""
    station_id: str
    observation_date: str
    observation_time: str
    temperature: Optional[float]  # °C
    humidity: Optional[float]  # %
    pressure: Optional[float]  # hPa
    wind_speed: Optional[float]  # m/s
    wind_direction: Optional[int]  # graus
    precipitation: Optional[float]  # mm
    solar_radiation: Optional[float]  # W/m²
    evaporation: Optional[float]  # mm


class INMETService:
    """
    Serviço de integração com INMET
    
    Endpoints:
    - Estações: https://apitempo.inmet.gov.br/estacoes
    - Dados horários: https://apitempo.inmet.gov.br/observacao/{data_hora}/{data_hora}/{codigo_estacao}
    - Dados diários: https://apitempo.inmet.gov.br/observacao/{data_inicial}/{data_final}/{codigo_estacao}
    """
    
    # INMET API base URL
    BASE_URL = "https://apitempo.inmet.gov.br"
    
    def __init__(self, api_key: str = None):
        """
        Inicializar serviço INMET
        
        Args:
            api_key: API key (opcional, API pública não requer key)
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ClimateAI/1.0',
            'Accept': 'application/json'
        })
        
        logger.info("INMET Service initialized")
    
    def get_stations(self, station_type: str = None) -> List[INMETStation]:
        """
        Obter lista de estações meteorológicas
        
        Args:
            station_type: Tipo de estação ('EMA' or 'EMS')
        
        Returns:
            Lista de estações
        """
        try:
            endpoint = f"{self.BASE_URL}/estacoes/{station_type}" if station_type else f"{self.BASE_URL}/estacoes"
            
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            
            stations_data = response.json()
            
            stations = []
            for station in stations_data:
                stations.append(INMETStation(
                    station_id=station.get('CD_ESTACAO', ''),
                    station_name=station.get('DC_NOME', ''),
                    state=station.get('SG_UF', ''),
                    city=station.get('DC_DISTRITO', ''),
                    latitude=float(station.get('VL_LATITUDE', 0).replace(',', '.')),
                    longitude=float(station.get('VL_LONGITUDE', 0).replace(',', '.')),
                    altitude=float(station.get('VL_ALTITUDE', 0)),
                    station_type=station.get('TP_ESTACAO', '')
                ))
            
            logger.info(f"Retrieved {len(stations)} INMET stations")
            return stations
            
        except Exception as e:
            logger.error(f"Error getting INMET stations: {e}")
            return []
    
    def get_hourly_data(
        self,
        station_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[INMETObservation]:
        """
        Obter dados horários de uma estação
        
        Args:
            station_id: Código da estação
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            Lista de observações horárias
        """
        try:
            # Format dates for API (YYYY-MM-DD)
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            endpoint = f"{self.BASE_URL}/observacao/{start_str}/{end_str}/{station_id}"
            
            response = self.session.get(endpoint, timeout=30)
            response.raise_for_status()
            
            observations_data = response.json()
            
            observations = []
            for obs in observations_data:
                observations.append(INMETObservation(
                    station_id=station_id,
                    observation_date=obs.get('DT_MEDIDAO', ''),
                    observation_time=obs.get('HR_MEDIDAO', ''),
                    temperature=float(obs.get('TEM_INS', 0) or 0),
                    humidity=float(obs.get('UMD_INS', 0) or 0),
                    pressure=float(obs.get('PRE_INS', 0) or 0),
                    wind_speed=float(obs.get('VNT_VEL_INS', 0) or 0),
                    wind_direction=int(obs.get('VNT_DIRE_INS', 0) or 0),
                    precipitation=float(obs.get('CHUVA_INS', 0) or 0),
                    solar_radiation=float(obs.get('RAD_GLOB_INS', 0) or 0),
                    evaporation=float(obs.get('EVAP_INS', 0) or 0)
                ))
            
            logger.info(f"Retrieved {len(observations)} hourly observations from station {station_id}")
            return observations
            
        except Exception as e:
            logger.error(f"Error getting hourly data from INMET: {e}")
            return []
    
    def get_daily_data(
        self,
        station_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Obter dados diários de uma estação
        
        Args:
            station_id: Código da estação
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            Lista de dados diários
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            endpoint = f"{self.BASE_URL}/observacao/{start_str}/{end_str}/{station_id}"
            
            response = self.session.get(endpoint, timeout=30)
            response.raise_for_status()
            
            daily_data = response.json()
            
            # Aggregate hourly data to daily
            daily_observations = {}
            for obs in daily_data:
                date = obs.get('DT_MEDIDAO', '')
                if date not in daily_observations:
                    daily_observations[date] = {
                        'station_id': station_id,
                        'date': date,
                        'temperatures': [],
                        'humidity': [],
                        'pressure': [],
                        'wind_speed': [],
                        'precipitation': 0.0
                    }
                
                if obs.get('TEM_INS'):
                    daily_observations[date]['temperatures'].append(float(obs['TEM_INS']))
                if obs.get('UMD_INS'):
                    daily_observations[date]['humidity'].append(float(obs['UMD_INS']))
                if obs.get('PRE_INS'):
                    daily_observations[date]['pressure'].append(float(obs['PRE_INS']))
                if obs.get('VNT_VEL_INS'):
                    daily_observations[date]['wind_speed'].append(float(obs['VNT_VEL_INS']))
                if obs.get('CHUVA_INS'):
                    daily_observations[date]['precipitation'] += float(obs['CHUVA_INS'] or 0)
            
            # Calculate daily aggregates
            result = []
            for date, data in daily_observations.items():
                result.append({
                    'station_id': station_id,
                    'date': date,
                    'temperature_max': max(data['temperatures']) if data['temperatures'] else None,
                    'temperature_min': min(data['temperatures']) if data['temperatures'] else None,
                    'temperature_avg': sum(data['temperatures']) / len(data['temperatures']) if data['temperatures'] else None,
                    'humidity_avg': sum(data['humidity']) / len(data['humidity']) if data['humidity'] else None,
                    'pressure_avg': sum(data['pressure']) / len(data['pressure']) if data['pressure'] else None,
                    'wind_speed_max': max(data['wind_speed']) if data['wind_speed'] else None,
                    'precipitation': data['precipitation']
                })
            
            logger.info(f"Retrieved {len(result)} daily observations from station {station_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting daily data from INMET: {e}")
            return []
    
    def find_nearest_station(
        self,
        latitude: float,
        longitude: float,
        station_type: str = 'EMA'
    ) -> Optional[INMETStation]:
        """
        Encontrar estação mais próxima de uma coordenada
        
        Args:
            latitude: Latitude
            longitude: Longitude
            station_type: Tipo de estação preferida
        
        Returns:
            Estação mais próxima
        """
        try:
            stations = self.get_stations(station_type)
            
            if not stations:
                # Fallback to all stations
                stations = self.get_stations()
            
            if not stations:
                return None
            
            # Calculate distance to each station
            nearest = None
            min_distance = float('inf')
            
            for station in stations:
                # Haversine formula for distance
                distance = self._haversine_distance(
                    latitude, longitude,
                    station.latitude, station.longitude
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest = station
            
            if nearest:
                logger.info(f"Found nearest INMET station: {nearest.station_name} ({min_distance:.2f} km)")
            
            return nearest
            
        except Exception as e:
            logger.error(f"Error finding nearest INMET station: {e}")
            return None
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calcular distância entre duas coordenadas (fórmula de Haversine)
        
        Returns:
            Distância em km
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Obter dados meteorológicos para uma localização
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            Dict com dados meteorológicos
        """
        # Find nearest station
        station = self.find_nearest_station(latitude, longitude)
        
        if not station:
            return {
                'success': False,
                'error': 'No INMET station found nearby',
                'data': []
            }
        
        # Get daily data from station
        daily_data = self.get_daily_data(station.station_id, start_date, end_date)
        
        return {
            'success': True,
            'source': 'INMET',
            'station': {
                'id': station.station_id,
                'name': station.station_name,
                'distance_km': self._haversine_distance(
                    latitude, longitude,
                    station.latitude, station.longitude
                )
            },
            'data': daily_data
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Obter status do serviço INMET
        
        Returns:
            Dict com status do serviço
        """
        try:
            # Test API connectivity
            stations = self.get_stations()
            
            return {
                'service': 'INMET',
                'status': 'active' if stations else 'degraded',
                'total_stations': len(stations),
                'api_url': self.BASE_URL,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'service': 'INMET',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

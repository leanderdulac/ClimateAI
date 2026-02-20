"""
Copernicus Climate Data Store (CDS) Service
Fornece dados de reanálise ERA5 para histórico climático de longo prazo

Fontes:
- ERA5: Reanálise global de hora em hora (desde 1940)
- ERA5-Land: Reanálise de superfície com maior resolução

API: https://cds.climate.copernicus.eu/api/how-to

Requisitos:
- Registrar em https://cds.climate.copernicus.eu/
- Obter UID e API key
- Instalar: pip install cdsapi
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class ERA5Data:
    """Dados ERA5"""
    latitude: float
    longitude: float
    date: str
    temperature_2m: Optional[float]  # °C
    temperature_max: Optional[float]  # °C
    temperature_min: Optional[float]  # °C
    precipitation: Optional[float]  # m
    wind_speed_10m: Optional[float]  # m/s
    wind_direction_10m: Optional[float]  # graus
    pressure_msl: Optional[float]  # Pa
    humidity_2m: Optional[float]  # %
    evaporation: Optional[float]  # m
    solar_radiation: Optional[float]  # J/m²


class CopernicusService:
    """
    Serviço de integração com Copernicus Climate Data Store
    
    Datasets principais:
    - reanalysis-era5-single-levels: Variáveis de superfície única
    - reanalysis-era5-land: Dados de superfície terrestre
    """
    
    def __init__(self, uid: str = None, api_key: str = None):
        """
        Inicializar serviço Copernicus
        
        Args:
            uid: User ID do CDS
            api_key: API key do CDS
        """
        self.uid = uid or os.getenv('CDSAPI_UID')
        self.api_key = api_key or os.getenv('CDSAPI_KEY')
        
        self.cds_client = None
        self._initialized = False
        
        # Verificar se cdsapi está instalado
        try:
            import cdsapi
            self.cdsapi_available = True
        except ImportError:
            logger.warning("cdsapi not installed. Install with: pip install cdsapi")
            self.cdsapi_available = False
        
        logger.info("Copernicus Service initialized")
    
    def _initialize_client(self) -> bool:
        """
        Inicializar cliente CDS
        
        Returns:
            True se inicializado com sucesso
        """
        if not self.cdsapi_available:
            return False
        
        if not self.uid or not self.api_key:
            logger.warning("CDS API credentials not configured")
            return False
        
        try:
            import cdsapi
            
            self.cds_client = cdsapi.Client(
                url='https://cds.climate.copernicus.eu/api/v2',
                key=f'{self.uid}:{self.api_key}'
            )
            
            self._initialized = True
            logger.info("CDS client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing CDS client: {e}")
            return False
    
    def get_era5_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        variables: List[str] = None
    ) -> List[ERA5Data]:
        """
        Obter dados ERA5 para uma localização
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Data inicial
            end_date: Data final
            variables: Variáveis para buscar
        
        Returns:
            Lista de dados ERA5
        """
        if not self._initialized:
            if not self._initialize_client():
                logger.warning("CDS client not available, returning mock data")
                return self._get_mock_era5_data(latitude, longitude, start_date, end_date)
        
        try:
            import cdsapi
            
            # Default variables
            if variables is None:
                variables = [
                    '2m_temperature',
                    'total_precipitation',
                    '10m_wind_speed',
                    '10m_wind_direction',
                    'mean_sea_level_pressure',
                    '2m_dewpoint_temperature'
                ]
            
            # Prepare request
            request = {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': variables,
                'year': [str(y) for y in range(start_date.year, end_date.year + 1)],
                'month': [f'{m:02d}' for m in range(1, 13)],
                'day': [f'{d:02d}' for d in range(1, 32)],
                'time': [f'{h:02d}:00' for h in range(0, 24)],
                'area': [
                    latitude + 0.1,  # North
                    longitude - 0.1,  # West
                    latitude - 0.1,  # South
                    longitude + 0.1   # East
                ]
            }
            
            # Download data
            logger.info(f"Requesting ERA5 data for {latitude},{longitude}")
            result = self.cds_client.retrieve('reanalysis-era5-single-levels', request)
            
            # Process NetCDF file (simplified - in production, use xarray)
            data = self._process_netcdf_result(result, latitude, longitude)
            
            logger.info(f"Retrieved {len(data)} ERA5 data points")
            return data
            
        except Exception as e:
            logger.error(f"Error getting ERA5 data: {e}")
            # Fallback to mock data
            return self._get_mock_era5_data(latitude, longitude, start_date, end_date)
    
    def _get_mock_era5_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> List[ERA5Data]:
        """
        Gerar dados ERA5 mock (para desenvolvimento/testes)
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            Lista de dados ERA5 mock
        """
        import random
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate realistic mock data based on latitude and season
            month = current_date.month
            
            # Temperature seasonal variation (simplified)
            base_temp = 20 - (abs(latitude) / 90) * 10  # Base temperature
            seasonal_variation = 10 * (1 - abs(month - 6) / 6)  # Seasonal variation
            temp = base_temp + seasonal_variation + random.uniform(-3, 3)
            
            # Precipitation (random with seasonal pattern)
            precip_prob = 0.3 if month in [12, 1, 2] else 0.5
            precipitation = random.uniform(0, 20) if random.random() < precip_prob else 0
            
            data.append(ERA5Data(
                latitude=latitude,
                longitude=longitude,
                date=current_date.strftime('%Y-%m-%d'),
                temperature_2m=temp,
                temperature_max=temp + random.uniform(3, 8),
                temperature_min=temp - random.uniform(3, 8),
                precipitation=precipitation / 1000,  # Convert mm to m
                wind_speed_10m=random.uniform(2, 15),
                wind_direction_10m=random.randint(0, 360),
                pressure_msl=101325 + random.uniform(-2000, 2000),
                humidity_2m=random.uniform(40, 90),
                evaporation=random.uniform(0, 5) / 1000,
                solar_radiation=random.uniform(10, 30) * 1e6
            ))
            
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(data)} mock ERA5 data points")
        return data
    
    def _process_netcdf_result(self, result, latitude: float, longitude: float) -> List[ERA5Data]:
        """
        Processar arquivo NetCDF do resultado
        
        Args:
            result: Resultado do CDS
            latitude: Latitude
            longitude: Longitude
        
        Returns:
            Lista de dados ERA5
        """
        # In production, use xarray to process NetCDF
        # This is a placeholder
        logger.warning("NetCDF processing not implemented, returning mock data")
        
        # Return mock data for now
        return self._get_mock_era5_data(
            latitude, longitude,
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
    
    def calculate_climate_percentiles(
        self,
        latitude: float,
        longitude: float,
        variable: str,
        percentiles: List[int] = [95, 99],
        historical_years: int = 30
    ) -> Dict[str, float]:
        """
        Calcular percentis climáticos de longo prazo
        
        Args:
            latitude: Latitude
            longitude: Longitude
            variable: Variável (e.g., 'precipitation', 'temperature')
            percentiles: Percentis para calcular
            historical_years: Anos de histórico
        
        Returns:
            Dict com percentis
        """
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=historical_years * 365)
        
        data = self.get_era5_data(latitude, longitude, start_date, end_date)
        
        if not data:
            return {f'p{p}': 0.0 for p in percentiles}
        
        # Extract variable values
        values = []
        for d in data:
            value = getattr(d, variable, None)
            if value is not None:
                values.append(value)
        
        if not values:
            return {f'p{p}': 0.0 for p in percentiles}
        
        # Calculate percentiles
        import numpy as np
        
        result = {}
        for p in percentiles:
            result[f'p{p}'] = float(np.percentile(values, p))
        
        logger.info(f"Calculated percentiles for {variable}: {result}")
        return result
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Obter status do serviço Copernicus
        
        Returns:
            Dict com status do serviço
        """
        return {
            'service': 'Copernicus CDS',
            'status': 'active' if self._initialized else 'inactive',
            'cdsapi_available': self.cdsapi_available,
            'credentials_configured': bool(self.uid and self.api_key),
            'api_url': 'https://cds.climate.copernicus.eu/api/v2',
            'timestamp': datetime.now().isoformat()
        }

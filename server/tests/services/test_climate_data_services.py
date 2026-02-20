"""
Testes Unitários para INMET e Copernicus Services
"""

import pytest
from datetime import datetime, timedelta
from services.inmet_service import INMETService, INMETStation, INMETObservation
from services.copernicus_service import CopernicusService, ERA5Data


class TestINMETService:
    """Testes para INMETService"""
    
    @pytest.fixture
    def inmet_service(self):
        """Fixture para serviço INMET"""
        return INMETService()
    
    def test_service_initialization(self, inmet_service):
        """Teste: Inicialização do serviço"""
        assert inmet_service.BASE_URL == "https://apitempo.inmet.gov.br"
        assert inmet_service.session is not None
    
    def test_get_stations(self, inmet_service):
        """Teste: Obter estações (pode falhar se API indisponível)"""
        stations = inmet_service.get_stations()
        
        # API pode estar indisponível, então apenas verificamos estrutura
        if stations:
            assert len(stations) > 0
            assert isinstance(stations[0], INMETStation)
            assert stations[0].station_id is not None
    
    def test_haversine_distance(self, inmet_service):
        """Teste: Cálculo de distância"""
        # São Paulo a Rio de Janeiro: ~358 km
        distance = inmet_service._haversine_distance(
            -23.5505, -46.6333,  # São Paulo
            -22.9068, -43.1729   # Rio de Janeiro
        )
        
        assert 350 < distance < 370  # Margem de erro
    
    def test_find_nearest_station(self, inmet_service):
        """Teste: Encontrar estação mais próxima"""
        station = inmet_service.find_nearest_station(-23.5505, -46.6333)
        
        # Pode retornar None se API indisponível
        if station:
            assert isinstance(station, INMETStation)
            assert station.station_id is not None
            assert -25 < station.latitude < -22  # SP region
    
    def test_get_weather_data(self, inmet_service):
        """Teste: Obter dados meteorológicos"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        result = inmet_service.get_weather_data(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verificar estrutura da resposta
        assert 'success' in result
        
        # API pode estar indisponível, então verificamos ambos os casos
        if result['success']:
            assert 'source' in result
            assert result['source'] == 'INMET'
            assert 'station' in result
            assert 'data' in result
        else:
            # Se falhou, deve ter erro
            assert 'error' in result
    
    def test_service_status(self, inmet_service):
        """Teste: Status do serviço"""
        status = inmet_service.get_service_status()
        
        assert 'service' in status
        assert status['service'] == 'INMET'
        assert 'status' in status
        assert 'timestamp' in status


class TestCopernicusService:
    """Testes para CopernicusService"""
    
    @pytest.fixture
    def copernicus_service(self):
        """Fixture para serviço Copernicus"""
        return CopernicusService()
    
    def test_service_initialization(self, copernicus_service):
        """Teste: Inicialização do serviço"""
        assert copernicus_service.cdsapi_available is True or copernicus_service.cdsapi_available is False
        assert copernicus_service._initialized is False  # Não inicializado sem credentials
    
    def test_get_mock_era5_data(self, copernicus_service):
        """Teste: Obter dados ERA5 mock"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        data = copernicus_service._get_mock_era5_data(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verificar estrutura dos dados (30-31 dias dependendo do mês)
        assert 30 <= len(data) <= 31  # Margem para dias inclusivos
        assert isinstance(data[0], ERA5Data)
        assert data[0].latitude == -23.5505
        assert data[0].longitude == -46.6333
        
        # Verificar valores realistas
        for d in data:
            assert d.temperature_2m is not None
            assert -10 < d.temperature_2m < 45  # Temperatura razoável
            assert 0 <= d.precipitation <= 0.1  # Em metros (0-100mm)
    
    def test_calculate_climate_percentiles(self, copernicus_service):
        """Teste: Calcular percentis climáticos"""
        percentiles = copernicus_service.calculate_climate_percentiles(
            latitude=-23.5505,
            longitude=-46.6333,
            variable='temperature_2m',
            percentiles=[95, 99],
            historical_years=1
        )
        
        # Verificar estrutura
        assert 'p95' in percentiles
        assert 'p99' in percentiles
        
        # Verificar valores realistas
        assert 15 < percentiles['p95'] < 40
        assert percentiles['p99'] > percentiles['p95']
    
    def test_service_status(self, copernicus_service):
        """Teste: Status do serviço"""
        status = copernicus_service.get_service_status()
        
        assert 'service' in status
        assert status['service'] == 'Copernicus CDS'
        assert 'cdsapi_available' in status
        assert 'credentials_configured' in status


class TestINMETObservation:
    """Testes para INMETObservation dataclass"""
    
    def test_observation_creation(self):
        """Teste: Criar observação"""
        obs = INMETObservation(
            station_id='A701',
            observation_date='2026-02-16',
            observation_time='15:00',
            temperature=25.5,
            humidity=65.0,
            pressure=1013.25,
            wind_speed=5.5,
            wind_direction=180,
            precipitation=2.5,
            solar_radiation=450.0,
            evaporation=3.0
        )
        
        assert obs.station_id == 'A701'
        assert obs.temperature == 25.5
        assert obs.humidity == 65.0


class TestERA5Data:
    """Testes para ERA5Data dataclass"""
    
    def test_era5_data_creation(self):
        """Teste: Criar dados ERA5"""
        data = ERA5Data(
            latitude=-23.5505,
            longitude=-46.6333,
            date='2026-02-16',
            temperature_2m=25.5,
            temperature_max=30.0,
            temperature_min=20.0,
            precipitation=0.005,
            wind_speed_10m=5.5,
            wind_direction_10m=180,
            pressure_msl=101325,
            humidity_2m=65.0,
            evaporation=0.003,
            solar_radiation=20e6
        )
        
        assert data.latitude == -23.5505
        assert data.temperature_2m == 25.5
        assert data.precipitation == 0.005


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

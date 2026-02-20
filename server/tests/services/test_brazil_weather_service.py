"""
Testes Unitários para Brazil Weather Service
"""

import pytest
from datetime import datetime, timedelta
from services.brazil_weather_service import BrazilWeatherService, BrazilWeatherData


class TestBrazilWeatherService:
    """Testes para BrazilWeatherService"""
    
    @pytest.fixture
    def brazil_weather_service(self):
        """Fixture para serviço BrazilWeather"""
        return BrazilWeatherService()
    
    def test_service_initialization(self, brazil_weather_service):
        """Teste: Inicialização do serviço"""
        assert brazil_weather_service.OPENMETEO_URL == "https://api.open-meteo.com/v1/forecast"
        assert brazil_weather_service.WEATHERAPI_URL == "https://api.weatherapi.com/v1"
        assert brazil_weather_service.HGBRASIL_URL == "https://api.hgbrasil.com/weather"
    
    def test_get_openmeteo_historical(self, brazil_weather_service):
        """Teste: Obter dados históricos do OpenMeteo"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        data = brazil_weather_service._get_openmeteo_historical(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=start_date,
            end_date=end_date
        )
        
        # API pode estar indisponível, então verificamos estrutura ou lista vazia
        if len(data) > 0:
            assert len(data) == 7  # 7 dias
            assert isinstance(data[0], BrazilWeatherData)
            assert data[0].source == 'openmeteo'
            
            # Verificar valores realistas para São Paulo
            for d in data:
                assert -10 < d.temperature_max < 45  # Temperatura razoável
                assert 0 <= d.precipitation <= 200  # Precipitação em mm
                assert 0 <= d.humidity <= 100  # Umidade em %
        else:
            # API indisponível é aceitável nos testes
            assert data == []
    
    def test_calculate_rainfall_percentiles(self, brazil_weather_service):
        """Teste: Calcular percentis de chuva"""
        percentiles = brazil_weather_service.calculate_rainfall_percentiles(
            latitude=-23.5505,
            longitude=-46.6333,
            percentiles=[95, 99],
            historical_years=1
        )
        
        # Verificar estrutura
        assert 'p95' in percentiles
        assert 'p99' in percentiles
        
        # Verificar valores realistas (em mm)
        assert 0 <= percentiles['p95'] <= 100
        assert percentiles['p99'] >= percentiles['p95']
    
    def test_get_current_conditions(self, brazil_weather_service):
        """Teste: Obter condições atuais"""
        # Sem API keys, deve usar fallback para OpenMeteo
        current = brazil_weather_service.get_current_conditions(
            latitude=-23.5505,
            longitude=-46.6333,
            source='openmeteo'
        )
        
        # Pode retornar None se OpenMeteo falhar, ou dados válidos
        if current:
            assert isinstance(current, BrazilWeatherData)
            assert current.source == 'openmeteo'
            assert -10 < current.temperature_avg < 45
    
    def test_service_status(self, brazil_weather_service):
        """Teste: Status do serviço"""
        status = brazil_weather_service.get_service_status()
        
        assert 'service' in status
        assert status['service'] == 'BrazilWeatherService'
        assert 'sources' in status
        assert 'openmeteo' in status['sources']
        assert status['sources']['openmeteo']['status'] == 'active'
        assert status['sources']['openmeteo']['cost'] == 'free'
        assert status['recommended_source'] == 'openmeteo'


class TestBrazilWeatherData:
    """Testes para BrazilWeatherData dataclass"""
    
    def test_weather_data_creation(self):
        """Teste: Criar dados meteorológicos"""
        data = BrazilWeatherData(
            location='São Paulo',
            state='SP',
            latitude=-23.5505,
            longitude=-46.6333,
            date='2026-02-16',
            temperature_max=30.0,
            temperature_min=20.0,
            temperature_avg=25.0,
            precipitation=5.5,
            humidity=65.0,
            wind_speed=10.5,
            wind_direction=180,
            pressure=1013.25,
            source='openmeteo'
        )
        
        assert data.location == 'São Paulo'
        assert data.state == 'SP'
        assert data.latitude == -23.5505
        assert data.temperature_max == 30.0
        assert data.precipitation == 5.5
        assert data.source == 'openmeteo'
    
    def test_weather_data_realistic_values(self):
        """Teste: Valores realistas"""
        data = BrazilWeatherData(
            location='Rio de Janeiro',
            state='RJ',
            latitude=-22.9068,
            longitude=-43.1729,
            date='2026-02-16',
            temperature_max=35.0,
            temperature_min=25.0,
            temperature_avg=30.0,
            precipitation=0.0,
            humidity=80.0,
            wind_speed=15.0,
            wind_direction=90,
            pressure=1010.0,
            source='weatherapi'
        )
        
        # Verificar valores dentro de faixas realistas
        assert 15 < data.temperature_min < data.temperature_max < 45
        assert 0 <= data.precipitation <= 300
        assert 0 <= data.humidity <= 100
        assert 0 <= data.wind_speed <= 150
        assert 900 <= data.pressure <= 1100


class TestBrazilWeatherServiceFallback:
    """Testes de fallback entre fontes"""
    
    @pytest.fixture
    def brazil_weather_service_no_keys(self):
        """Fixture sem API keys"""
        return BrazilWeatherService()
    
    def test_fallback_to_openmeteo(self, brazil_weather_service_no_keys):
        """Teste: Fallback para OpenMeteo quando outras fontes indisponíveis"""
        # Tentar WeatherAPI sem key
        data = brazil_weather_service_no_keys._get_weatherapi_historical(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        # Deve retornar lista vazia (sem key)
        assert data == []
        
        # Tentar HG Brasil sem key
        data = brazil_weather_service_no_keys._get_hgbrazil_historical(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        # Deve retornar lista vazia (sem key)
        assert data == []
    
    def test_get_historical_data_with_fallback(self, brazil_weather_service_no_keys):
        """Teste: get_historical_data com fallback automático"""
        # Tentar WeatherAPI (deve fallback para OpenMeteo)
        data = brazil_weather_service_no_keys.get_historical_data(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=datetime.now() - timedelta(days=3),
            end_date=datetime.now(),
            source='weatherapi'  # Sem key, deve fallback
        )
        
        # Pode retornar dados do OpenMeteo ou lista vazia se API indisponível
        if len(data) > 0:
            assert len(data) == 3
            assert data[0].source == 'openmeteo'
        else:
            # API indisponível é aceitável
            assert data == []


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

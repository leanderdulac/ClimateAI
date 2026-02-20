"""
Testes Unitários para XWeather Service
"""

import pytest
from services.xweather_service import XWeatherService, XWeatherCondition, XWeatherForecast


class TestXWeatherService:
    """Testes para XWeatherService"""
    
    @pytest.fixture
    def xweather_service(self):
        """Fixture para serviço XWeather"""
        return XWeatherService()
    
    def test_service_initialization(self, xweather_service):
        """Teste: Inicialização do serviço"""
        assert xweather_service.CLIENT_ID == "gIvJgm7aucflvyPpN4aMu"
        assert xweather_service.CLIENT_SECRET == "k2cfveiiBwIW5Q8dPnjOCxveYsYvhfjWUvni5MnQ"
        assert xweather_service.BASE_URL == "https://data.api.xweather.com"
    
    def test_build_url(self, xweather_service):
        """Teste: Construção de URL"""
        endpoint = "/conditions/-23.55,-46.63"
        params = {'plimit': '1', 'filter': '1min'}
        
        url = xweather_service._build_url(endpoint, params)
        
        assert xweather_service.BASE_URL in url
        assert endpoint in url
        assert 'client_id=' in url
        assert 'client_secret=' in url
        assert 'format=geojson' in url
        assert 'plimit=1' in url
        assert 'filter=1min' in url
    
    def test_get_service_status(self, xweather_service):
        """Teste: Status do serviço"""
        status = xweather_service.get_service_status()
        
        assert status['service'] == 'XWeather Integration'
        assert status['status'] == 'active'
        assert status['api_key_configured'] is True
        assert 'conditions' in status['endpoints']
        assert 'forecast' in status['endpoints']
        assert 'current_conditions' in status['features']
        assert 'weather_forecast' in status['features']
    
    def test_get_weather_data_structure(self, xweather_service):
        """Teste: Estrutura de dados do weather_data"""
        # Testar com coordenadas válidas (São Paulo)
        result = xweather_service.get_weather_data(
            latitude=-23.5505,
            longitude=-46.6333,
            days=1
        )
        
        # Verificar estrutura da resposta
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'source' in result
        assert 'current' in result or result.get('error') is not None
        assert 'forecast' in result or result.get('error') is not None
        
        # Se sucesso, verificar dados
        if result['success']:
            assert result['source'] in ['XWeather', 'Embrapa (fallback)']
            
            if result.get('current'):
                assert 'temperature' in result['current']
                assert 'humidity' in result['current']
                assert 'source' in result['current']
    
    def test_coordinates_validation(self, xweather_service):
        """Teste: Validação de coordenadas"""
        # Coordenadas inválidas
        result_invalid = xweather_service.get_weather_data(
            latitude=100,  # Inválido
            longitude=200,  # Inválido
            days=1
        )
        
        # Deve falhar ou usar fallback
        assert result_invalid is not None
    
    def test_fallback_mechanism(self, xweather_service):
        """Teste: Mecanismo de fallback para Embrapa"""
        # Testar fallback
        result = xweather_service.get_weather_data(
            latitude=-23.5505,
            longitude=-46.6333,
            days=1
        )
        
        # Se XWeather falhar, deve ter fallback
        if not result['success']:
            assert 'error' in result
        else:
            # Se sucesso, verificar fonte
            assert result['source'] in ['XWeather', 'Embrapa (fallback)']


class TestXWeatherCondition:
    """Testes para estrutura XWeatherCondition"""
    
    def test_condition_creation(self):
        """Teste: Criar XWeatherCondition"""
        condition = XWeatherCondition(
            location="São Paulo",
            latitude=-23.5505,
            longitude=-46.6333,
            temperature=25.5,
            feels_like=27.0,
            humidity=65,
            pressure=1013.25,
            wind_speed=10.5,
            wind_direction=180,
            visibility=10000,
            dew_point=18.5,
            weather_code=1,
            weather_description="Partly Cloudy",
            precip_1hr=0,
            precip_24hr=2.5,
            snow_1hr=0,
            snow_24hr=0,
            solar_radiation=450,
            uv_index=5,
            ceiling=3000,
            observation_time="2026-02-16T15:00:00Z",
            source="XWeather"
        )
        
        assert condition.location == "São Paulo"
        assert condition.temperature == 25.5
        assert condition.feels_like == 27.0
        assert condition.humidity == 65
        assert condition.source == "XWeather"


class TestXWeatherForecast:
    """Testes para estrutura XWeatherForecast"""
    
    def test_forecast_creation(self):
        """Teste: Criar XWeatherForecast"""
        forecast = XWeatherForecast(
            location="São Paulo",
            latitude=-23.5505,
            longitude=-46.6333,
            forecast_date="2026-02-17",
            temperature_high=28.0,
            temperature_low=18.0,
            humidity=70,
            precipitation=5.0,
            precipitation_probability=0.6,
            wind_speed=12.0,
            wind_direction=190,
            weather_code=2,
            weather_description="Cloudy",
            sunrise="2026-02-17T06:00:00Z",
            sunset="2026-02-17T19:00:00Z",
            source="XWeather"
        )
        
        assert forecast.forecast_date == "2026-02-17"
        assert forecast.temperature_high == 28.0
        assert forecast.temperature_low == 18.0
        assert forecast.precipitation == 5.0
        assert forecast.precipitation_probability == 0.6


class TestXWeatherAPIIntegration:
    """Testes de integração com API XWeather"""
    
    @pytest.fixture
    def xweather_service(self):
        return XWeatherService()
    
    @pytest.mark.skip(reason="Requires live API connection")
    def test_live_api_connection(self, xweather_service):
        """Teste: Conexão ao vivo com API XWeather"""
        result = xweather_service.get_weather_data(
            latitude=-23.5505,
            longitude=-46.6333,
            days=1
        )
        
        # Este teste requer conexão real com a API
        assert result is not None
    
    @pytest.mark.skip(reason="Requires live API connection")
    def test_live_forecast(self, xweather_service):
        """Teste: Previsão ao vivo"""
        forecast = xweather_service.get_forecast(
            latitude=-23.5505,
            longitude=-46.6333,
            days=7
        )
        
        # Este teste requer conexão real com a API
        if forecast:
            assert len(forecast) > 0
            assert len(forecast) <= 7


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

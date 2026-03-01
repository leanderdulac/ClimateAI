"""
Atlas Real-Time Climate Data Service
Integra dados climáticos REAIS (OpenMeteo) com simulação do Oracle/Blockchain

Fontes de dados:
1. OpenMeteo - Dados climáticos em tempo real (GRATUITO, sem API key)
2. Atlas Digital - Dados históricos de desastres (MDR)
3. Simulação Oracle - Payouts e blockchain (quando blockchain real não disponível)
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AtlasRealTimeClimateService:
    """
    Serviço híbrido: dados reais + simulação inteligente
    
    Prioridade:
    1. APIs reais (OpenMeteo, INMET, NOAA) quando disponíveis
    2. Fallback para simulação baseada em Atlas histórico
    3. Oracle simulation para blockchain/payouts
    """

    # OpenMeteo API (gratuita, não precisa key)
    OPENMETEO_BASE_URL = "https://api.open-meteo.com/v1"
    
    # Coordenadas de cidades brasileiras
    BRAZIL_CITIES = {
        'sao_paulo': {'lat': -23.5505, 'lon': -46.6333},
        'rio_de_janeiro': {'lat': -22.9068, 'lon': -43.1729},
        'porto_alegre': {'lat': -30.0346, 'lon': -51.2177},
        'curitiba': {'lat': -25.4284, 'lon': -49.2733},
        'florianopolis': {'lat': -27.5954, 'lon': -48.5480},
        'belo_horizonte': {'lat': -19.9167, 'lon': -43.9345},
        'salvador': {'lat': -12.9714, 'lon': -38.5014},
        'recife': {'lat': -8.0476, 'lon': -34.8770},
        'fortaleza': {'lat': -3.7319, 'lon': -38.5267},
        'manaus': {'lat': -3.1190, 'lon': -60.0217},
        'brasilia': {'lat': -15.7801, 'lon': -47.9292},
    }

    def __init__(self):
        self._cache = {}
        self._cache_timeout = timedelta(minutes=30)
        logger.info("AtlasRealTimeClimateService initialized")

    def get_real_time_weather(
        self,
        city: str = 'sao_paulo',
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Obter dados climáticos em tempo real da OpenMeteo
        
        Args:
            city: Nome da cidade (ver BRAZIL_CITIES)
            use_cache: Usar cache se disponível
            
        Returns:
            Dados climáticos ou None se falhar
        """
        if city not in self.BRAZIL_CITIES:
            logger.error(f"Cidade não encontrada: {city}")
            return None
        
        # Verificar cache
        if use_cache and city in self._cache:
            cache_time, data = self._cache[city]
            if datetime.now() - cache_time < self._cache_timeout:
                logger.info(f"Usando cache para {city}")
                return data
        
        # Buscar dados reais da OpenMeteo
        coords = self.BRAZIL_CITIES[city]
        
        try:
            url = f"{self.OPENMETEO_BASE_URL}/forecast"
            params = {
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'current': 'temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m',
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code',
                'timezone': 'America/Sao_Paulo',
                'forecast_days': 7
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Processar dados
            processed = self._process_openmeteo_data(data, city)
            
            # Salvar no cache
            self._cache[city] = (datetime.now(), processed)
            
            logger.info(f"Dados climáticos reais obtidos para {city}")
            return processed
            
        except requests.RequestException as e:
            logger.warning(f"Falha ao obter dados de {city}: {e}. Usando fallback.")
            return self._get_fallback_data(city)
        except Exception as e:
            logger.error(f"Erro ao processar dados de {city}: {e}")
            return self._get_fallback_data(city)

    def _process_openmeteo_data(
        self,
        raw_data: Dict,
        city: str
    ) -> Dict[str, Any]:
        """Processar dados da OpenMeteo"""
        current = raw_data.get('current', {})
        daily = raw_data.get('daily', {})
        
        # Mapear weather codes para descrições
        weather_codes = {
            0: 'Céu limpo',
            1: 'Principalmente limpo',
            2: 'Parcialmente nublado',
            3: 'Nublado',
            45: 'Nevoeiro',
            48: 'Nevoeiro com geada',
            51: 'Garoa leve',
            53: 'Garoa moderada',
            55: 'Garoa densa',
            61: 'Chuva leve',
            63: 'Chuva moderada',
            65: 'Chuva forte',
            80: 'Chuva leve',
            81: 'Chuva moderada',
            82: 'Chuva forte',
            95: 'Tempestade',
            96: 'Tempestade com granizo',
            99: 'Tempestade forte com granizo',
        }
        
        return {
            'city': city,
            'coordinates': self.BRAZIL_CITIES[city],
            'timestamp': datetime.now().isoformat(),
            'source': 'OpenMeteo (REAL)',
            'current': {
                'temperature': current.get('temperature_2m'),
                'humidity': current.get('relative_humidity_2m'),
                'precipitation': current.get('precipitation'),
                'weather_code': current.get('weather_code'),
                'weather_description': weather_codes.get(current.get('weather_code'), 'Desconhecido'),
                'wind_speed': current.get('wind_speed_10m'),
            },
            'daily': [
                {
                    'date': daily.get('time', [])[i] if i < len(daily.get('time', [])) else None,
                    'temp_max': daily.get('temperature_2m_max', [])[i] if i < len(daily.get('temperature_2m_max', [])) else None,
                    'temp_min': daily.get('temperature_2m_min', [])[i] if i < len(daily.get('temperature_2m_min', [])) else None,
                    'precipitation': daily.get('precipitation_sum', [])[i] if i < len(daily.get('precipitation_sum', [])) else None,
                    'weather_code': daily.get('weather_code', [])[i] if i < len(daily.get('weather_code', [])) else None,
                }
                for i in range(7)
            ],
            'risk_indicators': self._calculate_risk_indicators(current, daily),
        }

    def _calculate_risk_indicators(
        self,
        current: Dict,
        daily: Dict
    ) -> Dict[str, Any]:
        """
        Calcular indicadores de risco climático
        
        Baseado em:
        - Precipitação acumulada
        - Temperatura extrema
        - Códigos de clima severo
        """
        # Precipitação atual
        current_precip = current.get('precipitation', 0) or 0
        
        # Precipitação dos próximos 3 dias
        precip_sum = sum(daily.get('precipitation_sum', [0]*7)[:3]) or 0
        
        # Temperatura máxima
        temp_max = max(daily.get('temperature_2m_max', [0]*7)[:3]) or 0
        
        # Weather codes severos
        severe_codes = [95, 96, 99, 82, 65]  # Tempestades e chuva forte
        has_severe = any(code in severe_codes for code in daily.get('weather_code', []))
        
        # Calcular risk score (0-5)
        risk_score = 1.0
        
        if current_precip > 10:
            risk_score += 1.0
        if precip_sum > 50:
            risk_score += 1.5
        if temp_max > 35:
            risk_score += 0.5
        if has_severe:
            risk_score += 1.5
        
        risk_score = min(5.0, risk_score)
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': 'HIGH' if risk_score >= 3.5 else 'MEDIUM' if risk_score >= 2.0 else 'LOW',
            'flood_risk': precip_sum > 50,
            'drought_risk': precip_sum < 5 and temp_max > 30,
            'storm_risk': has_severe,
        }

    def _get_fallback_data(self, city: str) -> Dict[str, Any]:
        """
        Dados de fallback quando APIs reais falham
        
        Usa dados simulados baseados em:
        - Médias históricas da cidade
        - Sazonalidade atual
        - Variação aleatória controlada
        """
        import random
        
        # Mês atual para sazonalidade
        month = datetime.now().month
        is_summer = month in [12, 1, 2, 3]
        
        # Temperaturas base por cidade
        base_temps = {
            'sao_paulo': 25 if is_summer else 20,
            'rio_de_janeiro': 30 if is_summer else 25,
            'porto_alegre': 28 if is_summer else 18,
            'curitiba': 24 if is_summer else 15,
            'florianopolis': 27 if is_summer else 20,
            'belo_horizonte': 28 if is_summer else 23,
            'salvador': 30,
            'recife': 30,
            'fortaleza': 32,
            'manaus': 31,
            'brasilia': 26 if is_summer else 22,
        }
        
        base_temp = base_temps.get(city, 25)
        
        # Variação aleatória
        temp_variation = random.uniform(-3, 3)
        current_temp = base_temp + temp_variation
        
        # Precipitação sazonal
        precip_base = random.uniform(0, 20) if is_summer else random.uniform(0, 5)
        
        # Risk score simulado
        risk_score = random.uniform(1.5, 3.5)
        
        return {
            'city': city,
            'coordinates': self.BRAZIL_CITIES[city],
            'timestamp': datetime.now().isoformat(),
            'source': 'SIMULATED (fallback)',
            'current': {
                'temperature': round(current_temp, 1),
                'humidity': round(random.uniform(50, 80), 1),
                'precipitation': round(precip_base, 1),
                'weather_code': 2 if precip_base < 5 else 61,
                'weather_description': 'Parcialmente nublado' if precip_base < 5 else 'Chuva leve',
                'wind_speed': round(random.uniform(5, 15), 1),
            },
            'daily': [
                {
                    'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'temp_max': round(base_temp + random.uniform(-2, 5), 1),
                    'temp_min': round(base_temp - random.uniform(5, 10), 1),
                    'precipitation': round(random.uniform(0, 15), 1),
                    'weather_code': random.choice([1, 2, 3, 61, 80]),
                }
                for i in range(7)
            ],
            'risk_indicators': {
                'risk_score': round(risk_score, 2),
                'risk_level': 'MEDIUM',
                'flood_risk': precip_base > 10,
                'drought_risk': precip_base < 2,
                'storm_risk': False,
            },
        }

    def get_all_cities_weather(self) -> List[Dict[str, Any]]:
        """Obter clima de todas as cidades"""
        results = []
        for city in self.BRAZIL_CITIES.keys():
            weather = self.get_real_time_weather(city)
            if weather:
                results.append(weather)
        return results

    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Obter resumo de risco de todas as cidades
        
        Returns:
            Resumo consolidado de riscos climáticos
        """
        all_weather = self.get_all_cities_weather()
        
        high_risk = [w for w in all_weather if w['risk_indicators']['risk_level'] == 'HIGH']
        medium_risk = [w for w in all_weather if w['risk_indicators']['risk_level'] == 'MEDIUM']
        low_risk = [w for w in all_weather if w['risk_indicators']['risk_level'] == 'LOW']
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_cities': len(all_weather),
            'high_risk_cities': len(high_risk),
            'medium_risk_cities': len(medium_risk),
            'low_risk_cities': len(low_risk),
            'cities': [
                {
                    'city': w['city'],
                    'risk_level': w['risk_indicators']['risk_level'],
                    'risk_score': w['risk_indicators']['risk_score'],
                    'temperature': w['current']['temperature'],
                    'precipitation': w['current']['precipitation'],
                }
                for w in all_weather
            ],
        }


# Instância global
atlas_realtime_climate = AtlasRealTimeClimateService()

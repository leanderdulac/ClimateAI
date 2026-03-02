"""
Atlas Real-Time Climate Data API Router
Endpoints para dados climáticos REAIS (OpenMeteo) + simulação
"""

import logging
from typing import Dict, Any, List

from fastapi import APIRouter, Query

from services.atlas_realtime_climate_service import atlas_realtime_climate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/atlas-realtime", tags=["atlas-realtime"])


@router.get("/weather/{city}")
async def get_city_weather(
    city: str = "sao_paulo",
    use_cache: bool = True
):
    """
    Obter dados climáticos em tempo real de uma cidade
    
    **Fontes:**
    - OpenMeteo (dados REAIS, gratuitos)
    - Fallback: simulação baseada em médias históricas
    
    **Cidades disponíveis:**
    - sao_paulo, rio_de_janeiro, porto_alegre, curitiba, florianopolis
    - belo_horizonte, salvador, recife, fortaleza, manaus, brasilia
    """
    weather = atlas_realtime_climate.get_real_time_weather(city, use_cache)
    
    return {
        'status': 'success',
        'data': weather,
        'source': weather.get('source', 'UNKNOWN') if weather else 'NONE',
    }


@router.get("/all-cities")
async def get_all_cities_weather():
    """
    Obter clima de todas as cidades monitoradas
    
    **Retorna:**
    - Dados atuais de 11 capitais brasileiras
    - Indicadores de risco climático
    - Previsão para 7 dias
    """
    cities = atlas_realtime_climate.get_all_cities_weather()
    
    return {
        'status': 'success',
        'total_cities': len(cities),
        'data': cities,
    }


@router.get("/risk-summary")
async def get_risk_summary():
    """
    Resumo de riscos climáticos do Brasil
    
    **Retorna:**
    - Total de cidades em risco ALTO/MÉDIO/BAIXO
    - Lista de cidades com respectivos riscos
    - Dados em tempo real da OpenMeteo
    """
    summary = atlas_realtime_climate.get_risk_summary()
    
    return {
        'status': 'success',
        'data': summary,
    }


@router.get("/compare/{city1}/{city2}")
async def compare_cities(
    city1: str = "sao_paulo",
    city2: str = "rio_de_janeiro"
):
    """
    Comparar clima entre duas cidades
    
    **Útil para:**
    - Análise de risco comparada
    - Decisões de investimento
    - Estudos climáticos
    """
    weather1 = atlas_realtime_climate.get_real_time_weather(city1)
    weather2 = atlas_realtime_climate.get_real_time_weather(city2)
    
    return {
        'status': 'success',
        'comparison': {
            city1: weather1,
            city2: weather2,
        },
        'risk_comparison': {
            city1: weather1['risk_indicators'] if weather1 else None,
            city2: weather2['risk_indicators'] if weather2 else None,
        },
    }


@router.get("/health")
async def health_check():
    """Health check do serviço"""
    return {
        'status': 'healthy',
        'service': 'atlas-realtime-climate',
        'source': 'OpenMeteo (FREE)',
        'cities_available': len(atlas_realtime_climate.BRAZIL_CITIES),
    }

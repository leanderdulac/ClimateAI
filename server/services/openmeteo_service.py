"""
Serviço para integração com a API OpenMeteo.
Fornece métodos para obter dados climáticos históricos e previsões.
"""


import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import openmeteo_requests
import pandas as pd
import requests_cache
import asyncio
import requests
from fastapi import HTTPException
from retry_requests import retry
from lib.redis_cache import external_api_cache, get_cache
from lib.resilient_http_client import with_resilience
from utils import geohash_util

from models.schemas import ClimaData

logger = logging.getLogger(__name__)


class OpenMeteoService:
    def __init__(self):
        """
        Inicializa o serviço OpenMeteo com cache e retry.
        Cache expira após 1 hora e retry tenta 5 vezes com backoff exponencial.
        """
        try:
            CACHE_EXPIRATION_SECONDS = 3600  # 1 hora para evitar crescimento infinito

            self.cache_session = requests_cache.CachedSession(
                ".cache",
                expire_after=CACHE_EXPIRATION_SECONDS,
                backend="sqlite",
                allowable_methods=("GET", "POST"),
                stale_if_error=True,
            )
            # Disable SSL verify if needed (OpenMeteo SSLError workaround)
            self.cache_session.verify = False 

            retry_session = retry(self.cache_session, retries=5, backoff_factor=0.2)
            
            # Monkeypatch session.request to include a default timeout if not provided
            original_request = retry_session.request
            def request_with_timeout(*args, **kwargs):
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = 10
                return original_request(*args, **kwargs)
            retry_session.request = request_with_timeout
            
            self.openmeteo = openmeteo_requests.Client(session=retry_session)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao inicializar o serviço OpenMeteo: {str(e)}",
            )

    async def obter_historico(
        self,
        latitude: float,
        longitude: float,
        data_inicio: datetime,
        data_fim: datetime,
        variavel: Optional[str] = None,
    ) -> List[ClimaData]:
        """
        Obter dados climáticos históricos com cache geofísico (geohash).
        """
        gh = geohash_util.encode(latitude, longitude, precision=6)
        return await self._obter_historico_base(gh, latitude, longitude, data_inicio, data_fim, variavel)

    @external_api_cache("openmeteo_history_gh", ttl=3600*24)
    @with_resilience("openmeteo", max_retries=5, timeout=60.0)
    async def _obter_historico_base(
        self,
        gh: str,
        latitude: float,
        longitude: float,
        data_inicio: datetime,
        data_fim: datetime,
        variavel: Optional[str] = None,
    ) -> List[ClimaData]:
        """
        Obter dados climáticos históricos da API OpenMeteo.

        Args:
            latitude: Latitude do local (-90 a 90)
            longitude: Longitude do local (-180 a 180)
            data_inicio: Data inicial para busca de dados históricos
            data_fim: Data final para busca de dados históricos
            variavel: Variável específica para filtrar (opcional)

        Returns:
            Lista de objetos ClimaData com os dados históricos agregados por dia

        Raises:
            HTTPException: Se houver erro na requisição ou processamento

        Note:
            - Dados são obtidos em resolução horária e agregados por dia
            - Temperatura e umidade são médias diárias
            - Precipitação é soma diária
            - Pressão e vento são médias diárias
        """
        try:
            # Validar parâmetros
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude deve estar entre -90 e 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude deve estar entre -180 e 180")
            # Validação básica
            if data_fim < data_inicio:
                raise ValueError("Data final deve ser maior que data inicial")
                
            # Se o período for maior que 365 dias, fazer em chunks recursivamente ou iterativamente
            if (data_fim - data_inicio).days > 365:
                logger.info(f"Período solicitado > 365 dias. Quebrando em chunks anuais...")
                all_data = []
                current_start = data_inicio
                
                while current_start < data_fim:
                    current_end = min(current_start + timedelta(days=365), data_fim)
                    try:
                        chunk_data = await self.obter_historico(latitude, longitude, current_start, current_end, variavel)
                        all_data.extend(chunk_data)
                    except HTTPException as e:
                        if e.status_code == 404:
                            logger.warning(f"Sem dados para o chunk {current_start} a {current_end}")
                        else:
                            raise e
                    except Exception as e:
                        logger.error(f"Erro ao buscar chunk {current_start}: {e}")
                        
                    current_start = current_end + timedelta(days=1)
                    
                    # Defensivo: Delay para evitar rate limit de minutely requests
                    if current_start < data_fim:
                        await asyncio.sleep(1.0)
                    
                if not all_data:
                    raise HTTPException(status_code=404, detail="Nenhum dado encontrado em nenhum dos períodos.")
                    
                return all_data
            # Define os parâmetros da API
            # Define os parâmetros da API (Baseado no snippet do usuário - Archive)
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": data_inicio.strftime("%Y-%m-%d"),
                "end_date": data_fim.strftime("%Y-%m-%d"),
                "daily": [
                    "temperature_2m_mean",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "apparent_temperature_mean",
                    "apparent_temperature_max",
                    "apparent_temperature_min",
                    "precipitation_sum",
                    "snowfall_sum",
                    "rain_sum",
                    "precipitation_hours",
                    "wind_speed_10m_max",
                    "wind_gusts_10m_max",
                    "wind_direction_10m_dominant",
                    "shortwave_radiation_sum",
                    "et0_fao_evapotranspiration",
                ],
                "timezone": "America/Sao_Paulo",
            }

            # Se a data de fim for recente (últimos 7 dias), usar API de Forecast com past_days
            # caso contrário, usar Archive API.
            # Convertendo now().date() para datetime para comparação segura
            hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            is_recent = (hoje - data_fim).days <= 7
            
            if is_recent:
                url = "https://api.open-meteo.com/v1/forecast"
                # past_days max is 92 for forecast API. If we need more, we MUST use archive.
                # However, is_recent is only true if end_date within last 7 days.
                # But start date could be long ago.
                # Fix: logical check. Use forecast ONLY if start_date is also recent (e.g. within 90 days)
                
                days_since_start = (hoje - data_inicio).days
                if days_since_start > 90:
                    # Too far back for forecast API past_days
                    url = "https://archive-api.open-meteo.com/v1/archive"
                else:
                    # Recent enough for forecast API
                    url = "https://api.open-meteo.com/v1/forecast"
                    params["past_days"] = days_since_start
                    params["forecast_days"] = 1
                    if "start_date" in params: del params["start_date"]
                    if "end_date" in params: del params["end_date"]
            else:
                url = "https://archive-api.open-meteo.com/v1/archive"

            # Fazer a requisição à API
            responses = self.openmeteo.weather_api(url, params)
            
            # Algumas versões retornam uma lista, outras o objeto direto se for apenas uma localização
            if isinstance(responses, list):
                response = responses[0]
            else:
                response = responses
            
            daily = response.Daily()
            
            # Criar DataFrame com os dados diários
            daily_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s"),
                    end=pd.to_datetime(daily.TimeEnd(), unit="s"),
                    freq=pd.Timedelta(seconds=daily.Interval()),
                    inclusive="left",
                )
            }
            
            # Mapear variáveis conforme ordem params['daily']
            daily_data["temperature_mean"] = daily.Variables(0).ValuesAsNumpy()
            daily_data["temperature_max"] = daily.Variables(1).ValuesAsNumpy()
            daily_data["temperature_min"] = daily.Variables(2).ValuesAsNumpy()
            # apparent_mean (3), max (4), min (5)
            # precipitation_sum (6)
            daily_data["precipitation"] = daily.Variables(6).ValuesAsNumpy()
            # snowfall_sum (7)
            # rain_sum (8)
            # precipitation_hours (9)
            # wind_speed_10m_max (10)
            daily_data["wind_speed"] = daily.Variables(10).ValuesAsNumpy()
            # wind_gusts_10m_max (11)
            # wind_direction_10m_dominant (12)
            daily_data["wind_direction"] = daily.Variables(12).ValuesAsNumpy()
            
            # Converter para DataFrame
            df = pd.DataFrame(data=daily_data)
            
            # Garantir que a coluna 'date' é datetime sem timezone para comparação
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.normalize()
            
            # Preparar referências de data normalize para comparação (sem hora)
            data_inicio_ref = pd.to_datetime(data_inicio).normalize()
            data_fim_ref = pd.to_datetime(data_fim).normalize()
            
            logger.info(f"OpenMeteo: {len(df)} registros brutos. Filtrando de {data_inicio_ref} a {data_fim_ref}")
            # Log das datas disponíveis no DF para debug
            if not df.empty:
                 logger.debug(f"Datas disponíveis: {df['date'].min()} a {df['date'].max()}")

            df = df[(df['date'] >= data_inicio_ref) & (df['date'] <= data_fim_ref)]
            
            logger.info(f"Processando {len(df)} registros filtrados.")

            # Converter para o formato ClimaData
            dados = []
            for _, row in df.iterrows():
                try:
                    dado = ClimaData(
                        latitude=latitude,
                        longitude=longitude,
                        data=row["date"].to_pydatetime(),
                        temperatura=float(row["temperature_max"]), # Usar MAX para ser mais "preciso" conforme feedback
                        precipitacao=float(row["precipitation"]),
                        umidade=None, # Não disponível no daily snippet archive
                        vento_velocidade=float(row["wind_speed"]),
                        vento_direcao=float(row["wind_direction"]),
                        pressao=None, # Não disponível no daily snippet archive
                        indice_spi=None,  # SPI requer cálculo separado
                        fonte=f"OpenMeteo ({'Forecast' if is_recent else 'Archive'})",
                    )
                    dados.append(dado)
                except Exception as e:
                    logger.warning(f"Erro ao processar linha: {e}")
                    continue

            if not dados:
                logger.warning(f"Nenhum dado encontrado após filtro: {data_inicio_ref} a {data_fim_ref}")
                raise HTTPException(
                    status_code=404,
                    detail="Nenhum dado válido encontrado para o período",
                )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e)
            if "Minutely API request limit exceeded" in error_msg or "429" in error_msg:
                logger.warning(f"Open-Meteo Rate Limit hit: {error_msg}")
                raise HTTPException(
                    status_code=429,
                    detail="Limite de requisições do Open-Meteo atingido. Por favor, tente novamente em um minuto."
                )
            logger.error(f"Erro ao obter dados históricos: {error_msg}")
            raise HTTPException(
                status_code=500, detail=f"Erro ao obter dados históricos: {error_msg}"
            )

        return dados

    @external_api_cache("openmeteo_forecast", ttl=3600)
    @with_resilience("openmeteo", max_retries=3, timeout=30.0)
    async def obter_previsao(
        self, latitude: float, longitude: float, dias: int = 7
    ) -> List[ClimaData]:
        """
        Obter previsão do tempo da API OpenMeteo.

        Args:
            latitude: Latitude do local
            longitude: Longitude do local
            dias: Número de dias para previsão (máximo 16)

        Returns:
            Lista de objetos ClimaData com as previsões diárias

        Raises:
            HTTPException: Se houver erro na requisição ou processamento
        """
        try:
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude deve estar entre -90 e 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude deve estar entre -180 e 180")
            if not (1 <= dias <= 16):
                raise ValueError("Número de dias deve estar entre 1 e 16")

            # Define os parâmetros da API (Baseado no snippet do usuário)
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "apparent_temperature_max",
                    "rain_sum",
                    "showers_sum",
                    "snowfall_sum",
                    "precipitation_sum",
                    "precipitation_hours",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "wind_gusts_10m_max",
                    "wind_direction_10m_dominant",
                    "shortwave_radiation_sum",
                    "et0_fao_evapotranspiration",
                ],
                "hourly": [ # O usuário pediu mas nosso modelo ClimaData diário não precisa hourly na previsao
                            # Mas se o user insiste, o snippet pede hourly e daily.
                            # Vamos manter daily apenas para o return type ClimaData
                ],
                "timezone": "America/Sao_Paulo",
                "forecast_days": dias,
            }

            # Fazer a requisição à API
            responses = self.openmeteo.weather_api(
                url="https://api.open-meteo.com/v1/forecast", params=params
            )
            response = responses[0]

            # Processar os dados diários (Baseado no snippet do usuário - ordem importa)
            daily = response.Daily()
            daily_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s"),
                    periods=len(daily.Variables(0).ValuesAsNumpy()),
                    freq="D",
                )
            }

            # Mapear as variáveis conforme ordem do params['daily']
            daily_data["temperature_max"] = daily.Variables(0).ValuesAsNumpy()
            daily_data["temperature_min"] = daily.Variables(1).ValuesAsNumpy()
            daily_data["apparent_temperature_max"] = daily.Variables(2).ValuesAsNumpy()
            daily_data["rain_sum"] = daily.Variables(3).ValuesAsNumpy()
            daily_data["showers_sum"] = daily.Variables(4).ValuesAsNumpy()
            daily_data["snowfall_sum"] = daily.Variables(5).ValuesAsNumpy()
            # precipitation_sum (6)
            daily_data["precipitation"] = daily.Variables(6).ValuesAsNumpy()
            # precipitation_hours (7)
            # precipitation_probability_max (8)
            daily_data["precipitation_prob"] = daily.Variables(8).ValuesAsNumpy()
            # wind_speed_10m_max (9)
            daily_data["wind_speed"] = daily.Variables(9).ValuesAsNumpy()
            # wind_gusts_10m_max (10)
            daily_data["wind_gusts"] = daily.Variables(10).ValuesAsNumpy()
            # wind_direction_10m_dominant (11)
            daily_data["wind_direction"] = daily.Variables(11).ValuesAsNumpy()
            
            # et0_fao_evapotranspiration (13) - Opcional para futuro

            # Converter para DataFrame
            df = pd.DataFrame(data=daily_data)

            # Converter para o formato ClimaData
            dados = []
            for _, row in df.iterrows():
                dado = ClimaData(
                    latitude=latitude,
                    longitude=longitude,
                    data=row["date"].to_pydatetime(),
                    temperatura=float(row["temperature_max"]), # Usar MAX para maior precisão visual
                    precipitacao=float(row["precipitation"]),
                    probabilidade_precipitacao=float(row["precipitation_prob"]),
                    umidade=None,  # Não disponível na previsão diária configurada
                    vento_velocidade=float(row["wind_speed"]),
                    vento_rajada=float(row["wind_gusts"]),
                    vento_direcao=float(row["wind_direction"]),
                    pressao=None,
                    indice_spi=None,
                    fonte="OpenMeteo (Forecast API)",
                )
                dados.append(dado)

            return dados

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Erro ao obter previsão do tempo: {str(e)}"
            )

    async def get_forecast(
        self, latitude: float, longitude: float, days: int = 7
    ) -> List[ClimaData]:
        """
        Wrapper para obter_previsao com nome compatível com o endpoint da API

        Args:
            latitude: Latitude do local
            longitude: Longitude do local
            days: Número de dias para previsão (máximo 16)

        Returns:
            Lista de objetos ClimaData com as previsões diárias
        """
        return await self.obter_previsao(latitude, longitude, days)

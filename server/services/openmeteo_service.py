"""
Serviço para integração com a API OpenMeteo.
Fornece métodos para obter dados climáticos históricos e previsões.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import openmeteo_requests
import pandas as pd
import requests_cache
from fastapi import HTTPException
from retry_requests import retry

from models.schemas import ClimaData


class OpenMeteoService:
    def __init__(self):
        """
        Inicializa o serviço OpenMeteo com cache e retry.
        Cache expira após 1 hora e retry tenta 5 vezes com backoff exponencial.
        """
        try:
            # Cache simples por 1 hora
            self.cache_session = requests_cache.CachedSession(
                ".cache", expire_after=3600
            )
            retry_session = retry(self.cache_session, retries=5, backoff_factor=0.2)
            self.openmeteo = openmeteo_requests.Client(session=retry_session)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao inicializar o serviço OpenMeteo: {str(e)}",
            )

    def obter_historico(
        self,
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
            if data_fim < data_inicio:
                raise ValueError("Data final deve ser maior que data inicial")
            if (data_fim - data_inicio).days > 365:
                raise ValueError("Período máximo de consulta é 1 ano")
            # Define os parâmetros da API
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": data_inicio.strftime("%Y-%m-%d"),
                "end_date": data_fim.strftime("%Y-%m-%d"),
                "hourly": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "precipitation",
                    "surface_pressure",
                    "wind_speed_10m",
                    "wind_direction_10m",
                ],
                "timezone": "America/Sao_Paulo",
            }

            # Fazer a requisição à API
            url = "https://archive-api.open-meteo.com/v1/archive"
            response = self.openmeteo.weather_api(url, params)

            # Processar os dados horários (response é uma lista, pegar o primeiro elemento)
            response = response[0]
            hourly = response.Hourly()
            # Criar DataFrame com os dados horários
            try:
                hourly_data = {
                    "date": pd.date_range(
                        start=pd.to_datetime(hourly.Time(), unit="s"),
                        end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
                        freq=pd.Timedelta(seconds=hourly.Interval()),
                        inclusive="left",
                    ),
                    "temperature": hourly.Variables(0).ValuesAsNumpy(),
                    "humidity": hourly.Variables(1).ValuesAsNumpy(),
                    "precipitation": hourly.Variables(2).ValuesAsNumpy(),
                    "pressure": hourly.Variables(3).ValuesAsNumpy(),
                    "wind_speed": hourly.Variables(4).ValuesAsNumpy(),
                    "wind_direction": hourly.Variables(5).ValuesAsNumpy(),
                }
            except IndexError as e:
                raise HTTPException(
                    status_code=500,
                    detail="Erro ao processar dados da API: formato inesperado",
                )

            # Criar DataFrame
            df = pd.DataFrame(data=hourly_data)

            # Agrupar por dia e calcular médias/somas
            daily_data = (
                df.groupby(df["date"].dt.date)
                .agg(
                    {
                        "temperature": "mean",
                        "humidity": "mean",
                        "precipitation": "sum",
                        "pressure": "mean",
                        "wind_speed": "mean",
                        "wind_direction": lambda x: float(
                            pd.Series.mode(x)[0]
                        ),  # direção dominante
                    }
                )
                .reset_index()
            )

            # Ordenar por data para garantir ordem cronológica
            daily_data = daily_data.sort_values("date").reset_index(drop=True)

            # Converter para o formato ClimaData
            dados = []
            for _, row in daily_data.iterrows():
                try:
                    dado = ClimaData(
                        latitude=latitude,
                        longitude=longitude,
                        data=datetime.combine(row["date"], datetime.min.time()),
                        temperatura=float(row["temperature"]),
                        precipitacao=float(row["precipitation"]),
                        umidade=float(row["humidity"]),
                        vento_velocidade=float(row["wind_speed"]),
                        vento_direcao=float(row["wind_direction"]),
                        pressao=float(row["pressure"]),
                        indice_spi=None,  # SPI requer cálculo separado
                        fonte="OpenMeteo",
                    )
                    dados.append(dado)
                except ValueError as e:
                    continue  # Pular registros com valores inválidos
                except Exception as e:
                    raise HTTPException(
                        status_code=500, detail=f"Erro ao processar dados: {str(e)}"
                    )

            if not dados:
                raise HTTPException(
                    status_code=404,
                    detail="Nenhum dado válido encontrado para o período",
                )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Erro ao obter dados históricos: {str(e)}"
            )

        return dados

    def obter_previsao(
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

            # Define os parâmetros da API
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_mean",
                    "windspeed_10m_max",
                    "windgusts_10m_max",
                    "winddirection_10m_dominant",
                ],
                "timezone": "America/Sao_Paulo",
                "forecast_days": dias,
            }

            # Fazer a requisição à API
            responses = self.openmeteo.weather_api(
                url="https://api.open-meteo.com/v1/forecast", params=params
            )
            response = responses[0]

            # Processar os dados diários
            daily = response.Daily()
            daily_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s"),
                    periods=len(daily.Variables(0).ValuesAsNumpy()),
                    freq="D",
                )
            }

            # Mapear as variáveis
            daily_data["temperature_max"] = daily.Variables(0).ValuesAsNumpy()
            daily_data["temperature_min"] = daily.Variables(1).ValuesAsNumpy()
            daily_data["precipitation"] = daily.Variables(2).ValuesAsNumpy()
            daily_data["precipitation_prob"] = daily.Variables(3).ValuesAsNumpy()
            daily_data["wind_speed"] = daily.Variables(4).ValuesAsNumpy()
            daily_data["wind_gusts"] = daily.Variables(5).ValuesAsNumpy()
            daily_data["wind_direction"] = daily.Variables(6).ValuesAsNumpy()

            # Converter para DataFrame
            df = pd.DataFrame(data=daily_data)

            # Converter para o formato ClimaData
            dados = []
            for _, row in df.iterrows():
                dado = ClimaData(
                    latitude=latitude,
                    longitude=longitude,
                    data=row["date"].to_pydatetime(),
                    temperatura=(
                        float(row["temperature_max"]) + float(row["temperature_min"])
                    )
                    / 2,
                    precipitacao=float(row["precipitation"]),
                    probabilidade_precipitacao=float(row["precipitation_prob"]),
                    umidade=None,  # Não disponível na previsão diária
                    vento_velocidade=float(row["wind_speed"]),
                    vento_rajada=float(row["wind_gusts"]),
                    vento_direcao=float(row["wind_direction"]),
                    pressao=None,  # Não disponível na previsão diária
                    indice_spi=None,
                    fonte="OpenMeteo",
                )
                dados.append(dado)

            return dados

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Erro ao obter previsão do tempo: {str(e)}"
            )

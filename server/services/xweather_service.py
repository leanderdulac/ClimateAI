"""
Serviço para integração com a API xWeather para previsões climáticas no Brasil
URL: https://data.api.xweather.com/forecasts/brazil
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import httpx
from fastapi import HTTPException

from models.schemas import ClimaData

logger = logging.getLogger(__name__)


class XWeatherService:
    def __init__(self):
        self.client_id = "gIvJgm7aucflvyPpN4aMu"
        self.client_secret = "k2cfveiiBwIW5Q8dPnjOCxveYsYvhfjWUvni5MnQ"
        self.base_url = "https://data.api.xweather.com/forecasts"
        self.api_key = None  # Será obtido via troca de credenciais
        self._token_expires_at = None

    async def _get_access_token(self) -> str:
        """
        Obtém token de acesso usando client credentials
        """
        if (
            self.api_key
            and self._token_expires_at
            and datetime.now() < self._token_expires_at - timedelta(minutes=5)
        ):
            # Token ainda é válido
            return self.api_key

        # Endpoint para obter token usando client credentials
        token_url = "https://data.api.xweather.com/auth/token"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    token_data = response.json()
                    self.api_key = token_data.get("access_token")

                    # Define expiração do token (menos 5 min para renovação antecipada)
                    expires_in = token_data.get("expires_in", 3600)
                    self._token_expires_at = datetime.now() + timedelta(
                        seconds=expires_in - 300
                    )

                    return self.api_key
                else:
                    # Se o endpoint de token não existe ou funciona diferente,
                    # tentaremos usar os parâmetros diretamente
                    logger.warning("Falha no OAuth. Usando credenciais diretas.")
                    # Usaremos os parâmetros client_id e client_secret diretamente
                    return f"Basic {self.client_id}:{self.client_secret}"
            except Exception as e:
                logger.error(f"Erro ao obter token de acesso: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao obter acesso à API xWeather: {str(e)}",
                )

    async def get_brazil_climate_forecast(
        self, days: int = 7, location: str = "brasilia,br"
    ) -> Dict[str, Any]:
        """
        Obtém previsão climática para o Brasil via API xWeather

        Args:
            days: Número de dias para previsão (padrão 7, máx 7 conforme filtro 'day')

        Returns:
            Dados climáticos para o Brasil
        """
        # Garante que não ultrapasse o máximo permitido pela API
        days = min(days, 7)  # Limite de 7 dias com filtro 'day'

        # Obter token de acesso
        access_token = await self._get_access_token()

        # Parâmetros da requisição conforme especificado
        params = {
            "format": "json",
            "filter": "day",  # Filtro especificado
            "limit": days,  # Limite especificado
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
                if self.api_key and "Basic" not in str(access_token)
                else ""
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Remover autorização se for Basic auth
        if "Basic" in str(access_token):
            params.update(
                {"client_id": self.client_id, "client_secret": self.client_secret}
            )
            headers.pop("Authorization", None)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/{location}"
                response = await client.get(url, params=params, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    return data
                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Credenciais inválidas para a API xWeather",
                    )
                elif response.status_code == 429:
                    raise HTTPException(
                        status_code=429,
                        detail="Limite de requisições excedido para a API xWeather",
                    )
                else:
                    logger.error(
                        f"Erro xWeather: {response.status_code} - {response.text}"[:200]
                    )
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Erro na API xWeather: {response.text}",
                    )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408, detail="Timeout na requisição para a API xWeather"
            )
        except Exception as e:
            logger.error(f"Erro inesperado ao chamar API xWeather: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Erro ao obter dados da API xWeather: {str(e)}"
            )

    async def get_brazil_climate_forecast_for_location(
        self, latitude: float, longitude: float, days: int = 7
    ) -> List[ClimaData]:
        """
        Obtém previsão climática para coordenadas específicas no Brasil

        Args:
            latitude: Latitude (-90 a 90)
            longitude: Longitude (-180 a 180)
            days: Número de dias para previsão (máximo 7)

        Returns:
            Lista de dados climáticos diários
        """
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude deve estar entre -90 e 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude deve estar entre -180 e 180")

        # Primeiro obtemos a previsão para a localização específica
        location = f"{latitude},{longitude}"
        forecast_data = await self.get_brazil_climate_forecast(days, location)

        # Processar os dados para extrair informações relevantes para a localização
        # A estrutura real dependerá da resposta da API
        # mas faremos um tratamento genérico
        clima_data_list = []

        try:
            # Verificar se a resposta tem a estrutura esperada
            # A resposta da API geralmente vem em 'response' -> [0] -> 'periods'
            forecast_items = []

            if isinstance(forecast_data, dict):
                if not forecast_data.get("success", True):
                    logger.error(f"API retornou erro: {forecast_data.get('error')}")
                    return []

                response_list = forecast_data.get("response", [])
                if (
                    response_list
                    and isinstance(response_list, list)
                    and len(response_list) > 0
                ):
                    # Pegamos o primeiro item da resposta (primeira localização)
                    first_location = response_list[0]
                    if "periods" in first_location:
                        forecast_items = first_location["periods"]

            # Fallback para tentar encontrar em outros lugares
            if not forecast_items:
                forecast_items = forecast_data.get("forecasts", [])

            # Se não encontrar 'forecasts', tenta outras chaves
            if not forecast_items:
                # Verificar se é uma lista direta
                if isinstance(forecast_data, list):
                    forecast_items = forecast_data
                else:
                    # Tentar encontrar outras chaves possíveis
                    possible_keys = [
                        "data",
                        "results",
                        "items",
                        "climate_data",
                        "weather",
                    ]
                    for key in possible_keys:
                        if key in forecast_data:
                            forecast_items = forecast_data[key]
                            break

            if not forecast_items and isinstance(forecast_data, dict):
                # Se a estrutura for diferente, tentamos interpretar como um único item
                # Mas apenas se não tivermos encontrado nada antes
                pass

            for i, item in enumerate(forecast_items[:days]):
                # Extraindo campos potenciais da resposta
                date_str = self._extract_field(
                    item,
                    ["validTime", "date", "dt", "data", "timestamp"],
                    default=(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                )

                # Converter string de data para objeto datetime se necessário
                if isinstance(date_str, str):
                    try:
                        data_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        try:
                            data_obj = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except ValueError:
                            data_obj = datetime.now() + timedelta(days=i)
                else:
                    data_obj = (
                        date_str
                        if isinstance(date_str, datetime)
                        else datetime.now() + timedelta(days=i)
                    )

                # Extrair outros campos climáticos
                temperatura = self._extract_field(
                    item,
                    [
                        "avgTempC",
                        "tempC",
                        "temperature",
                        "temp",
                        "temperature_avg",
                        "avg_temp",
                    ],
                    default=None,
                )
                if not temperatura:
                    # Tentar extrair máximas e mínimas e calcular média
                    temp_max = self._extract_field(
                        item,
                        ["maxTempC", "max_temp", "temp_max", "temperature_max"],
                        default=None,
                    )
                    temp_min = self._extract_field(
                        item,
                        ["minTempC", "min_temp", "temp_min", "temperature_min"],
                        default=None,
                    )
                    if temp_max is not None and temp_min is not None:
                        temperatura = (temp_max + temp_min) / 2
                    elif temp_max:
                        temperatura = temp_max
                    elif temp_min:
                        temperatura = temp_min

                precipitacao = self._extract_field(
                    item,
                    ["precipMM", "precipitation", "rain", "precip", "mm"],
                    default=None,
                )
                umidade = self._extract_field(
                    item, ["humidity", "umidade", "humidity_avg"], default=None
                )
                vento_velocidade = self._extract_field(
                    item,
                    ["windSpeedKPH", "wind_speed", "wind", "velocity"],
                    default=None,
                )
                vento_direcao = self._extract_field(
                    item,
                    [
                        "windDirDEG",
                        "wind_dir_deg",
                        "wind_direction_deg",
                        "dir_deg",
                        "windDir",
                        "wind_dir",
                        "wind_direction",
                        "dir",
                    ],
                    default=None,
                )
                pressao = self._extract_field(
                    item,
                    ["pressureMB", "pressure", "pressao", "barometric"],
                    default=None,
                )

                # Criar objeto ClimaData
                clima_data = ClimaData(
                    latitude=latitude,
                    longitude=longitude,
                    data=data_obj,
                    temperatura=temperatura,
                    precipitacao=precipitacao,
                    umidade=umidade,
                    vento_velocidade=vento_velocidade,
                    vento_direcao=vento_direcao,
                    pressao=pressao,
                    indice_spi=None,  # SPI requer cálculo separado
                    fonte="xWeather API",
                )

                clima_data_list.append(clima_data)

        except Exception as e:
            logger.error(f"Erro ao processar dados da API xWeather: {str(e)}")
            # Se der erro no processamento, retornamos uma previsão vazia
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar dados da API xWeather: {str(e)}",
            )

        return clima_data_list

    def _extract_field(self, data: Dict, possible_keys: List[str], default=None):
        """
        Extrai um campo de dicionário tentando varias possíveis chaves
        """
        for key in possible_keys:
            if isinstance(data, dict) and key in data:
                value = data[key]
                # Verificar se é um dicionário aninhado e extrair valor útil
                if isinstance(value, dict):
                    # Tentar extrair campo 'value', 'val', 'data', ou similar
                    for subkey in ["value", "val", "data", "avg", "mean"]:
                        if subkey in value:
                            return value[subkey]
                return value
        return default


# Instância global do serviço
xweather_service = XWeatherService()

"""
Serviço de integração com a API da Embrapa
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

from services.openmeteo_service import OpenMeteoService

load_dotenv()

logger = logging.getLogger(__name__)


class EmbrapaService:
    def __init__(self):
        self.api_key = os.getenv("EMBRAPA_API_KEY")
        self.base_url = os.getenv("EMBRAPA_API_URL", "https://api.cnptia.embrapa.br")
        self.api_version = os.getenv("EMBRAPA_API_VERSION", "climapi/v1")

        # Verificar se a configuração está completa
        self.is_configured = bool(self.api_key and self.api_key != "your_api_key_here")

        if self.is_configured:
            self.session = requests.Session()
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            )
        else:
            self.session = None

    async def get_climate_data(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[Dict]:
        """
        Obtém dados climáticos históricos da API da Embrapa
        Com fallback para OpenMeteo se Embrapa não estiver disponível
        """
        if not self.is_configured:
            logger.warning("Embrapa API não configurada, usando fallback OpenMeteo")
            return await self._fallback_to_openmeteo(
                latitude, longitude, start_date, end_date
            )

        # Calcular período de 30 anos se necessário
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Se o período for muito longo, limitar a 30 anos
        if (end_dt - start_dt).days > 365 * 30:
            start_dt = end_dt - timedelta(days=365 * 30)
            start_date = start_dt.strftime("%Y-%m-%d")

        endpoint = f"{self.base_url}/{self.api_version}/clima/historico"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "data_inicio": start_date,
            "data_fim": end_date,
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Normalizar dados para o formato esperado
            if isinstance(data, dict) and "dados" in data:
                return data["dados"]
            elif isinstance(data, list):
                return data
            else:
                return []

        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Erro na API Embrapa: {str(e)}. Usando fallback OpenMeteo.")
            return await self._fallback_to_openmeteo(
                latitude, longitude, start_date, end_date
            )

    async def get_weather_forecast(
        self, latitude: float, longitude: float, days: int = 7
    ) -> Dict:
        """
        Obtém previsão do tempo da API da Embrapa
        Com fallback para OpenMeteo se Embrapa não estiver disponível
        """
        if not self.is_configured:
            logger.warning("Embrapa API não configurada, usando fallback OpenMeteo")
            return await self._fallback_forecast_openmeteo(latitude, longitude, days)

        endpoint = f"{self.base_url}/{self.api_version}/clima/previsao"
        params = {"latitude": latitude, "longitude": longitude, "dias": days}

        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Erro na API Embrapa: {str(e)}. Usando fallback OpenMeteo.")
            return await self._fallback_forecast_openmeteo(latitude, longitude, days)

    async def get_location_data(self, latitude: float, longitude: float) -> Dict:
        """
        Obtém dados da localização da API da Embrapa
        """
        endpoint = f"{self.base_url}/{self.api_version}/localizacao"
        params = {"latitude": latitude, "longitude": longitude}

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter dados da localização: {str(e)}")

    async def get_agricultural_zoning(
        self, latitude: float, longitude: float, crop: str
    ) -> Dict:
        """
        Obtém zoneamento agrícola da API da Embrapa
        """
        endpoint = f"{self.base_url}/{self.api_version}/zarc"
        params = {"latitude": latitude, "longitude": longitude, "cultura": crop}

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter zoneamento agrícola: {str(e)}")

    async def get_climate_risk_assessment(
        self, latitude: float, longitude: float
    ) -> Dict:
        """
        Obtém avaliação de risco climático da API da Embrapa
        """
        if not self.is_configured:
            raise Exception(
                "Embrapa API não configurada. Configure EMBRAPA_API_KEY no arquivo .env"
            )

        endpoint = f"{self.base_url}/{self.api_version}/clima/risco"
        params = {"latitude": latitude, "longitude": longitude}

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter avaliação de risco climático: {str(e)}")

    async def _fallback_to_openmeteo(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[Dict]:
        """
        Fallback para OpenMeteo quando Embrapa não estiver disponível
        """
        try:
            openmeteo_service = OpenMeteoService()
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            # OpenMeteo limita a 1 ano, então ajustar se necessário
            if (end_dt - start_dt).days > 365:
                start_dt = end_dt - timedelta(days=365)

            dados = openmeteo_service.obter_historico(
                latitude, longitude, start_dt, end_dt
            )

            # Converter para o formato esperado pela API
            return [
                {
                    "latitude": d.latitude,
                    "longitude": d.longitude,
                    "data": d.data.strftime("%Y-%m-%d"),
                    "temperatura": d.temperatura,
                    "precipitacao": d.precipitacao,
                    "umidade": d.umidade,
                    "vento_velocidade": d.vento_velocidade,
                    "vento_direcao": d.vento_direcao,
                    "pressao": d.pressao,
                    "fonte": "OpenMeteo (fallback)",
                }
                for d in dados
            ]
        except Exception as e:
            logger.error(f"Erro no fallback OpenMeteo: {str(e)}")
            return []

    async def _fallback_forecast_openmeteo(
        self, latitude: float, longitude: float, days: int
    ) -> Dict:
        """
        Fallback para previsão OpenMeteo quando Embrapa não estiver disponível
        """
        try:
            openmeteo_service = OpenMeteoService()
            dados = openmeteo_service.obter_previsao(
                latitude, longitude, min(days, 16)
            )  # OpenMeteo limita a 16 dias

            # Converter para formato de previsão
            previsao = {
                "latitude": latitude,
                "longitude": longitude,
                "periodo_dias": min(days, 16),
                "fonte": "OpenMeteo (fallback)",
                "previsao": [
                    {
                        "data": d.data.strftime("%Y-%m-%d"),
                        "temperatura": d.temperatura,
                        "precipitacao": d.precipitacao,
                        "umidade": d.umidade,
                        "vento_velocidade": d.vento_velocidade,
                        "vento_direcao": d.vento_direcao,
                        "pressao": d.pressao,
                    }
                    for d in dados
                ],
            }
            return previsao
        except Exception as e:
            logger.error(f"Erro no fallback de previsão OpenMeteo: {str(e)}")
            return {
                "latitude": latitude,
                "longitude": longitude,
                "periodo_dias": days,
                "fonte": "Erro - OpenMeteo indisponível",
                "previsao": [],
            }


# Instância única do serviço
embrapa_service = EmbrapaService()

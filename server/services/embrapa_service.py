"""
Serviço de integração com a API da Embrapa
"""
import os
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class EmbrapaAPIService:
    def __init__(self):
        self.api_key = os.getenv('EMBRAPA_API_KEY')
        self.base_url = os.getenv('EMBRAPA_API_URL', 'https://api.cnptia.embrapa.br/api')
        self.api_version = os.getenv('EMBRAPA_API_VERSION', 'v1')

        # Verificar se a configuração está completa
        self.is_configured = bool(self.api_key and self.api_key != 'your_api_key_here')

        if self.is_configured:
            self.session = requests.Session()
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
        else:
            self.session = None

    async def get_climate_data(self, latitude: float, longitude: float, start_date: str, end_date: str) -> List[Dict]:
        """
        Obtém dados climáticos históricos da API da Embrapa
        """
        if not self.is_configured:
            raise Exception("Embrapa API não configurada. Configure EMBRAPA_API_KEY no arquivo .env")

        # Calcular período de 30 anos se necessário
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Se o período for muito longo, limitar a 30 anos
        if (end_dt - start_dt).days > 365 * 30:
            start_dt = end_dt - timedelta(days=365 * 30)
            start_date = start_dt.strftime("%Y-%m-%d")

        endpoint = f"{self.base_url}/clima/historico"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'data_inicio': start_date,
            'data_fim': end_date
        }

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Normalizar dados para o formato esperado
            if isinstance(data, dict) and 'dados' in data:
                return data['dados']
            elif isinstance(data, list):
                return data
            else:
                return []
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter dados climáticos: {str(e)}")

    async def get_weather_forecast(self, latitude: float, longitude: float, days: int = 7) -> Dict:
        """
        Obtém previsão do tempo da API da Embrapa
        """
        if not self.is_configured:
            raise Exception("Embrapa API não configurada. Configure EMBRAPA_API_KEY no arquivo .env")

        endpoint = f"{self.base_url}/clima/previsao"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'dias': days
        }

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter previsão do tempo: {str(e)}")

    async def get_location_data(self, latitude: float, longitude: float) -> Dict:
        """
        Obtém dados da localização da API da Embrapa
        """
        endpoint = f"{self.base_url}/localizacao"
        params = {
            'latitude': latitude,
            'longitude': longitude
        }

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter dados da localização: {str(e)}")

    async def get_agricultural_zoning(self, latitude: float, longitude: float, 
                                    crop: str) -> Dict:
        """
        Obtém zoneamento agrícola da API da Embrapa
        """
        endpoint = f"{self.base_url}/zarc"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'cultura': crop
        }

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter zoneamento agrícola: {str(e)}")

    async def get_climate_risk_assessment(self, latitude: float, longitude: float) -> Dict:
        """
        Obtém avaliação de risco climático da API da Embrapa
        """
        if not self.is_configured:
            raise Exception("Embrapa API não configurada. Configure EMBRAPA_API_KEY no arquivo .env")

        endpoint = f"{self.base_url}/clima/risco"
        params = {
            'latitude': latitude,
            'longitude': longitude
        }

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter avaliação de risco climático: {str(e)}")

# Instância única do serviço
embrapa_service = EmbrapaAPIService()
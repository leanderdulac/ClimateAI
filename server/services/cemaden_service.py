import logging
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class CemadenService:
    """
    Client for CEMADEN (Centro Nacional de Monitoramento e Alertas de Desastres Naturais) API
    Base API URL: https://sws.cemaden.gov.br/PED/rest/
    Swagger UI: https://sws.cemaden.gov.br/PED/api/ui/
    """
    
    BASE_URL = "https://sws.cemaden.gov.br/PED/rest/"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the CEMADEN API client.
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.verify = False  # nosec
        # Some government APIs use self-signed certificates or have issues randomly.
        # If needed, `self.session.verify = False` could be dynamically set via env vars.
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = urljoin(self.BASE_URL, endpoint)
        
        try:
            # In case the endpoint has a leading slash, removing it ensures urljoin behaves correctly
            # depending on BASE_URL formatting
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]
                url = urljoin(self.BASE_URL, endpoint)
                
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # API frequently returns json, let's gracefully handle if it returns empty or text
            if not response.content:
                return []
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error calling CEMADEN API {endpoint}: {response.status_code} - {response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection/Timeout Error calling CEMADEN API {endpoint}: {str(e)}")
            raise
            
    def get_estacoes(self) -> List[Dict]:
        """
        Get metadata of all monitoring stations (PCDs).
        Returns a list of dictionaries with station details like location, id, state, etc.
        """
        return self._make_request("pcds-cadastro/estacoes")
        
    def get_dados_recentes(self) -> List[Dict]:
        """
        Get recent accumulated rainfall and sensor data from all stations.
        """
        return self._make_request("pcds-acum/acumulados-recentes")
        
    def get_dados_pcd(self, codestacao: str) -> List[Dict]:
        """
        Get specific recent data for a particular PCD (station).
        """
        params = {"codestacao": codestacao}
        return self._make_request("pcds/dados_pcd", params=params)

    def get_dados_historicos(self, codestacao: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Get historical data for a given station.
        Dates should follow the format expected by the API (e.g. DD/MM/YYYY HH:MM depending on parameter spec).
        Note: Based on swagger, these params exist, but the date format might require testing.
        Usually yyyy-mm-dd or similar. We pass them directly here.
        """
        params = {
            "codestacao": codestacao,
            "datainicio": start_date,
            "datafim": end_date
        }
        return self._make_request("controle-agendamento/pcds-dados-historicos", params=params)

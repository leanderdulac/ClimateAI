"""
Serviço para dados climáticos
"""
from typing import List, Optional
from datetime import datetime, timedelta
import math
import random
from models.schemas import ClimaData
from services.openmeteo_service import OpenMeteoService


class ClimaService:
    def __init__(self):
        self.openmeteo_service = OpenMeteoService()

    def obter_historico(
        self,
        latitude: float,
        longitude: float,
        data_inicio: datetime,
        data_fim: datetime,
        variavel: Optional[str] = None
    ) -> List[ClimaData]:
        """
        Obter dados climáticos históricos para uma localização específica
        """
        # Obter dados reais da API OpenMeteo
        dados = self.openmeteo_service.obter_historico(
            latitude=latitude,
            longitude=longitude,
            data_inicio=data_inicio,
            data_fim=data_fim,
            variavel=variavel
        )
        
        return dados

    def obter_clima_atual(
        self,
        latitude: float,
        longitude: float
    ) -> ClimaData:
        """
        Obter condições climáticas atuais para uma localização específica
        """
        # Usar o mesmo serviço do OpenMeteo, mas apenas para hoje
        agora = datetime.now()
        dados = self.openmeteo_service.obter_historico(
            latitude=latitude,
            longitude=longitude,
            data_inicio=agora,
            data_fim=agora + timedelta(days=1)
        )
        
        # Retornar os dados do primeiro (e único) dia
        return dados[0] if dados else None

    def _gerar_temperatura_simulada(self, latitude: float, data: datetime) -> float:
        """
        Gerar temperatura simulada considerando latitude e sazonalidade do dia do ano.
        """
        dia_do_ano = data.timetuple().tm_yday
        variacao_sazonal = 8 * math.sin((2 * math.pi * dia_do_ano) / 365)
        ajuste_latitude = max(-8.0, min(8.0, -abs(latitude) * 0.2))
        ruido = random.uniform(-2.5, 2.5)
        return 24 + variacao_sazonal + ajuste_latitude + ruido

    def _gerar_precipitacao_simulada(self, data: datetime) -> float:
        """
        Gerar precipitação simulada com base em padrões sazonais simples.
        """
        dia_do_ano = data.timetuple().tm_yday
        indice_estacao = (math.sin((2 * math.pi * (dia_do_ano - 30)) / 365) + 1) / 2
        precipitacao_base = 5 + 20 * indice_estacao
        ruido = random.uniform(-3, 3)
        return max(0.0, precipitacao_base + ruido)

    def _gerar_umidade_simulada(self, temperatura: float) -> float:
        """
        Gerar umidade relativa simulada em função da temperatura.
        """
        umidade_base = 75 - (temperatura - 25) * 1.1
        ruido = random.uniform(-5, 5)
        return max(30.0, min(100.0, umidade_base + ruido))

    def _calcular_spi(self, precipitacao: float, indice_dia: int) -> float:
        """
        Calcular um índice SPI (Standardized Precipitation Index) simplificado.
        """
        media_historica = 12.0  # média diária aproximada
        desvio_padrao = 6.0
        if desvio_padrao == 0:
            return 0.0
        spi = (precipitacao - media_historica) / desvio_padrao
        ajuste_temporal = math.sin(indice_dia / 3.0) * 0.1
        return max(-3.0, min(3.0, spi + ajuste_temporal))

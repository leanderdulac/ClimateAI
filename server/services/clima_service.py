"""
Serviço para dados climáticos
"""
from typing import List, Optional
from datetime import datetime, timedelta
from models.schemas import ClimaData, ClimaTipo
import random
import math


class ClimaService:
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
        # Simulação de dados históricos (em um sistema real, isso viria de uma API ou banco de dados)
        dados = []
        dias = (data_fim - data_inicio).days
        
        for i in range(dias):
            data_atual = data_inicio + timedelta(days=i)
            
            # Gerar dados climáticos simulados baseados na localização
            temperatura = self._gerar_temperatura_simulada(latitude, data_atual)
            precipitacao = self._gerar_precipitacao_simulada(data_atual)
            umidade = self._gerar_umidade_simulada(temperatura)
            
            dado = ClimaData(
                latitude=latitude,
                longitude=longitude,
                data=data_atual,
                temperatura=temperatura,
                precipitacao=precipitacao,
                umidade=umidade,
                vento_velocidade=random.uniform(0, 20),
                vento_direcao=random.uniform(0, 360),
                pressao=random.uniform(980, 1040),
                indice_spi=self._calcular_spi(precipitacao, i),
                fonte="simulado"
            )
            dados.append(dado)
        
        return dados

    def obter_clima_atual(
        self,
        latitude: float,
        longitude: float
    ) -> ClimaData:
        """
        Obter condições climáticas atuais para uma localização específica
        """
        agora = datetime.now()
        
        temperatura = self._gerar_temperatura_simulada(latitude, agora)
        precipitacao = self._gerar_precipitacao_simulada(agora)
        umidade = self._gerar_umidade_simulada(temperatura)
        
        return ClimaData(
            latitude=latitude,
            longitude=longitude,
            data=agora,
            temperatura=temperatura,
            precipitacao=precipitacao,
            umidade=umidade,
            vento_velocidade=random.uniform(0, 20),
            vento_direcao=random.uniform(0, 360),
            pressao=random.uniform(980, 1040),
            indice_spi=self._calcular_spi(precipitacao, 0),
            fonte="simulado"
        )

    def _gerar_temperatura_simulada(self, latitude: float, data: datetime) -> float:
        """
        Gerar temperatura simulada baseada na latitude e estação do ano
        """
        # Temperatura base variando com a latitude (mais quente perto do equador)
        temp_base = 30 - abs(latitude) * 0.3
        
        # Variação sazonal
        dia_ano = data.timetuple().tm_yday
        variacao_sazonal = 5 * math.sin(2 * math.pi * (dia_ano - 80) / 365)
        
        # Variação diária
        variacao_diaria = random.uniform(-3, 3)
        
        return round(temp_base + variacao_sazonal + variacao_diaria, 2)

    def _gerar_precipitacao_simulada(self, data: datetime) -> float:
        """
        Gerar precipitação simulada
        """
        # Probabilidade de chuva baseada no dia do ano
        dia_ano = data.timetuple().tm_yday
        probabilidade_chuva = 0.3 + 0.2 * math.sin(2 * math.pi * dia_ano / 365)
        
        if random.random() < probabilidade_chuva:
            return round(random.uniform(0.1, 50), 2)  # mm
        else:
            return 0.0

    def _gerar_umidade_simulada(self, temperatura: float) -> float:
        """
        Gerar umidade simulada baseada na temperatura
        """
        # Umidade tende a ser inversamente proporcional à temperatura
        umidade_base = 80 - temperatura * 0.5
        variacao = random.uniform(-10, 10)
        return max(0, min(100, round(umidade_base + variacao, 2)))

    def _calcular_spi(self, precipitacao: float, dia: int) -> float:
        """
        Calcular Standardized Precipitation Index (simulado)
        """
        # Simulação simplificada do SPI
        media_historica = 5.0  # média histórica de precipitação
        desvio_padrao = 8.0    # desvio padrão histórico
        
        if media_historica == 0:
            return 0
            
        # SPI simplificado
        spi = (precipitacao - media_historica) / desvio_padrao
        return round(spi, 2)
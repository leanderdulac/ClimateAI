"""
Serviço para previsões climáticas
"""
from typing import List
from datetime import datetime, timedelta
from models.schemas import PrevisaoClima, ClimaData
from services.clima_service import ClimaService
import random


class PrevisaoService:
    def __init__(self):
        self.clima_service = ClimaService()

    def obter_previsao_clima(
        self,
        latitude: float,
        longitude: float,
        dias: int
    ) -> PrevisaoClima:
        """
        Obter previsão climática para uma localização específica
        """
        data_inicio = datetime.now()
        data_fim = data_inicio + timedelta(days=dias)
        
        variaveis = []
        for i in range(dias):
            data_atual = data_inicio + timedelta(days=i)
            
            # Simular confiança decrescente com o tempo
            confianca = max(0.5, 1.0 - (i * 0.05))
            
            temperatura = self.clima_service._gerar_temperatura_simulada(latitude, data_atual)
            precipitacao = self.clima_service._gerar_precipitacao_simulada(data_atual) * confianca
            umidade = self.clima_service._gerar_umidade_simulada(temperatura) + random.uniform(-5, 5)
            
            dado = ClimaData(
                latitude=latitude,
                longitude=longitude,
                data=data_atual,
                temperatura=temperatura,
                precipitacao=precipitacao,
                umidade=umidade,
                vento_velocidade=random.uniform(0, 20) * confianca,
                vento_direcao=random.uniform(0, 360),
                pressao=random.uniform(980, 1040),
                indice_spi=self.clima_service._calcular_spi(precipitacao, i),
                fonte="previsao_simulada"
            )
            variaveis.append(dado)
        
        return PrevisaoClima(
            latitude=latitude,
            longitude=longitude,
            data_inicio=data_inicio,
            data_fim=data_fim,
            variaveis=variaveis,
            metodo="ensemble_simulado",
            confianca=0.75  # confiança média da previsão
        )

    def obter_previsao_eventos(
        self,
        latitude: float,
        longitude: float,
        dias: int
    ) -> List[str]:
        """
        Obter previsão de eventos climáticos extremos
        """
        eventos = []
        
        for i in range(dias):
            data = datetime.now() + timedelta(days=i)
            
            # Probabilidades de eventos baseadas no clima simulado
            temp = self.clima_service._gerar_temperatura_simulada(latitude, data)
            precip = self.clima_service._gerar_precipitacao_simulada(data)
            
            # Calcular probabilidades de eventos
            prob_seca = max(0, min(1, (25 - precip) * 0.02)) if temp > 25 else 0
            prob_enchente = max(0, min(1, precip * 0.01)) if precip > 20 else 0
            prob_onda_calor = max(0, min(1, (temp - 30) * 0.1)) if temp > 30 else 0
            
            # Adicionar eventos com base nas probabilidades
            if random.random() < prob_seca:
                eventos.append(f"Seca potencial em {data.strftime('%Y-%m-%d')}")
            if random.random() < prob_enchente:
                eventos.append(f"Risco de enchente em {data.strftime('%Y-%m-%d')}")
            if random.random() < prob_onda_calor:
                eventos.append(f"Onda de calor prevista em {data.strftime('%Y-%m-%d')}")
        
        return eventos
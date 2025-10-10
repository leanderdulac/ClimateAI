"""
Serviço para modelagem econômica
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from models.schemas import PrevisaoPreco
import random


class ModelagemService:
    def obter_previsao_precos(
        self,
        simbolos: List[str],
        latitude: Optional[float],
        longitude: Optional[float],
        dias: int
    ) -> List[PrevisaoPreco]:
        """
        Obter previsões de preços de commodities considerando fatores climáticos
        """
        precos = []
        
        for simbolo in simbolos:
            # Preço atual simulado (em um sistema real, isso viria de uma API financeira)
            preco_atual = self._obter_preco_atual_simulado(simbolo)
            
            # Fatores climáticos simulados baseados na localização
            fatores_climaticos = []
            if latitude and longitude:
                for i in range(min(dias, 10)):  # Limitar para os primeiros 10 dias
                    data_fator = datetime.now() + timedelta(days=i)
                    fator = {
                        "data": data_fator.isoformat(),
                        "tipo": random.choice(["temperatura", "precipitacao", "umidade"]),
                        "impacto": random.uniform(-0.1, 0.1),  # -10% a +10% de impacto
                        "descricao": f"Efeito climático simulado em {data_fator.strftime('%Y-%m-%d')}"
                    }
                    fatores_climaticos.append(fator)
            
            # Cálculo de preço previsto com base nos fatores climáticos
            impacto_total = sum(f["impacto"] for f in fatores_climaticos)
            preco_previsto = preco_atual * (1 + impacto_total)
            variacao_prevista = ((preco_previsto - preco_atual) / preco_atual) * 100
            
            descricao = self._obter_descricao_commodity(simbolo)
            
            previsao = PrevisaoPreco(
                simbolo=simbolo,
                descricao=descricao,
                data_referencia=datetime.now(),
                preco_atual=round(preco_atual, 2),
                preco_previsto=round(preco_previsto, 2),
                variacao_prevista=round(variacao_prevista, 2),
                confianca=round(random.uniform(0.6, 0.9), 2),
                fatores_climaticos=fatores_climaticos
            )
            
            precos.append(previsao)
        
        return precos

    def obter_impacto_climatico(
        self,
        simbolo: str,
        latitude: float,
        longitude: float,
        periodo: int
    ) -> List[Dict]:
        """
        Obter análise de impacto climático sobre o preço de uma commodity
        """
        impactos = []
        
        # Simular impacto climático ao longo do tempo
        for i in range(0, periodo, 7):  # Semanalmente para visualização
            data_referencia = datetime.now() + timedelta(days=i)
            
            # Simular correlação entre variáveis climáticas e variação de preço
            correlacao_temperatura = random.uniform(-0.3, 0.5)  # Mais calor pode afetar negativa/positivamente
            correlacao_precipitacao = random.uniform(-0.5, 0.3)  # Mais chuva pode afetar negativa/positivamente
            correlacao_eventos = random.uniform(0.3, 0.8)  # Eventos extremos normalmente tem impacto negativo
            
            impacto = {
                "data": data_referencia.isoformat(),
                "correlacao_temperatura": round(correlacao_temperatura, 3),
                "correlacao_precipitacao": round(correlacao_precipitacao, 3),
                "correlacao_eventos_extremos": round(correlacao_eventos, 3),
                "impacto_total": round(
                    (correlacao_temperatura * 0.3 + 
                     correlacao_precipitacao * 0.3 + 
                     correlacao_eventos * 0.4) * 100, 2
                ),  # Impacto total em %
                "descricao": f"Impacto climático simulado para {simbolo} em {data_referencia.strftime('%Y-%m-%d')}"
            }
            
            impactos.append(impacto)
        
        return impactos

    def _obter_preco_atual_simulado(self, simbolo: str) -> float:
        """
        Obter preço atual simulado para um símbolo de commodity
        """
        precos_base = {
            "SOF": 1200.0,   # Soja
            "MIL": 800.0,    # Milho
            "TRI": 1500.0,   # Trigo
            "BOI": 300.0,    # Boi gordo
            "ACU": 2.5,      # Açúcar
            "CAF": 150.0,    # Café
            "ALG": 5.0,      # Algodão
            "OIL": 800.0,    # Óleo de soja
            "MEC": 200.0,    # Milho em Chicago
            "SBC": 400.0     # Soja em Chicago
        }
        
        # Adicionar variação aleatória diária
        base = precos_base.get(simbolo.upper(), 1000.0)
        variacao = random.uniform(0.95, 1.05)  # ±5% de variação
        
        return base * variacao

    def _obter_descricao_commodity(self, simbolo: str) -> str:
        """
        Obter descrição da commodity baseada no símbolo
        """
        descricoes = {
            "SOF": "Contrato Futuro de Soja",
            "MIL": "Contrato Futuro de Milho",
            "TRI": "Contrato Futuro de Trigo",
            "BOI": "Contrato Futuro de Boi Gordo",
            "ACU": "Contrato Futuro de Açúcar",
            "CAF": "Contrato Futuro de Café",
            "ALG": "Contrato Futuro de Algodão",
            "OIL": "Contrato Futuro de Óleo de Soja",
            "MEC": "Milho CEPEA/ESALQ",
            "SBC": "Soja CBOT"
        }
        
        return descricoes.get(simbolo.upper(), f"Commodity {simbolo}")
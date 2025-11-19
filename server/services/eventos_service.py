"""
Serviço para detecção de eventos climáticos
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from models.schemas import EventoClimatico, EventoClimaticoTipo
from models.token_schemas import EventoToken
from services.tokenizacao_eventos_service import TokenizacaoEventosService


class EventosService:
    def __init__(self):
        self.token_service = TokenizacaoEventosService()

    def obter_eventos(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        tipo: Optional[EventoClimaticoTipo],
        data_inicio: Optional[datetime],
        data_fim: Optional[datetime],
        raio: float,
    ) -> List[EventoClimatico]:
        """
        Obter eventos climáticos detectados em uma área específica
        """
        # Simular eventos climáticos com base nos parâmetros
        eventos = []

        # Simular alguns eventos climáticos
        for i in range(random.randint(0, 5)):
            # Data aleatória dentro do intervalo se especificado
            if data_inicio and data_fim:
                data_evento = data_inicio + timedelta(
                    days=random.randint(0, (data_fim - data_inicio).days)
                )
            else:
                data_evento = datetime.now() - timedelta(days=random.randint(0, 30))

            # Tipo aleatório de evento se não especificado
            tipo_evento = tipo or random.choice(list(EventoClimaticoTipo))

            # Intensidade e probabilidade simuladas
            intensidade = random.uniform(3.0, 5.0)  # Escala de 1 a 5
            probabilidade = random.uniform(0.6, 0.95)

            # Gerar coordenadas dentro do raio especificado se latitude/longitude fornecidas
            if latitude and longitude:
                # Adicionar variação aleatória dentro do raio (aproximadamente)
                lat_offset = random.uniform(-0.01, 0.01) * (raio / 10.0)
                lon_offset = random.uniform(-0.01, 0.01) * (raio / 10.0)
                evento_lat = latitude + lat_offset
                evento_lon = longitude + lon_offset
            else:
                evento_lat = -23.5505 + random.uniform(-10, 10)  # Exemplo para Brasil
                evento_lon = -46.6333 + random.uniform(-10, 10)

            descricao = self._gerar_descricao_evento(
                tipo_evento, evento_lat, evento_lon, data_evento
            )

            evento = EventoClimatico(
                tipo=tipo_evento,
                latitude=evento_lat,
                longitude=evento_lon,
                data_inicio=data_evento,
                intensidade=intensidade,
                probabilidade=probabilidade,
                descricao=descricao,
                nivel_alerta=math.ceil(intensidade),
            )

            eventos.append(evento)

        return sorted(eventos, key=lambda x: x.data_inicio, reverse=True)

    def obter_eventos_por_severidade(
        self, latitude: float, longitude: float, severidade_minima: int, dias: int
    ) -> List[EventoClimatico]:
        """
        Obter eventos climáticos com severidade mínima em uma área
        """
        eventos = self.obter_eventos(
            latitude=latitude,
            longitude=longitude,
            tipo=None,
            data_inicio=datetime.now() - timedelta(days=dias),
            data_fim=datetime.now(),
            raio=50.0,
        )

        # Filtrar por severidade mínima
        eventos_filtrados = [e for e in eventos if e.nivel_alerta >= severidade_minima]

        return eventos_filtrados

    def _gerar_descricao_evento(
        self,
        tipo: EventoClimaticoTipo,
        latitude: float,
        longitude: float,
        data: datetime,
    ) -> str:
        """
        Gerar descrição detalhada para um evento climático
        """
        descricoes = {
            EventoClimaticoTipo.SECA: f"Período prolongado de baixa precipitação detectado na região "
            f"(coordenadas: {latitude:.4f}, {longitude:.4f}) em {data.strftime('%Y-%m-%d')}. "
            f"Índice SPI abaixo de -2.0.",
            EventoClimaticoTipo.ENCHENTE: f"Evento de precipitação extrema detectado na região "
            f"(coordenadas: {latitude:.4f}, {longitude:.4f}) em {data.strftime('%Y-%m-%d')}. "
            f"Risco de inundações em áreas de baixada.",
            EventoClimaticoTipo.ONDA_CALOR: f"Onda de calor severa detectada na região "
            f"(coordenadas: {latitude:.4f}, {longitude:.4f}) em {data.strftime('%Y-%m-%d')}. "
            f"Temperaturas acima de 35°C por mais de 3 dias consecutivos.",
            EventoClimaticoTipo.GEADA: f"Ocorrência de geada detectada na região "
            f"(coordenadas: {latitude:.4f}, {longitude:.4f}) em {data.strftime('%Y-%m-%d')}. "
            f"Risco para culturas sensíveis.",
            EventoClimaticoTipo.SECA_FLASH: f"Seca flash detectada na região "
            f"(coordenadas: {latitude:.4f}, {longitude:.4f}) em {data.strftime('%Y-%m-%d')}. "
            f"Degradada rápida da umidade do solo com impacto potencial na agricultura.",
        }

        return descricoes.get(
            tipo,
            f"Evento climático {tipo.value} detectado em {data.strftime('%Y-%m-%d')}",
        )

    def obter_eventos_com_tokens(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        tipo: Optional[EventoClimaticoTipo],
        data_inicio: Optional[datetime],
        data_fim: Optional[datetime],
        raio: float,
    ) -> Tuple[List[EventoClimatico], List[EventoToken]]:
        """
        Obter eventos climáticos com seus respectivos tokens

        Returns:
            Tuple com lista de eventos e lista de tokens correspondentes
        """
        eventos = self.obter_eventos(
            latitude, longitude, tipo, data_inicio, data_fim, raio
        )
        tokens = self.token_service.tokenizar_multiplos_eventos(eventos)

        return eventos, tokens

    def obter_tokens_eventos(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        tipo: Optional[EventoClimaticoTipo],
        data_inicio: Optional[datetime],
        data_fim: Optional[datetime],
        raio: float,
    ) -> List[EventoToken]:
        """
        Obter apenas os tokens dos eventos climáticos detectados

        Returns:
            Lista de tokens dos eventos
        """
        eventos = self.obter_eventos(
            latitude, longitude, tipo, data_inicio, data_fim, raio
        )
        tokens = self.token_service.tokenizar_multiplos_eventos(eventos)

        return tokens

    def obter_evento_por_token(
        self, token_id: str
    ) -> Tuple[Optional[EventoClimatico], Optional[EventoToken]]:
        """
        Obter evento e token por ID do token

        Args:
            token_id: ID do token a ser buscado

        Returns:
            Tuple com evento e token, ou (None, None) se não encontrado
        """
        try:
            # Decodificar informações do token
            token_info = self.token_service.decodificar_token(token_id)

            # Simular busca do evento baseado nas informações do token
            # Em produção, isso seria uma busca no banco de dados
            evento_simulado = EventoClimatico(
                tipo=token_info.get("event_type"),
                latitude=-8.7618,  # Porto Velho como exemplo
                longitude=-63.9039,
                data_inicio=datetime.now() - timedelta(days=2),
                intensidade=4.0,
                probabilidade=0.8,
                descricao=f"Evento {token_info.get('event_type').value} recuperado por token",
                nivel_alerta=token_info.get("severity_level", 3),
            )

            # Gerar token para o evento simulado
            token = self.token_service.gerar_token_evento(evento_simulado)

            return evento_simulado, token

        except Exception as e:
            print(f"Erro ao buscar evento por token: {str(e)}")
            return None, None

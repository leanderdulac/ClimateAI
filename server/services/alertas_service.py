"""
Serviço para sistema de alertas
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from models.schemas import Alerta
from services.eventos_service import EventosService


class AlertasService:
    def __init__(self):
        self.eventos_service = EventosService()
        self.alertas_armazenados = []  # Em produção, usar banco de dados
        self._gerar_alertas_iniciais()

    def _gerar_alertas_iniciais(self):
        """
        Gerar alguns alertas iniciais para demonstração
        """
        for i in range(5):
            alerta = Alerta(
                id=str(uuid.uuid4()),
                tipo=random.choice(["clima", "preco", "evento", "sistema"]),
                titulo=f"Alerta de Demonstração #{i+1}",
                descricao=f"Este é um alerta de demonstração simulado para teste do sistema FIMCE.",
                nivel=random.randint(1, 5),
                localizacao=(
                    {
                        "lat": -23.5505 + random.uniform(-5, 5),
                        "lon": -46.6333 + random.uniform(-5, 5),
                    }
                    if random.choice([True, False])
                    else None
                ),
                data_criacao=datetime.now() - timedelta(hours=random.randint(1, 24)),
                data_validade=datetime.now() + timedelta(days=7),
                lido=random.choice([True, False]),
            )
            self.alertas_armazenados.append(alerta)

    def obter_alertas(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        nivel_minimo: int,
        ativo: bool,
        limite: int,
    ) -> List[Alerta]:
        """
        Obter alertas ativos em uma área específica
        """
        # Filtrar alertas ativos
        alertas_filtrados = []

        for alerta in self.alertas_armazenados:
            # Verificar se o alerta está ativo
            if ativo and alerta.data_validade < datetime.now():
                continue

            # Verificar nível mínimo
            if alerta.nivel < nivel_minimo:
                continue

            # Verificar localização se fornecida
            if latitude and longitude and alerta.localizacao:
                # Calcular distância aproximada (em graus, simplificado)
                distancia = (
                    (alerta.localizacao["lat"] - latitude) ** 2
                    + (alerta.localizacao["lon"] - longitude) ** 2
                ) ** 0.5
                # Considerar alertas dentro de 5 graus de distância (aproximadamente 500km)
                if distancia > 5.0:
                    continue

            alertas_filtrados.append(alerta)

        # Ordenar por nível (decrescente) e data de criação (decrescente)
        alertas_filtrados.sort(key=lambda x: (x.nivel, x.data_criacao), reverse=True)

        # Limitar resultados
        return alertas_filtrados[:limite]

    def obter_alertas_usuario(
        self, usuario_id: str, lido: Optional[bool]
    ) -> List[Alerta]:
        """
        Obter alertas específicos de um usuário
        """
        # Em um sistema real, isso filtraria alertas associados ao usuário
        alertas_usuario = self.alertas_armazenados

        if lido is not None:
            alertas_usuario = [a for a in alertas_usuario if a.lido == lido]

        return alertas_usuario

    def marcar_como_lido(self, alerta_id: str):
        """
        Marcar um alerta como lido
        """
        for alerta in self.alertas_armazenados:
            if alerta.id == alerta_id:
                alerta.lido = True
                return

        raise ValueError(f"Alerta com ID {alerta_id} não encontrado")

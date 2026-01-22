"""
Serviço de tokenização para eventos climáticos
"""

import hashlib
import json
import math
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from models.schemas import EventoClimatico, EventoClimaticoTipo
from models.token_schemas import EventoToken, TokenAnalysis, TokenGroup
from services.tokenization_service import TokenizationService

logger = logging.getLogger(__name__)

class TokenizacaoEventosService:
    """
    Serviço para tokenização de eventos climáticos.
    Gera tokens únicos e estruturados para identificação e processamento de eventos.
    Integra com TokenizationService para mintagem na blockchain.
    """

    def __init__(self):
        # Mapeamento de tipos de eventos para códigos numéricos
        self.event_type_codes = {
            EventoClimaticoTipo.SECA: "SEC",
            EventoClimaticoTipo.ENCHENTE: "ENC",
            EventoClimaticoTipo.ONDA_CALOR: "CAL",
            EventoClimaticoTipo.GEADA: "GEA",
            EventoClimaticoTipo.SECA_FLASH: "SFL",
        }

        # Pesos para cálculo de severidade composta
        self.severity_weights = {
            "intensity": 0.4,
            "probability": 0.3,
            "duration": 0.2,
            "spatial_extent": 0.1,
        }
        
        # Inicializa o serviço de blockchain (pode ser Mock ou Real)
        try:
            self.blockchain_service = TokenizationService()
        except Exception as e:
            logger.error(f"Falha ao iniciar serviço de blockchain: {e}")
            self.blockchain_service = None

    def gerar_token_evento(self, evento: EventoClimatico) -> EventoToken:
        """
        Gera um token único para um evento climático

        Args:
            evento: Instância de EventoClimatico

        Returns:
            EventoToken: Token estruturado do evento
        """
        # Calcular severidade composta
        severity_level = self._calcular_severidade_composta(evento)

        # Gerar hashes para localização e temporal
        location_hash = self._gerar_hash_localizacao(evento.latitude, evento.longitude)
        temporal_hash = self._gerar_hash_temporal(evento.data_inicio, evento.data_fim)

        # Gerar token ID único
        token_id = self._gerar_token_id(
            evento.tipo,
            severity_level,
            location_hash,
            temporal_hash,
            evento.data_inicio,
        )

        # Metadata adicional
        metadata = {
            "original_severity": evento.nivel_alerta,
            "description": evento.descricao,
            "calculated_severity": severity_level,
            "event_category": self._categorizar_evento(evento),
            "risk_score": self._calcular_risco(evento, severity_level),
            "on_chain_status": "pending",
            "tx_hash": None
        }

        return EventoToken(
            token_id=token_id,
            event_type=evento.tipo,
            severity_level=severity_level,
            latitude=evento.latitude,
            longitude=evento.longitude,
            start_date=evento.data_inicio,
            end_date=evento.data_fim,
            intensity=evento.intensidade,
            probability=evento.probabilidade,
            location_hash=location_hash,
            temporal_hash=temporal_hash,
            metadata=metadata,
            created_at=datetime.now(),
        )

    def mint_token_on_chain(self, token: EventoToken, destination_address: str) -> Dict[str, Any]:
        """
        Realiza a emissão (mint) do token na blockchain.
        
        Args:
            token: O objeto EventoToken gerado
            destination_address: Endereço da carteira Ethereum para receber o token
            
        Returns:
            Dict com o status da transação e hash
        """
        if not self.blockchain_service:
            logger.warning("Serviço de blockchain indisponível. Token não será mintado on-chain.")
            return {"status": "error", "message": "Blockchain service unavailable"}

        try:
            # A quantidade de tokens pode ser baseada na severidade ou risco
            # Ex: Severidade 5 = 50 tokens, Severidade 1 = 10 tokens
            amount = token.severity_level * 10
            
            logger.info(f"Iniciando mintagem on-chain para token {token.token_id} -> {destination_address}")
            receipt = self.blockchain_service.mint(destination_address, amount)
            
            # Extrair hash da transação
            tx_hash = receipt.get("transactionHash") if isinstance(receipt, dict) else receipt.transactionHash
            if hasattr(tx_hash, 'hex'):
                tx_hash = tx_hash.hex()
            elif isinstance(tx_hash, bytes):
                tx_hash = tx_hash.hex()

            # Atualizar metadata do token (em memória, persistência deve ser feita pelo chamador)
            token.metadata["on_chain_status"] = "minted"
            token.metadata["tx_hash"] = tx_hash
            token.metadata["minted_amount"] = amount
            
            return {
                "status": "success",
                "tx_hash": tx_hash,
                "amount": amount,
                "token_id": token.token_id
            }
            
        except Exception as e:
            logger.error(f"Erro ao mintar token on-chain: {e}")
            token.metadata["on_chain_status"] = "failed"
            token.metadata["error"] = str(e)
            return {"status": "error", "message": str(e)}

    def tokenizar_multiplos_eventos(
        self, eventos: List[EventoClimatico]
    ) -> List[EventoToken]:
        """
        Tokeniza múltiplos eventos climáticos

        Args:
            eventos: Lista de eventos climáticos

        Returns:
            List[EventoToken]: Lista de tokens gerados
        """
        tokens = []
        for evento in eventos:
            try:
                token = self.gerar_token_evento(evento)
                tokens.append(token)
            except Exception as e:
                # Log do erro e continuação do processamento
                print(f"Erro ao tokenizar evento {evento.tipo}: {str(e)}")
                continue

        return tokens

    def decodificar_token(self, token_id: str) -> Dict[str, Any]:
        """
        Decodifica um token ID para extrair informações

        Args:
            token_id: ID do token a ser decodificado

        Returns:
            Dict com informações extraídas do token
        """
        try:
            # Token format: TYPE-LEVEL-LOC-TEMP-TIME
            parts = token_id.split("-")
            if len(parts) != 5:
                raise ValueError("Formato de token inválido")

            event_type_code = parts[0]
            severity_level = int(parts[1])
            location_hash = parts[2]
            temporal_hash = parts[3]
            timestamp = parts[4]

            # Mapear código de volta para tipo de evento
            event_type = None
            for tipo, code in self.event_type_codes.items():
                if code == event_type_code:
                    event_type = tipo
                    break

            return {
                "event_type": event_type,
                "severity_level": severity_level,
                "location_hash": location_hash,
                "temporal_hash": temporal_hash,
                "timestamp": timestamp,
                "token_structure": "TYPE-LEVEL-LOC-TEMP-TIME",
            }

        except Exception as e:
            raise ValueError(f"Erro ao decodificar token: {str(e)}")

    def agrupar_eventos_por_token(
        self, tokens: List[EventoToken]
    ) -> Dict[str, List[EventoToken]]:
        """
        Agrupa tokens por características similares

        Args:
            tokens: Lista de tokens a agrupar

        Returns:
            Dict com grupos de tokens
        """
        grupos = {}

        for token in tokens:
            # Chave de agrupamento baseada em tipo e severidade
            group_key = f"{token.event_type.value}_{token.severity_level}"

            if group_key not in grupos:
                grupos[group_key] = []

            grupos[group_key].append(token)

        return grupos

    def _calcular_severidade_composta(self, evento: EventoClimatico) -> int:
        """
        Calcula severidade composta baseada em múltiplos fatores
        """
        # Intensidade normalizada (1-5)
        intensity_score = min(5, max(1, evento.intensidade))

        # Probabilidade normalizada (1-5)
        prob_score = min(5, max(1, evento.probabilidade * 5))

        # Duração (se disponível)
        duration_score = 3  # padrão médio
        if evento.data_fim:
            duration_days = (evento.data_fim - evento.data_inicio).days
            duration_score = min(5, max(1, duration_days / 7))  # 1 semana = score 1

        # Extensão espacial (estimativa baseada em coordenadas)
        spatial_score = 3  # padrão médio

        # Cálculo ponderado
        composite_score = (
            self.severity_weights["intensity"] * intensity_score
            + self.severity_weights["probability"] * prob_score
            + self.severity_weights["duration"] * duration_score
            + self.severity_weights["spatial_extent"] * spatial_score
        )

        return round(composite_score)

    def _gerar_hash_localizacao(self, latitude: float, longitude: float) -> str:
        """
        Gera hash único para localização geográfica
        """
        # Arredondar para reduzir granularidade e agrupar locais próximos
        lat_rounded = round(latitude, 2)  # ~1km de precisão
        lon_rounded = round(longitude, 2)

        location_str = f"{lat_rounded:.2f},{lon_rounded:.2f}"
        return hashlib.md5(location_str.encode()).hexdigest()[:8]

    def _gerar_hash_temporal(
        self, start_date: datetime, end_date: Optional[datetime]
    ) -> str:
        """
        Gera hash único para período temporal
        """
        if end_date:
            temporal_str = f"{start_date.isoformat()}_{end_date.isoformat()}"
        else:
            temporal_str = start_date.isoformat()

        return hashlib.md5(temporal_str.encode()).hexdigest()[:8]

    def _gerar_token_id(
        self,
        event_type: EventoClimaticoTipo,
        severity_level: int,
        location_hash: str,
        temporal_hash: str,
        timestamp: datetime,
    ) -> str:
        """
        Gera ID único do token
        """
        type_code = self.event_type_codes[event_type]
        time_code = timestamp.strftime("%Y%m%d%H%M%S")

        # Combinar elementos para criar token único
        token_components = [
            type_code,
            str(severity_level),
            location_hash[:4],  # primeiros 4 chars do hash de localização
            temporal_hash[:4],  # primeiros 4 chars do hash temporal
            time_code,
        ]

        return "-".join(token_components)

    def _categorizar_evento(self, evento: EventoClimatico) -> str:
        """
        Categoriza evento baseado em suas características
        """
        if evento.intensidade >= 4.5:
            return "extremo"
        elif evento.intensidade >= 3.5:
            return "severo"
        elif evento.intensidade >= 2.5:
            return "moderado"
        else:
            return "leve"

    def _calcular_risco(self, evento: EventoClimatico, severity_level: int) -> float:
        """
        Calcula score de risco baseado no evento e severidade
        """
        # Fatores de risco por tipo de evento
        risk_factors = {
            EventoClimaticoTipo.SECA: 0.8,
            EventoClimaticoTipo.ENCHENTE: 0.9,
            EventoClimaticoTipo.ONDA_CALOR: 0.7,
            EventoClimaticoTipo.GEADA: 0.6,
            EventoClimaticoTipo.SECA_FLASH: 0.85,
        }

        base_risk = risk_factors.get(evento.tipo, 0.5)
        severity_multiplier = severity_level / 5.0  # normalizar para 0-1

        return min(1.0, base_risk * severity_multiplier * evento.probabilidade)

    def analisar_tokens(self, tokens: List[EventoToken]) -> TokenAnalysis:
        """
        Realiza análise estatística dos tokens

        Args:
            tokens: Lista de tokens a analisar

        Returns:
            TokenAnalysis: Análise estatística dos tokens
        """
        if not tokens:
            return TokenAnalysis(
                total_tokens=0,
                tokens_by_type={},
                tokens_by_severity={},
                risk_distribution={},
                temporal_clusters=[],
                spatial_clusters=[],
            )

        # Contagem por tipo
        tokens_by_type = {}
        for token in tokens:
            tipo = token.event_type.value
            tokens_by_type[tipo] = tokens_by_type.get(tipo, 0) + 1

        # Contagem por severidade
        tokens_by_severity = {}
        for token in tokens:
            severity = token.severity_level
            tokens_by_severity[severity] = tokens_by_severity.get(severity, 0) + 1

        # Distribuição de risco
        risk_distribution = {}
        for token in tokens:
            risk_score = token.metadata.get("risk_score", 0)
            risk_category = self._categorizar_risco(risk_score)
            risk_distribution[risk_category] = (
                risk_distribution.get(risk_category, 0) + 1
            )

        # Clusters temporais (simplificado)
        temporal_clusters = self._identificar_clusters_temporais(tokens)

        # Clusters espaciais (simplificado)
        spatial_clusters = self._identificar_clusters_espaciais(tokens)

        return TokenAnalysis(
            total_tokens=len(tokens),
            tokens_by_type=tokens_by_type,
            tokens_by_severity=tokens_by_severity,
            risk_distribution=risk_distribution,
            temporal_clusters=temporal_clusters,
            spatial_clusters=spatial_clusters,
        )

    def agrupar_tokens(self, tokens: List[EventoToken]) -> List[TokenGroup]:
        """
        Agrupa tokens por similaridade

        Args:
            tokens: Lista de tokens a agrupar

        Returns:
            List[TokenGroup]: Grupos de tokens similares
        """
        grupos_dict = self.agrupar_eventos_por_token(tokens)
        grupos = []

        for group_key, group_tokens in grupos_dict.items():
            if len(group_tokens) < 2:
                continue

            # Calcular centróide da localização
            latitudes = [t.latitude for t in group_tokens]
            longitudes = [t.longitude for t in group_tokens]
            centroid_lat = sum(latitudes) / len(latitudes)
            centroid_lon = sum(longitudes) / len(longitudes)

            # Severidade média
            avg_severity = sum(t.severity_level for t in group_tokens) / len(
                group_tokens
            )

            # Score de risco médio
            avg_risk = sum(t.metadata.get("risk_score", 0) for t in group_tokens) / len(
                group_tokens
            )

            grupo = TokenGroup(
                group_id=f"GROUP_{group_key}_{hash(group_key) % 10000}",
                group_type=group_key,
                tokens=[t.token_id for t in group_tokens],
                centroid_location={"latitude": centroid_lat, "longitude": centroid_lon},
                average_severity=round(avg_severity, 2),
                risk_score=round(avg_risk, 3),
                metadata={
                    "member_count": len(group_tokens),
                    "date_range": self._calcular_range_temporal(group_tokens),
                },
            )
            grupos.append(grupo)

        return grupos

    def calcular_risco_token(self, token_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula score de risco para informações de token decodificado

        Args:
            token_info: Informações decodificadas do token

        Returns:
            Dict com análise de risco
        """
        event_type = token_info.get("event_type")
        severity_level = token_info.get("severity_level", 3)

        # Fatores de risco por tipo de evento
        risk_factors = {
            EventoClimaticoTipo.SECA: 0.8,
            EventoClimaticoTipo.ENCHENTE: 0.9,
            EventoClimaticoTipo.ONDA_CALOR: 0.7,
            EventoClimaticoTipo.GEADA: 0.6,
            EventoClimaticoTipo.SECA_FLASH: 0.85,
        }

        base_risk = risk_factors.get(event_type, 0.5)
        severity_multiplier = severity_level / 5.0

        risk_score = min(1.0, base_risk * severity_multiplier)

        return {
            "risk_score": round(risk_score, 3),
            "risk_level": self._categorizar_risco(risk_score),
            "contributing_factors": {
                "event_type_risk": base_risk,
                "severity_multiplier": severity_multiplier,
                "event_type": event_type.value if event_type else "unknown",
            },
            "recommendations": self._gerar_recomendacoes_risco(risk_score, event_type),
        }

    def validar_token(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida a integridade e consistência de um token

        Args:
            token_data: Dados do token a validar

        Returns:
            Dict com resultado da validação
        """
        try:
            token_id = token_data.get("token_id", "")

            # Verificar formato básico
            if not token_id or len(token_id.split("-")) != 5:
                return {
                    "valid": False,
                    "error": "Formato de token inválido",
                    "checks": {"format": False},
                }

            # Tentar decodificar
            decoded = self.decodificar_token(token_id)

            # Verificar consistência dos dados
            consistency_checks = {
                "event_type_valid": decoded.get("event_type") is not None,
                "severity_range": 1 <= decoded.get("severity_level", 0) <= 5,
                "structure_complete": len(decoded) >= 5,
            }

            is_valid = all(consistency_checks.values())

            return {
                "valid": is_valid,
                "decoded_info": decoded if is_valid else None,
                "checks": consistency_checks,
                "error": None if is_valid else "Dados do token inconsistentes",
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Erro na validação: {str(e)}",
                "checks": {"exception": False},
            }

    def _categorizar_risco(self, risk_score: float) -> str:
        """Categoriza score de risco"""
        if risk_score >= 0.8:
            return "extremo"
        elif risk_score >= 0.6:
            return "alto"
        elif risk_score >= 0.4:
            return "medio"
        elif risk_score >= 0.2:
            return "baixo"
        else:
            return "muito_baixo"

    def _identificar_clusters_temporais(
        self, tokens: List[EventoToken]
    ) -> List[Dict[str, Any]]:
        """Identifica clusters temporais simplificados"""
        # Agrupar por mês
        monthly_groups = {}
        for token in tokens:
            month_key = token.start_date.strftime("%Y-%m")
            if month_key not in monthly_groups:
                monthly_groups[month_key] = []
            monthly_groups[month_key].append(token)

        clusters = []
        for month, month_tokens in monthly_groups.items():
            if len(month_tokens) >= 2:
                clusters.append(
                    {
                        "period": month,
                        "event_count": len(month_tokens),
                        "avg_severity": sum(t.severity_level for t in month_tokens)
                        / len(month_tokens),
                        "event_types": list(
                            set(t.event_type.value for t in month_tokens)
                        ),
                    }
                )

        return clusters

    def _identificar_clusters_espaciais(
        self, tokens: List[EventoToken]
    ) -> List[Dict[str, Any]]:
        """Identifica clusters espaciais simplificados"""
        # Agrupar por região aproximada (graus arredondados)
        spatial_groups = {}
        for token in tokens:
            region_key = f"{round(token.latitude, 1)},{round(token.longitude, 1)}"
            if region_key not in spatial_groups:
                spatial_groups[region_key] = []
            spatial_groups[region_key].append(token)

        clusters = []
        for region, region_tokens in spatial_groups.items():
            if len(region_tokens) >= 2:
                lat, lon = map(float, region.split(","))
                clusters.append(
                    {
                        "centroid": {"latitude": lat, "longitude": lon},
                        "event_count": len(region_tokens),
                        "avg_severity": sum(t.severity_level for t in region_tokens)
                        / len(region_tokens),
                        "event_types": list(
                            set(t.event_type.value for t in region_tokens)
                        ),
                    }
                )

        return clusters

    def _calcular_range_temporal(self, tokens: List[EventoToken]) -> Dict[str, str]:
        """Calcula o range temporal de um grupo de tokens"""
        if not tokens:
            return {"start": None, "end": None}

        start_dates = [t.start_date for t in tokens]
        end_dates = [t.end_date or t.start_date for t in tokens]

        return {
            "start": min(start_dates).isoformat(),
            "end": max(end_dates).isoformat(),
        }

    def _gerar_recomendacoes_risco(
        self, risk_score: float, event_type: EventoClimaticoTipo
    ) -> List[str]:
        """Gera recomendações baseadas no score de risco"""
        recommendations = []

        if risk_score >= 0.8:
            recommendations.extend(
                [
                    "Implementar plano de contingência imediato",
                    "Monitorar condições meteorológicas continuamente",
                    "Preparar evacuação se necessário",
                    "Alertar autoridades locais",
                ]
            )
        elif risk_score >= 0.6:
            recommendations.extend(
                [
                    "Aumentar monitoramento da região",
                    "Preparar recursos de emergência",
                    "Comunicar risco para comunidade afetada",
                ]
            )
        elif risk_score >= 0.4:
            recommendations.extend(
                [
                    "Manter vigilância constante",
                    "Atualizar planos de resposta",
                    "Informar stakeholders sobre o risco",
                ]
            )

        # Recomendações específicas por tipo de evento
        if event_type == EventoClimaticoTipo.ENCHENTE:
            recommendations.append("Verificar sistemas de drenagem e diques")
        elif event_type == EventoClimaticoTipo.SECA:
            recommendations.append("Implementar medidas de conservação de água")
        elif event_type == EventoClimaticoTipo.ONDA_CALOR:
            recommendations.append("Preparar infraestrutura para resfriamento")
        elif event_type == EventoClimaticoTipo.GEADA:
            recommendations.append("Proteger culturas sensíveis ao frio")

        return recommendations

"""
Serviço de tokenização blockchain para eventos climáticos
Adaptação do conceito Hathor para o sistema ClimateWise
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from models.schemas import EventoClimatico, EventoClimaticoTipo
from models.token_schemas import EventoToken
from services.tokenizacao_eventos_service import TokenizacaoEventosService


class BlockchainTokenService:
    """
    Serviço para tokenização de eventos climáticos com conceito blockchain.
    Adapta o conceito de tokens Hathor para o sistema ClimateWise.
    """

    def __init__(self):
        self.token_service = TokenizacaoEventosService()
        self.blockchain_registry = {}  # Simulação de registro blockchain
        self.network = "climatewise-testnet"  # Rede do ClimateWise

    async def mint_climate_token(
        self,
        evento: EventoClimatico,
        wallet_address: str,
        token_supply: int = 1000000,
        decimals: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Cria um token blockchain para um evento climático

        Args:
            evento: Evento climático a ser tokenizado
            wallet_address: Endereço da carteira do proprietário
            token_supply: Suprimento total do token
            decimals: Número de casas decimais
            metadata: Metadados adicionais do token

        Returns:
            Dict com informações da transação de mint
        """
        try:
            # Gerar token estruturado do ClimateWise
            # Passamos o metadata para que os risk_factors sejam persistidos no BD
            climate_token = await self.token_service.gerar_token_evento(evento, extra_metadata=metadata)

            # Criar token blockchain baseado no evento
            blockchain_token = self._create_blockchain_token(
                climate_token=climate_token,
                wallet_address=wallet_address,
                token_supply=token_supply,
                decimals=decimals,
                metadata=metadata or {},
            )

            # Registrar na blockchain simulada
            transaction = self._register_token_transaction(blockchain_token)

            # Aciona mint on-chain (real ou mock, conforme TokenizationService)
            on_chain_result = await self.token_service.mint_token_on_chain(
                climate_token,
                wallet_address,
            )

            if isinstance(on_chain_result, dict):
                blockchain_token["token_data"]["metadata"]["on_chain_result"] = on_chain_result

            return {
                "success": True,
                "transaction_id": transaction["tx_id"],
                "token_uid": blockchain_token["token_uid"],
                "climate_token_id": climate_token.token_id,
                "blockchain_token": blockchain_token,
                "transaction": transaction,
                "on_chain": on_chain_result,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "climate_token_id": None,
                "transaction_id": None,
            }

    def _create_blockchain_token(
        self,
        climate_token: EventoToken,
        wallet_address: str,
        token_supply: int,
        decimals: int,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Cria estrutura do token blockchain baseada no token ClimateWise
        """
        # Gerar UID único para o token (similar ao Hathor)
        token_uid = self._generate_token_uid(climate_token)

        # Criar dados do token
        token_data = {
            "name": self._generate_token_name(climate_token),
            "symbol": self._generate_token_symbol(climate_token),
            "decimals": decimals,
            "total_supply": token_supply,
            "climate_event": {
                "token_id": climate_token.token_id,
                "event_type": climate_token.event_type.value,
                "severity_level": climate_token.severity_level,
                "latitude": climate_token.latitude,
                "longitude": climate_token.longitude,
                "start_date": climate_token.start_date.isoformat(),
                "intensity": climate_token.intensity,
                "probability": climate_token.probability,
            },
            "metadata": {
                **metadata,
                **climate_token.metadata,
                "network": self.network,
                "created_at": datetime.now().isoformat(),
                "creator_address": wallet_address,
            },
        }

        return {
            "token_uid": token_uid,
            "token_data": token_data,
            "owner_address": wallet_address,
            "initial_supply": token_supply,
            "decimals": decimals,
        }

    def _generate_token_uid(self, climate_token: EventoToken) -> str:
        """
        Gera UID único para o token (hash do token ClimateWise + timestamp)
        """
        content = f"{climate_token.token_id}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def _generate_token_name(self, climate_token: EventoToken) -> str:
        """
        Gera nome do token baseado no evento climático
        """
        event_names = {
            EventoClimaticoTipo.SECA: "Seca Climática",
            EventoClimaticoTipo.ENCHENTE: "Evento de Enchente",
            EventoClimaticoTipo.ONDA_CALOR: "Onda de Calor",
            EventoClimaticoTipo.GEADA: "Evento de Geada",
            EventoClimaticoTipo.SECA_FLASH: "Seca Flash",
        }

        base_name = event_names.get(climate_token.event_type, "Evento Climático")
        location = f"{abs(climate_token.latitude):.2f}°{'N' if climate_token.latitude >= 0 else 'S'}"

        return f"{base_name} - {location} {climate_token.start_date.year}"

    def _generate_token_symbol(self, climate_token: EventoToken) -> str:
        """
        Gera símbolo do token baseado no tipo e severidade
        """
        type_codes = {
            EventoClimaticoTipo.SECA: "SEC",
            EventoClimaticoTipo.ENCHENTE: "ENC",
            EventoClimaticoTipo.ONDA_CALOR: "CAL",
            EventoClimaticoTipo.GEADA: "GEA",
            EventoClimaticoTipo.SECA_FLASH: "SFL",
        }

        type_code = type_codes.get(climate_token.event_type, "CLI")
        severity = climate_token.severity_level
        year = climate_token.start_date.year % 100  # Últimos 2 dígitos do ano

        return f"{type_code}{severity}{year}"

    def _register_token_transaction(
        self, blockchain_token: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registra a transação de criação do token na blockchain simulada
        """
        tx_id = str(uuid.uuid4())

        transaction = {
            "tx_id": tx_id,
            "type": "token_mint",
            "token_uid": blockchain_token["token_uid"],
            "timestamp": datetime.now().isoformat(),
            "inputs": [],  # Sem inputs para mint
            "outputs": [
                {
                    "address": blockchain_token["owner_address"],
                    "value": blockchain_token["initial_supply"],
                    "token_uid": blockchain_token["token_uid"],
                }
            ],
            "token_data": blockchain_token["token_data"],
            "network": self.network,
            "status": "confirmed",
        }

        # Registrar na blockchain simulada
        self.blockchain_registry[tx_id] = transaction
        self.blockchain_registry[blockchain_token["token_uid"]] = blockchain_token

        return transaction

    def get_token_info(self, token_uid: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um token pela UID
        """
        return self.blockchain_registry.get(token_uid)

    def get_transaction_info(self, tx_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de uma transação pelo ID
        """
        return self.blockchain_registry.get(tx_id)

    def list_tokens_by_owner(self, wallet_address: str) -> List[Dict[str, Any]]:
        """
        Lista todos os tokens de um proprietário
        """
        tokens = []
        for item in self.blockchain_registry.values():
            if isinstance(item, dict) and item.get("owner_address") == wallet_address:
                tokens.append(item)
        return tokens

    def transfer_token(
        self, token_uid: str, from_address: str, to_address: str, amount: int
    ) -> Dict[str, Any]:
        """
        Transfere tokens entre endereços
        """
        try:
            # Verificar se o token existe
            token_info = self.get_token_info(token_uid)
            if not token_info:
                raise ValueError("Token não encontrado")

            # Verificar propriedade
            if token_info["owner_address"] != from_address:
                raise ValueError("Endereço de origem não é proprietário do token")

            # Criar transação de transferência
            tx_id = str(uuid.uuid4())
            transaction = {
                "tx_id": tx_id,
                "type": "token_transfer",
                "token_uid": token_uid,
                "timestamp": datetime.now().isoformat(),
                "inputs": [
                    {"address": from_address, "value": amount, "token_uid": token_uid}
                ],
                "outputs": [
                    {"address": to_address, "value": amount, "token_uid": token_uid}
                ],
                "network": self.network,
                "status": "confirmed",
            }

            # Registrar transação
            self.blockchain_registry[tx_id] = transaction

            # Atualizar proprietário do token (simplificado)
            token_info["owner_address"] = to_address

            return {
                "success": True,
                "transaction_id": tx_id,
                "transaction": transaction,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "transaction_id": None}

    def get_climate_event_tokens(
        self, event_type: Optional[EventoClimaticoTipo] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista tokens de eventos climáticos por tipo
        """
        tokens = []
        for item in self.blockchain_registry.values():
            if isinstance(item, dict) and "token_data" in item:
                token_data = item["token_data"]
                if "climate_event" in token_data:
                    if (
                        event_type is None
                        or token_data["climate_event"]["event_type"] == event_type.value
                    ):
                        tokens.append(item)
        return tokens


# Exemplo de uso adaptado para o ClimateWise
if __name__ == "__main__":
    # Inicializar serviço
    blockchain_service = BlockchainTokenService()

    # Criar evento climático de exemplo
    evento_exemplo = EventoClimatico(
        tipo=EventoClimaticoTipo.SECA,
        latitude=-8.7618,
        longitude=-63.9039,
        data_inicio=datetime.now() - timedelta(days=5),
        intensidade=4.2,
        probabilidade=0.85,
        descricao="Seca severa detectada na região de Porto Velho",
        nivel_alerta=4,
    )

    # Endereço da carteira (simulado)
    wallet_address = "climatewise_wallet_001"

    # Criar token blockchain
    resultado = blockchain_service.mint_climate_token(
        evento=evento_exemplo,
        wallet_address=wallet_address,
        token_supply=1000000,  # 1M tokens
        decimals=0,
        metadata={
            "region": "Porto Velho, RO",
            "impact_level": "high",
            "mitigation_required": True,
        },
    )

    if resultado["success"]:
        print("✅ Token blockchain criado com sucesso!")
        print(f"Transaction ID: {resultado['transaction_id']}")
        print(f"Token UID: {resultado['token_uid']}")
        print(f"Climate Token ID: {resultado['climate_token_id']}")
        print(f"Token Symbol: {resultado['blockchain_token']['token_data']['symbol']}")
        print(f"Token Name: {resultado['blockchain_token']['token_data']['name']}")
    else:
        print(f"❌ Erro ao criar token: {resultado['error']}")

    # Listar tokens do proprietário
    print(f"\n📋 Tokens do proprietário {wallet_address}:")
    owner_tokens = blockchain_service.list_tokens_by_owner(wallet_address)
    for token in owner_tokens:
        print(f"  - {token['token_data']['symbol']}: {token['token_data']['name']}")

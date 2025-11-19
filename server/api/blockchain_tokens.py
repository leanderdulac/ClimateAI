"""
Router para endpoints de tokens blockchain de eventos climáticos
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

from models.schemas import EventoClimatico, EventoClimaticoTipo
from models.token_schemas import (
    BlockchainToken,
    BlockchainTransaction,
    TokenMintRequest,
    TokenTransferRequest,
)
from services.blockchain_token_service import BlockchainTokenService

router = APIRouter()
blockchain_service = BlockchainTokenService()


@router.post("/mint", response_model=Dict[str, Any])
async def mint_climate_token(request: TokenMintRequest = Body(...)):
    """
    Cria um token blockchain para um evento climático

    Esta operação cria um token único na blockchain ClimateAI
    representando um evento climático específico.
    """
    try:
        resultado = blockchain_service.mint_climate_token(
            evento=request.evento,
            wallet_address=request.wallet_address,
            token_supply=request.token_supply,
            decimals=request.decimals,
            metadata=request.metadata,
        )

        if not resultado["success"]:
            raise HTTPException(
                status_code=400, detail=f"Erro ao criar token: {resultado['error']}"
            )

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro interno ao criar token: {str(e)}"
        )


@router.get("/token/{token_uid}")
async def get_token_info(token_uid: str):
    """
    Obtém informações detalhadas de um token

    Args:
        token_uid: UID único do token
    """
    try:
        token_info = blockchain_service.get_token_info(token_uid)
        if not token_info:
            raise HTTPException(status_code=404, detail="Token não encontrado")

        return token_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar token: {str(e)}")


@router.get("/transaction/{tx_id}")
async def get_transaction_info(tx_id: str):
    """
    Obtém informações de uma transação

    Args:
        tx_id: ID da transação
    """
    try:
        tx_info = blockchain_service.get_transaction_info(tx_id)
        if not tx_info:
            raise HTTPException(status_code=404, detail="Transação não encontrada")

        return tx_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao buscar transação: {str(e)}"
        )


@router.get("/wallet/{wallet_address}/tokens")
async def get_wallet_tokens(wallet_address: str):
    """
    Lista todos os tokens de uma carteira

    Args:
        wallet_address: Endereço da carteira
    """
    try:
        tokens = blockchain_service.list_tokens_by_owner(wallet_address)
        return {"tokens": tokens, "count": len(tokens)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao buscar tokens da carteira: {str(e)}"
        )


@router.post("/transfer", response_model=Dict[str, Any])
async def transfer_token(request: TokenTransferRequest = Body(...)):
    """
    Transfere tokens entre carteiras

    Args:
        request: Dados da transferência
    """
    try:
        resultado = blockchain_service.transfer_token(
            token_uid=request.token_uid,
            from_address=request.from_address,
            to_address=request.to_address,
            amount=request.amount,
        )

        if not resultado["success"]:
            raise HTTPException(
                status_code=400, detail=f"Erro na transferência: {resultado['error']}"
            )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro interno na transferência: {str(e)}"
        )


@router.get("/eventos/{event_type}")
async def get_tokens_by_event_type(event_type: EventoClimaticoTipo):
    """
    Lista tokens de um tipo específico de evento climático

    Args:
        event_type: Tipo de evento climático
    """
    try:
        tokens = blockchain_service.get_climate_event_tokens(event_type)
        return {"event_type": event_type.value, "tokens": tokens, "count": len(tokens)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar tokens por tipo de evento: {str(e)}",
        )


@router.get("/eventos")
async def get_all_climate_event_tokens():
    """
    Lista todos os tokens de eventos climáticos
    """
    try:
        tokens = blockchain_service.get_climate_event_tokens()
        return {
            "tokens": tokens,
            "count": len(tokens),
            "network": blockchain_service.network,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar tokens de eventos climáticos: {str(e)}",
        )


@router.get("/stats")
async def get_blockchain_stats():
    """
    Obtém estatísticas da blockchain ClimateAI
    """
    try:
        # Contar diferentes tipos de registros
        total_transactions = 0
        total_tokens = 0
        token_types = {}

        for item in blockchain_service.blockchain_registry.values():
            if isinstance(item, dict):
                if "tx_id" in item and "type" in item:
                    total_transactions += 1
                elif "token_uid" in item and "token_data" in item:
                    total_tokens += 1
                    event_type = (
                        item["token_data"].get("climate_event", {}).get("event_type")
                    )
                    if event_type:
                        token_types[event_type] = token_types.get(event_type, 0) + 1

        return {
            "network": blockchain_service.network,
            "total_transactions": total_transactions,
            "total_tokens": total_tokens,
            "token_types": token_types,
            "registry_size": len(blockchain_service.blockchain_registry),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}"
        )


@router.get("/wallet/{wallet_address}/balance")
async def get_wallet_balance(wallet_address: str):
    """
    Obter saldo completo da carteira incluindo todos os tokens
    """
    try:
        # Buscar tokens do proprietário
        tokens = blockchain_service.list_tokens_by_owner(wallet_address)

        # Calcular estatísticas
        total_value = sum(token.get("initial_supply", 0) for token in tokens)
        active_tokens = len([t for t in tokens if t.get("initial_supply", 0) > 0])

        # Simular variação 24h (em produção, isso viria de dados reais de mercado)
        portfolio_change_24h = 8.5  # Mock data - em produção calcular baseado em preços

        # Formatar dados para o frontend
        formatted_tokens = []
        for token in tokens:
            token_data = token.get("token_data", {})
            climate_event = token_data.get("climate_event", {})

            formatted_tokens.append(
                {
                    "tokenUid": token.get("token_uid", ""),
                    "symbol": token_data.get("symbol", ""),
                    "name": token_data.get("name", ""),
                    "balance": token.get("initial_supply", 0),
                    "value": token.get(
                        "initial_supply", 0
                    ),  # Simplificado - em produção usar preço real
                    "change24h": 0,  # Mock - em produção calcular variação real
                    "eventType": climate_event.get("event_type", ""),
                    "severity": climate_event.get("severity_level", 0),
                    "location": f"{climate_event.get('latitude', 0):.2f}°, {climate_event.get('longitude', 0):.2f}°",
                    "createdAt": token_data.get("metadata", {}).get("created_at", ""),
                }
            )

        return {
            "wallet_address": wallet_address,
            "total_tokens": len(tokens),
            "active_tokens": active_tokens,
            "total_value": total_value,
            "portfolio_change_24h": portfolio_change_24h,
            "tokens": formatted_tokens,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter saldo da carteira: {str(e)}"
        )


@router.get("/wallet/{wallet_address}/transactions")
async def get_wallet_transactions(
    wallet_address: str, limit: int = Query(50, ge=1, le=100)
):
    """
    Obter histórico de transações da carteira
    """
    try:
        registry = blockchain_service.blockchain_registry

        # Filtrar transações relacionadas à carteira
        transactions = []
        for item in registry.values():
            if isinstance(item, dict) and "tx_id" in item:
                tx = item
                # Verificar se a carteira está envolvida na transação
                wallet_involved = False

                # Verificar inputs
                if tx.get("inputs"):
                    for inp in tx["inputs"]:
                        if (
                            isinstance(inp, dict)
                            and inp.get("address") == wallet_address
                        ):
                            wallet_involved = True
                            break

                # Verificar outputs
                if not wallet_involved and tx.get("outputs"):
                    for out in tx["outputs"]:
                        if (
                            isinstance(out, dict)
                            and out.get("address") == wallet_address
                        ):
                            wallet_involved = True
                            break

                if wallet_involved:
                    # Formatar dados da transação para o frontend
                    token_symbol = "CLIM"  # Default
                    if tx.get("token_data") and tx["token_data"].get("symbol"):
                        token_symbol = tx["token_data"]["symbol"]

                    transactions.append(
                        {
                            "id": tx.get("tx_id", ""),
                            "type": tx.get("type", "unknown"),
                            "tokenSymbol": token_symbol,
                            "amount": (
                                tx.get("outputs", [{}])[0].get("value", 0)
                                if tx.get("outputs")
                                else 0
                            ),
                            "from": (
                                tx.get("inputs", [{}])[0].get("address", "system")
                                if tx.get("inputs")
                                else "system"
                            ),
                            "to": (
                                tx.get("outputs", [{}])[0].get(
                                    "address", wallet_address
                                )
                                if tx.get("outputs")
                                else wallet_address
                            ),
                            "timestamp": tx.get("timestamp", ""),
                            "status": tx.get("status", "confirmed"),
                            "value": (
                                tx.get("outputs", [{}])[0].get("value", 0)
                                if tx.get("outputs")
                                else 0
                            ),
                        }
                    )

        # Ordenar por timestamp (mais recente primeiro) e limitar
        transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        transactions = transactions[:limit]

        return {
            "wallet_address": wallet_address,
            "total_transactions": len(transactions),
            "transactions": transactions,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter transações da carteira: {str(e)}"
        )

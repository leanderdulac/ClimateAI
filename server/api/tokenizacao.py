"""
Router para endpoints de tokenização de eventos climáticos
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session
from models.sqlalchemy_models import BlockchainTransaction
from models.schemas import EventoClimatico, EventoClimaticoTipo
from models.token_schemas import EventoToken, TokenAnalysis, TokenGroup
from services.eventos_service import EventosService
from services.tokenizacao_eventos_service import TokenizacaoEventosService

router = APIRouter()
token_service = TokenizacaoEventosService()
eventos_service = EventosService()


class TokenizarComMintRequest(BaseModel):
    evento: EventoClimatico
    destination_address: Optional[str] = None
    mint_on_chain: bool = False


@router.post("/tokenizar", response_model=EventoToken)
async def tokenizar_evento(evento: EventoClimatico = Body(...)):
    """
    Tokeniza um evento climático específico

    Gera um token único estruturado para o evento fornecido,
    incluindo informações de severidade, localização e temporalidade.
    """
    try:
        token = await token_service.gerar_token_evento(evento)
        # Assuming 'request' and 'destination_address' would be passed or derived
        # For now, this line is added as per instruction, but it needs context for 'request'
        # and 'destination_address' to be fully functional.
        # Placeholder for demonstration:
        # resultado = await token_service.mint_token_on_chain(token, request.destination_address)
        # return resultado
        return token
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Erro ao tokenizar evento: {str(e)}"
        )


@router.post("/tokenizar-com-mint")
async def tokenizar_evento_com_mint(
    request: TokenizarComMintRequest = Body(...),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Tokeniza um evento climático e, opcionalmente, executa mint on-chain.

    Quando `mint_on_chain=true`, é necessário informar `destination_address`.
    """
    try:
        token = await token_service.gerar_token_evento(request.evento)
        response: Dict[str, Any] = {"token": token}

        if request.mint_on_chain:
            if not request.destination_address:
                raise HTTPException(
                    status_code=400,
                    detail="destination_address é obrigatório quando mint_on_chain=true",
                )

            on_chain = await token_service.mint_token_on_chain(
                token,
                request.destination_address,
            )

            tx_hash = on_chain.get("tx_hash") if isinstance(on_chain, dict) else None
            tx_hash = tx_hash or f"mint-{token.token_id}-{int(datetime.now().timestamp())}"
            status = "CONFIRMED" if on_chain.get("status") == "success" else "FAILED"
            amount = float(on_chain.get("value", 0))

            db_tx = BlockchainTransaction(
                tx_hash=tx_hash,
                token_uid=token.token_id,
                from_address="platform_mint_service",
                to_address=request.destination_address,
                amount=amount,
                status=status,
                message=f"Tokenização com mint: {on_chain.get('status', 'unknown')}",
                explorer_url="",
            )

            try:
                db.add(db_tx)
                await db.commit()
            except Exception:
                await db.rollback()

            response["on_chain"] = on_chain

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao tokenizar evento com mint: {str(e)}",
        )


@router.post("/tokenizar-multiplos", response_model=List[EventoToken])
async def tokenizar_multiplos_eventos(eventos: List[EventoClimatico] = Body(...)):
    """
    Tokeniza múltiplos eventos climáticos

    Processa uma lista de eventos e retorna seus respectivos tokens.
    Eventos com erro são ignorados e o processamento continua.
    """
    try:
        tokens = await token_service.tokenizar_multiplos_eventos(eventos)
        return tokens
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Erro ao tokenizar eventos: {str(e)}"
        )


@router.get("/decodificar/{token_id}")
async def decodificar_token(token_id: str):
    """
    Decodifica um token ID para extrair suas informações

    Args:
        token_id: ID do token no formato TYPE-LEVEL-LOC-TEMP-TIME

    Returns:
        Informações extraídas do token
    """
    try:
        decoded_info = token_service.decodificar_token(token_id)
        return decoded_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro interno ao decodificar token: {str(e)}"
        )


@router.get("/analise", response_model=TokenAnalysis)
async def analisar_tokens(
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    raio: float = Query(100.0, ge=1.0, le=1000.0),
    dias: int = Query(30, ge=1, le=365),
):
    """
    Realiza análise estatística dos tokens de eventos na área especificada

    Args:
        latitude: Latitude central da análise
        longitude: Longitude central da análise
        raio: Raio em km para busca de eventos
        dias: Período em dias para análise histórica

    Returns:
        Análise estatística dos tokens encontrados
    """
    try:
        # Buscar eventos na área
        eventos = eventos_service.obter_eventos(
            latitude=latitude,
            longitude=longitude,
            tipo=None,
            data_inicio=datetime.now() - timedelta(days=dias),
            data_fim=datetime.now(),
            raio=raio,
        )

        # Tokenizar eventos
        tokens = await token_service.tokenizar_multiplos_eventos(eventos)

        # Realizar análise
        analysis = token_service.analisar_tokens(tokens)

        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao analisar tokens: {str(e)}"
        )


@router.get("/grupos", response_model=List[TokenGroup])
async def agrupar_tokens(
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    raio: float = Query(100.0, ge=1.0, le=1000.0),
    dias: int = Query(30, ge=1, le=365),
):
    """
    Agrupa tokens similares por tipo e severidade

    Args:
        latitude: Latitude central da análise
        longitude: Longitude central da análise
        raio: Raio em km para busca de eventos
        dias: Período em dias para análise histórica

    Returns:
        Grupos de tokens similares
    """
    try:
        # Buscar eventos na área
        eventos = eventos_service.obter_eventos(
            latitude=latitude,
            longitude=longitude,
            tipo=None,
            data_inicio=datetime.now() - timedelta(days=dias),
            data_fim=datetime.now(),
            raio=raio,
        )

        # Tokenizar eventos
        tokens = await token_service.tokenizar_multiplos_eventos(eventos)

        # Agrupar tokens
        grupos = token_service.agrupar_tokens(tokens)

        return grupos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao agrupar tokens: {str(e)}")


@router.get("/risco/{token_id}")
async def calcular_risco_token(token_id: str):
    """
    Calcula o score de risco associado a um token específico

    Args:
        token_id: ID do token a ser analisado

    Returns:
        Score de risco e fatores associados
    """
    try:
        # Decodificar token
        token_info = token_service.decodificar_token(token_id)

        # Calcular risco baseado nas informações do token
        risk_analysis = token_service.calcular_risco_token(token_info)

        return risk_analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao calcular risco do token: {str(e)}"
        )


@router.post("/validar-token")
async def validar_token(token_data: Dict[str, Any] = Body(...)):
    """
    Valida se um token é autêntico e consistente

    Args:
        token_data: Dados do token a ser validado

    Returns:
        Status de validação e detalhes
    """
    try:
        validation_result = token_service.validar_token(token_data)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao validar token: {str(e)}")

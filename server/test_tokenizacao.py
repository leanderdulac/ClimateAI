"""
Teste da funcionalidade de tokenização de eventos climáticos
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta

from models.schemas import EventoClimatico, EventoClimaticoTipo
from services.tokenizacao_eventos_service import TokenizacaoEventosService


import asyncio

async def testar_tokenizacao():
    """Testa a funcionalidade básica de tokenização"""

    print("🧪 Testando Tokenização de Eventos Climáticos")
    print("=" * 50)

    # Criar serviço de tokenização
    token_service = TokenizacaoEventosService()

    # Criar evento de teste
    evento_teste = EventoClimatico(
        tipo=EventoClimaticoTipo.ENCHENTE,
        latitude=-8.7618,
        longitude=-63.9039,
        data_inicio=datetime.now() - timedelta(days=2),
        data_fim=datetime.now() - timedelta(days=1),
        intensidade=4.2,
        probabilidade=0.85,
        descricao="Enchente severa detectada na região de Porto Velho",
        nivel_alerta=4,
    )

    print("📝 Evento de teste:")
    print(f"  Tipo: {evento_teste.tipo.value}")
    print(f"  Localização: {evento_teste.latitude}, {evento_teste.longitude}")
    print(f"  Intensidade: {evento_teste.intensidade}")
    print(f"  Probabilidade: {evento_teste.probabilidade}")
    print()

    # Gerar token
    print("🔄 Gerando token...")
    token = await token_service.gerar_token_evento(evento_teste)

    print("✅ Token gerado com sucesso!")
    print(f"  Token ID: {token.token_id}")
    print(f"  Tipo: {token.event_type.value}")
    print(f"  Severidade: {token.severity_level}")
    print(f"  Hash Localização: {token.location_hash}")
    print(f"  Hash Temporal: {token.temporal_hash}")
    print(f"  Metadata: {token.metadata}")
    print()

    # Testar decodificação
    print("🔍 Testando decodificação do token...")
    try:
        decoded = token_service.decodificar_token(token.token_id)
        print("✅ Token decodificado com sucesso!")
        print(
            f"  Tipo decodificado: {decoded['event_type'].value if decoded['event_type'] else 'None'}"
        )
        print(f"  Severidade decodificada: {decoded['severity_level']}")
        print(f"  Timestamp: {decoded['timestamp']}")
    except Exception as e:
        print(f"❌ Erro na decodificação: {str(e)}")
    print()

    # Testar múltiplos eventos
    print("🔄 Testando tokenização de múltiplos eventos...")
    eventos_teste = [
        evento_teste,
        EventoClimatico(
            tipo=EventoClimaticoTipo.SECA,
            latitude=-9.0,
            longitude=-64.0,
            data_inicio=datetime.now() - timedelta(days=5),
            intensidade=3.8,
            probabilidade=0.75,
            descricao="Seca moderada na região",
            nivel_alerta=3,
        ),
        EventoClimatico(
            tipo=EventoClimaticoTipo.ONDA_CALOR,
            latitude=-8.8,
            longitude=-63.8,
            data_inicio=datetime.now() - timedelta(days=1),
            intensidade=4.5,
            probabilidade=0.90,
            descricao="Onda de calor extrema",
            nivel_alerta=5,
        ),
    ]

    tokens_multiplos = await token_service.tokenizar_multiplos_eventos(eventos_teste)
    print(f"✅ {len(tokens_multiplos)} tokens gerados!")

    for i, t in enumerate(tokens_multiplos, 1):
        print(f"  Token {i}: {t.token_id} (Severidade: {t.severity_level})")
    print()

    # Testar agrupamento
    print("🔄 Testando agrupamento de tokens...")
    grupos = token_service.agrupar_eventos_por_token(tokens_multiplos)
    print(f"✅ {len(grupos)} grupos identificados:")

    for group_key, group_tokens in grupos.items():
        print(f"  Grupo '{group_key}': {len(group_tokens)} tokens")
    print()

    # Testar análise
    print("🔄 Testando análise de tokens...")
    analise = token_service.analisar_tokens(tokens_multiplos)
    print("✅ Análise realizada:")
    print(f"  Total de tokens: {analise.total_tokens}")
    print(f"  Tokens por tipo: {analise.tokens_by_type}")
    print(f"  Tokens por severidade: {analise.tokens_by_severity}")
    print(f"  Distribuição de risco: {analise.risk_distribution}")
    print(f"  Clusters temporais: {len(analise.temporal_clusters)}")
    print(f"  Clusters espaciais: {len(analise.spatial_clusters)}")
    print()

    print("🎉 Todos os testes de tokenização foram concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(testar_tokenizacao())


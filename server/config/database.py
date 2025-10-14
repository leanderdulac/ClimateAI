"""
Configuração de Banco de Dados para ClimateAI
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import os

# Configurações do banco de dados - Temporariamente usando sync para resolver problema
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Usando engine síncrona temporariamente para resolver problema de driver
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as sync_sessionmaker

# Engine síncrona (temporária)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Session factory síncrona (temporária)
sync_session_maker = sync_sessionmaker(
    engine,
    expire_on_commit=False
)

# Mock das funções assíncronas para manter compatibilidade
async def get_db_session():
    """Mock assíncrono temporário"""
    # Retorna um gerador vazio para evitar erros
    return
    yield  # pragma: no cover

# Manter compatibilidade com código existente
async_session_maker = sync_session_maker

# Session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência para obter sessão de banco de dados
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Função para inicializar o banco (para desenvolvimento)
async def init_db():
    """
    Inicializa o banco de dados e cria tabelas
    """
    # TODO: Implementar criação de tabelas quando houver modelos SQLAlchemy
    pass


# Função para fechar conexões
async def close_db():
    """
    Fecha conexões do banco de dados
    """
    await engine.dispose()
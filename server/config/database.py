"""
Configuração de Banco de Dados para ClimateAI
"""

import os
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configurações do banco de dados
# DATABASE_URL será determinado dinamicamente ou via getenv

# Variáveis globais para o engine e session_maker
engine = None
async_session_maker = None


def _create_engine_and_session_maker(database_url: str):
    """Cria o engine e o session maker com base na URL do banco de dados."""
    global engine, async_session_maker

    is_postgres = database_url.startswith("postgresql")

    if is_postgres:
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
        )
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    else:
        # SQLite async setup (development)
        # Ensure aiosqlite driver is used for async SQLite
        engine = create_async_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # Use StaticPool for in-memory SQLite
        )
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência para obter sessão de banco de dados
    """
    # Garante que o engine e o session_maker foram inicializados
    if engine is None or async_session_maker is None:
        # Em ambiente de teste, o DATABASE_URL é definido em conftest.py
        # Em produção, ele vem do ambiente
        current_db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        print(f"DEBUG: current_db_url in get_db_session: {current_db_url}")
        _create_engine_and_session_maker(current_db_url)

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
    # Garante que o engine e o session_maker foram inicializados
    if engine is None or async_session_maker is None:
        current_db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        print(f"DEBUG: current_db_url in get_db_session: {current_db_url}")
        _create_engine_and_session_maker(current_db_url)

    # TODO: Implementar criação de tabelas quando houver modelos SQLAlchemy
    pass


# Função para fechar conexões
async def close_db():
    """
    Fecha conexões do banco de dados
    """
    if engine:
        await engine.dispose()

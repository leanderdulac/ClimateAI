"""
Configuração de Banco de Dados para ClimateAI
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator
import os

# Configurações do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Detect database type
is_postgres = DATABASE_URL.startswith("postgresql")

if is_postgres:
    # PostgreSQL async setup
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
    )
    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
else:
    # SQLite setup (development)
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    # For SQLite, use sync session maker wrapped as async
    sync_session_maker = sessionmaker(
        engine,
        expire_on_commit=False
    )
    async_session_maker = sync_session_maker


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
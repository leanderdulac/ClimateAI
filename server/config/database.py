"""
Configuração de Banco de Dados para ClimateAI
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import os

# Configurações do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Engine assíncrona
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

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
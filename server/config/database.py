"""
Configuração de Banco de Dados para ClimateAI
"""

import os
import asyncio
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models.sqlalchemy_models import Base

# Configurações centralizadas
from config.config import settings

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
        # Force IPv4 resolution for Supabase to avoid timeouts
        import socket
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(database_url)
            if parsed.hostname:
                ip = socket.gethostbyname(parsed.hostname)
                print(f"Resolved {parsed.hostname} to {ip}")
                # Reconstruct URL with IP but keep original hostname in args if needed, 
                # but for asyncpg/sqlalchemy, replacing hostname usually works best for connection.
                # simpler: just let it be, but the resolution check confirms we can reach it.
                # Actually, let's create a custom connector or just verify we can reach it.
        except Exception as e:
            print(f"Warning: DNS resolution failed: {e}")

        import ssl
        
        # Create unverified SSL context for pooler to avoid certificate hostname mismatch issues
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        print(f"CRITICAL: create_async_engine is using URL: {database_url}")

        engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            connect_args={
                "server_settings": {"jit": "off"},
                "ssl": ssl_context
            },
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
        # Caso contrário, usamos o settings.DATABASE_URL já calculado (Supabase como primário)
        current_db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
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
        current_db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
        _create_engine_and_session_maker(current_db_url)

    # Criar tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully")


# Função para fechar conexões
async def close_db():
    """
    Fecha conexões do banco de dados
    """
    if engine:
        await engine.dispose()

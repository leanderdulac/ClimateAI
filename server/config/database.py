"""
Configuração de Banco de Dados para ClimateWise
"""

import os
import asyncio
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
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
        # Assuming .env provides the correct IPv4 pooler url directly

        # Only use SSL for remote PostgreSQL connections (e.g., Supabase pooler).
        # Local connections (localhost) in CI/test environments don't support SSL.
        is_localhost = "localhost" in database_url or "127.0.0.1" in database_url
        use_ssl = not is_localhost

        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "server_settings": {
                "prepared_statement_cache_size": "0"
            }
        }

        if use_ssl:
            import ssl
            # Create unverified SSL context for pooler to avoid certificate hostname mismatch issues
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ssl_context


        # Adiciona parâmetro para pgbouncer/asyncpg
        if "asyncpg" in database_url:
            separator = "&" if "?" in database_url else "?"
            if "prepared_statement_cache_size" not in database_url:
                database_url += f"{separator}prepared_statement_cache_size=0"
            separator = "&"
            if "statement_cache_size" not in database_url:
                database_url += f"{separator}statement_cache_size=0"


        # Use NullPool in production to avoid PgBouncer connection limit issues
        # and ensure every request gets a fresh connection from the pooler.
        pool_class = NullPool if os.getenv("ENVIRONMENT") == "production" else None
        
        engine_kwargs = {
            "pool_pre_ping": True,
            "connect_args": connect_args,
        }
        
        if pool_class:
            engine_kwargs["poolclass"] = pool_class
        else:
            engine_kwargs["pool_size"] = getattr(settings, "DB_POOL_SIZE", 10)
            engine_kwargs["max_overflow"] = getattr(settings, "DB_MAX_OVERFLOW", 20)
            engine_kwargs["pool_recycle"] = 3600

        engine = create_async_engine(
            database_url,
            **engine_kwargs
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
        # Se DATABASE_ENABLED for false, usamos sempre o sqlite local
        database_enabled = os.getenv("DATABASE_ENABLED", "true").lower() == "true"
        current_db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
        if not database_enabled:
            current_db_url = "sqlite+aiosqlite:///test.db"
            
        if current_db_url and "?sslmode=require" in current_db_url:
            current_db_url = current_db_url.replace("?sslmode=require", "")
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
        # Se DATABASE_ENABLED for false, usamos sempre o sqlite local
        database_enabled = os.getenv("DATABASE_ENABLED", "true").lower() == "true"
        current_db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
        if not database_enabled:
            current_db_url = "sqlite+aiosqlite:///local_dev.db"
            
        if current_db_url and "?sslmode=require" in current_db_url:
            current_db_url = current_db_url.replace("?sslmode=require", "")
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

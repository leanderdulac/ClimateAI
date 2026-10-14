"""
Configuração de Banco de Dados para ClimateWise
"""

import os
import ssl
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from models.sqlalchemy_models import Base

# Official Supabase root CA (prod-ca-2021). System CAs do not include this, so
# verify-full against *.pooler.supabase.com fails with
# "self-signed certificate in certificate chain" unless we load it.
# Source: https://supabase.com/docs/guides/platform/ssl-enforcement
# Official file: https://supabase-downloads.s3-ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt
BUNDLED_SUPABASE_CA_PATH = Path(__file__).resolve().parent / "certs" / "prod-ca-2021.crt"


def resolve_postgres_ssl_root_cert(
    root_cert: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Return (cafile, cadata) for an extra CA on top of system trust.

    ``DB_SSL_ROOT_CERT`` may be a filesystem path or a PEM blob. When unset,
    the bundled Supabase ``prod-ca-2021.crt`` is used.
    """
    override = root_cert if root_cert is not None else os.getenv("DB_SSL_ROOT_CERT")
    if override is not None and override.strip():
        value = override.strip()
        if "-----BEGIN" in value:
            return None, value
        path = Path(value).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"DB_SSL_ROOT_CERT file not found: {path}")
        return str(path), None

    if BUNDLED_SUPABASE_CA_PATH.is_file():
        return str(BUNDLED_SUPABASE_CA_PATH), None
    return None, None


def build_postgres_ssl_context(
    *,
    is_localhost: bool,
    environment: Optional[str] = None,
    insecure_override: Optional[bool] = None,
    root_cert: Optional[str] = None,
) -> Optional[ssl.SSLContext]:
    """Build an SSL context for remote Postgres. Localhost stays unencrypted.

    Verified contexts load the system CA store plus the bundled Supabase root
    CA (or ``DB_SSL_ROOT_CERT`` path/PEM override). Hostname checks stay on.
    """
    if is_localhost:
        return None

    env_name = (environment or os.getenv("ENVIRONMENT", "development")).lower()
    if insecure_override is None:
        insecure_override = os.getenv("DB_SSL_INSECURE", "false").lower() == "true"

    if insecure_override:
        if env_name == "production":
            raise ValueError("DB_SSL_INSECURE is not allowed when ENVIRONMENT=production")
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    # System CAs first, then the extra root (Supabase or operator override).
    ssl_context = ssl.create_default_context()
    cafile, cadata = resolve_postgres_ssl_root_cert(root_cert)
    if cafile or cadata:
        ssl_context.load_verify_locations(cafile=cafile, cadata=cadata)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = True
    return ssl_context

# Configurações centralizadas
from config.config import settings

# Configurações do banco de dados
# DATABASE_URL será determinado dinamicamente ou via getenv

# Variáveis globais para o engine e session_maker
engine = None
async_session_maker = None


def _url_has_query_param(database_url: str, name: str) -> bool:
    query = database_url.split("?", 1)[1] if "?" in database_url else ""
    return any(part.startswith(name + "=") for part in query.split("&") if part)


def apply_asyncpg_pgbouncer_settings(database_url: str) -> tuple[str, dict]:
    """Disable asyncpg prepared-statement caches (PgBouncer transaction pooler, port 6543)."""
    is_localhost = "localhost" in database_url or "127.0.0.1" in database_url
    is_pooler = ":6543" in database_url
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }
    # server_settings is accepted by PgBouncer; skip on local non-pooler Postgres.
    if not is_localhost or is_pooler:
        connect_args["server_settings"] = {
            "prepared_statement_cache_size": "0"
        }

    if "asyncpg" in database_url:
        for param in ("prepared_statement_cache_size", "statement_cache_size"):
            if not _url_has_query_param(database_url, param):
                separator = "&" if "?" in database_url else "?"
                database_url += f"{separator}{param}=0"

    return database_url, connect_args


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

        database_url, connect_args = apply_asyncpg_pgbouncer_settings(database_url)

        if use_ssl:
            ssl_context = build_postgres_ssl_context(is_localhost=is_localhost)
            if ssl_context is not None:
                connect_args["ssl"] = ssl_context

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
    database_enabled = os.getenv("DATABASE_ENABLED", "true").lower() == "true"
    current_db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
    if not database_enabled:
        current_db_url = "sqlite+aiosqlite:///local_dev.db"
    if current_db_url and "?sslmode=require" in current_db_url:
        current_db_url = current_db_url.replace("?sslmode=require", "")

    if engine is None or async_session_maker is None:
        _create_engine_and_session_maker(current_db_url)

    environment = (settings.ENVIRONMENT or os.getenv("ENVIRONMENT", "development")).lower()
    if environment == "production":
        await asyncio.to_thread(run_alembic_upgrade, current_db_url)
        print("Database migrations applied successfully")

    # create_all is additive (checkfirst). It covers models added before the
    # matching Alembic revision is applied — e.g. local sqlite files.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully")


def _sync_database_url(database_url: str) -> str:
    from config.db_url import to_sync_database_url

    return to_sync_database_url(database_url)


def run_alembic_upgrade(database_url: str) -> None:
    """Apply Alembic migrations using a sync driver URL."""
    from alembic import command
    from alembic.config import Config
    from config.db_url import escape_alembic_config_url

    server_dir = Path(__file__).resolve().parent.parent
    cfg = Config(str(server_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(server_dir / "alembic"))
    cfg.set_main_option(
        "sqlalchemy.url",
        escape_alembic_config_url(_sync_database_url(database_url)),
    )
    command.upgrade(cfg, "head")


# Função para fechar conexões
async def close_db():
    """
    Fecha conexões do banco de dados
    """
    if engine:
        await engine.dispose()

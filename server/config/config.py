"""
Configurações do Framework Integrado de Modelagem Climático-Econômica (FIMCE)
"""

from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Configurações do servidor
    HOST: str = "localhost"
    PORT: int = 8000
    DEBUG: bool = False  # Production default
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    SECRET_KEY: str = ""  # Must be set via environment variables
    ALLOW_ORIGINS_INPUT: str = (
        "http://localhost:3000,http://localhost:5173"  # Input as string from env
    )

    # We'll compute this property based on the input
    @property
    def ALLOW_ORIGINS(self) -> List[str]:
        """Parse ALLOW_ORIGINS from the input string."""
        if self.ALLOW_ORIGINS_INPUT:
            # Split by comma and strip whitespace
            return [
                origin.strip()
                for origin in self.ALLOW_ORIGINS_INPUT.split(",")
                if origin.strip()
            ]
        return ["http://localhost:3000", "http://localhost:5173"]

    # Configurações de API
    EMBRAPA_API_KEY: Optional[str] = None
    EMBRAPA_API_URL: Optional[str] = None
    EMBRAPA_API_VERSION: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENMETEO_API_KEY: Optional[str] = None

    # Configurações OpenMeteo
    OPENMETEO_CACHE_DIR: str = ".cache"
    OPENMETEO_CACHE_TIMEOUT: int = 3600  # 1 hora

    # Configurações de geocodificação
    GEOCODING_CACHE_TIMEOUT: int = 86400  # 24 horas
    GEOCODING_MAX_RETRIES: int = 3

    # Configurações de cache
    REDIS_ENABLED: bool = False
    REDIS_URL: Optional[str] = None

    # Configurações de banco de dados
    DATABASE_ENABLED: bool = True
    DATABASE_URL: str = (
        "postgresql+asyncpg://climateai:climateai123@localhost/climateai"
    )

    # Configurações de produção (adicionadas para compatibilidade)
    DB_PASSWORD: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    DOMAIN: Optional[str] = None
    PROMETHEUS_METRICS_ENABLED: bool = False
    GRAFANA_ADMIN_PASSWORD: Optional[str] = None

    # Configurações adicionais
    ENVIRONMENT: str = "development"
    MAX_FILE_SIZE: int = 10485760
    ALLOWED_FILE_EXTENSIONS: str = "csv,json,xlsx,pdf"
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    # Configurações Blockchain
    BLOCKCHAIN_ENABLED: bool = False
    BC_NODE_URL: Optional[str] = None
    ADMIN_WALLET_ADDRESS: Optional[str] = None
    MIN_BALANCE_THRESHOLD_ETHER: float = 0.05  # 0.05 ETH como um limite razoável para testes/operação

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Validação de segurança obrigatória
if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
    import warnings

    warnings.warn(
        "⚠️  SECRET_KEY não está definido ou é muito curto! "
        "Use: export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')",
        RuntimeWarning,
    )
    # Em produção (DEBUG=False), falhar
    if not settings.DEBUG:
        raise ValueError(
            "SECRET_KEY must be set in environment variables and be at least 32 characters"
        )

# Validar CORS
if not settings.ALLOW_ORIGINS or settings.ALLOW_ORIGINS == []:
    import warnings

    warnings.warn(
        "⚠️  ALLOW_ORIGINS está vazio. Configure via ALLOW_ORIGINS env var",
        RuntimeWarning,
    )

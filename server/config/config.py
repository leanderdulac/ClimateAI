"""
Configurações do Framework Integrado de Modelagem Climático-Econômica (FIMCE)
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Configurações do servidor
    HOST: str = "localhost"
    PORT: int = 8000
    DEBUG: bool = False  # Production default
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    SECRET_KEY: str = "changeme123"  # Should be set via environment in production
    ALLOW_ORIGINS: list = []  # Restrictive default for production
    
    # Configurações de API
    EMBRAPA_API_KEY: Optional[str] = None
    EMBRAPA_API_URL: Optional[str] = None
    EMBRAPA_API_VERSION: Optional[str] = None
    
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
    DATABASE_URL: str = "postgresql+asyncpg://climateai:climateai123@localhost/climateai"
    
    # Configurações de produção (adicionadas para compatibilidade)
    DB_PASSWORD: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    DOMAIN: Optional[str] = None
    PROMETHEUS_METRICS_ENABLED: bool = False
    GRAFANA_ADMIN_PASSWORD: Optional[str] = None
    OPENMETEO_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = Settings()
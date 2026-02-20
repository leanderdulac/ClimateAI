"""
Configurações do Framework Integrado de Modelagem Climático-Econômica (FIMCE)
"""

import os
import secrets
import sys
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# IMPORTANTE: Carregar as variáveis de ambiente base antes de inicializar as configurações
# para que os valores padrão do Pydantic possam ser lidos do ambiente.
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=env_path)

# Carregar arquivo de configuração local se existir (para o servidor especificamente)
local_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(local_env_path):
    load_dotenv(dotenv_path=local_env_path, override=True)


def generate_secret_key() -> str:
    """Gera uma SECRET_KEY segura se não existir"""
    return secrets.token_urlsafe(32)


class Settings(BaseSettings):
    # Configurações do servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # SECRET_KEY: Usar do .env ou gerar automaticamente
    SECRET_KEY: str = os.getenv("SECRET_KEY") or generate_secret_key()
    
    ALLOW_ORIGINS_INPUT: str = os.getenv(
        "ALLOW_ORIGINS", 
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    )

    # We'll compute this property based on the input
    @property
    def ALLOW_ORIGINS(self) -> List[str]:
        """Parse ALLOW_ORIGINS from the input string."""
        if self.ALLOW_ORIGINS_INPUT and self.ALLOW_ORIGINS_INPUT.strip():
            # Split by comma and strip whitespace
            origins = [
                origin.strip()
                for origin in self.ALLOW_ORIGINS_INPUT.split(",")
                if origin.strip()
            ]
            return origins if origins else ["http://localhost:3000", "http://localhost:5173"]
        return ["http://localhost:3000", "http://localhost:5173"]

    # Configurações de API
    EMBRAPA_API_KEY: Optional[str] = os.getenv("EMBRAPA_API_KEY")
    EMBRAPA_API_URL: str = os.getenv("EMBRAPA_API_URL", "https://api.cnptia.embrapa.br")
    EMBRAPA_API_VERSION: str = os.getenv("EMBRAPA_API_VERSION", "climapi/v1")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GROK_API_KEY: Optional[str] = os.getenv("GROK_API_KEY")
    OPENMETEO_API_KEY: Optional[str] = os.getenv("OPENMETEO_API_KEY")
    NOAA_API_KEY: Optional[str] = os.getenv("NOAA_API_KEY")

    # Configurações OpenMeteo
    OPENMETEO_CACHE_DIR: str = ".cache"
    OPENMETEO_CACHE_TIMEOUT: int = 3600  # 1 hora

    # Configurações de geocodificação
    GEOCODING_CACHE_TIMEOUT: int = 86400  # 24 horas
    GEOCODING_MAX_RETRIES: int = 3

    # Configurações de cache
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # ==============================================
    # Banco de Dados (Supabase como fonte primária)
    # ==============================================
    DATABASE_ENABLED: bool = os.getenv("DATABASE_ENABLED", "true").lower() == "true"

    # Se SUPABASE_DB_URL estiver definido, priorizamos ele como DATABASE_URL.
    # Caso contrário, tentamos construir a URL a partir dos componentes padrão
    # do Supabase (host db.<project>.supabase.co e usuário postgres).
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")
    SUPABASE_DB_HOST: str = os.getenv("SUPABASE_DB_HOST", "")
    SUPABASE_DB_PORT: str = os.getenv("SUPABASE_DB_PORT", "5432")
    SUPABASE_DB_NAME: str = os.getenv("SUPABASE_DB_NAME", "postgres")
    SUPABASE_DB_USER: str = os.getenv("SUPABASE_DB_USER", "postgres")
    SUPABASE_DB_PASSWORD: str = os.getenv("SUPABASE_DB_PASSWORD", "")

    def _build_supabase_database_url(self) -> Optional[str]:
        """Gera a DATABASE_URL para Supabase se as variáveis existirem."""
        # Prioriza uma URL completa caso fornecida
        if self.SUPABASE_DB_URL:
            return self.SUPABASE_DB_URL

        # Constrói a URL apenas se host e senha estiverem presentes
        if self.SUPABASE_DB_HOST and self.SUPABASE_DB_PASSWORD:
            return (
                f"postgresql+asyncpg://{self.SUPABASE_DB_USER}:"
                f"{self.SUPABASE_DB_PASSWORD}@{self.SUPABASE_DB_HOST}:"
                f"{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}?sslmode=require"
            )

        return None

    # DATABASE_URL final: calculada em tempo de execução
    DATABASE_URL: Optional[str] = None

    def __init__(self, **values):
        super().__init__(**values)
        # Calcula DATABASE_URL em tempo de inicialização
        # Se DATABASE_URL estiver explicitamente no .env, use-o (para preservar ?sslmode=require)
        if not self.DATABASE_URL:
            self.DATABASE_URL = os.getenv("DATABASE_URL")
            
        if not self.DATABASE_URL:
            supabase_url = self._build_supabase_database_url()
            if supabase_url:
                self.DATABASE_URL = supabase_url
            else:
                self.DATABASE_URL = "postgresql+asyncpg://climateai:climateai123@localhost:5432/climateai"

    # Configurações de produção
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD")
    DOMAIN: Optional[str] = os.getenv("DOMAIN")
    PROMETHEUS_METRICS_ENABLED: bool = os.getenv("PROMETHEUS_METRICS_ENABLED", "false").lower() == "true"
    GRAFANA_ADMIN_PASSWORD: Optional[str] = os.getenv("GRAFANA_ADMIN_PASSWORD")

    # OpenTelemetry
    OTEL_ENABLED: bool = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "climateai-backend")
    OTEL_SERVICE_VERSION: str = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")

    # Configurações adicionais
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    ALLOWED_FILE_EXTENSIONS: str = os.getenv("ALLOWED_FILE_EXTENSIONS", "csv,json,xlsx,pdf")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")

    # Configurações Blockchain
    BLOCKCHAIN_ENABLED: bool = os.getenv("BLOCKCHAIN_ENABLED", "false").lower() == "true"
    BC_NODE_URL: Optional[str] = os.getenv("BC_NODE_URL")
    ADMIN_WALLET_ADDRESS: Optional[str] = os.getenv("ADMIN_WALLET_ADDRESS")
    MIN_BALANCE_THRESHOLD_ETHER: float = float(os.getenv("MIN_BALANCE_THRESHOLD_ETHER", "0.05"))

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True


# Criar instância das configurações
settings = Settings()

# Validação CRÍTICA de segurança em produção
if not settings.DEBUG:
    # Em produção, SECRET_KEY deve estar configurada
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        print("❌ ERRO CRÍTICO: SECRET_KEY não está definida ou é muito curta!", file=sys.stderr)
        print("Em produção, defina no .env:", file=sys.stderr)
        print("  SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')", file=sys.stderr)
        sys.exit(1)
    
    # Em produção, validar CORS
    if "*" in settings.ALLOW_ORIGINS:
        print("⚠️  AVISO: CORS está aberto (*) em produção. Isso é um risco de segurança!", file=sys.stderr)
    
    # Validar DATABASE_URL em produção
    if "localhost" in settings.DATABASE_URL:
        print("⚠️  AVISO: DATABASE_URL aponta para localhost em produção!", file=sys.stderr)
else:
    # Em desenvolvimento, apenas avisar
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        print("⚠️  AVISO: SECRET_KEY gerada automaticamente. Em produção, defina explicitamente.", file=sys.stderr)
        print(f"   SECRET_KEY atual: {settings.SECRET_KEY[:10]}...", file=sys.stderr)

# Validar CORS
if not settings.ALLOW_ORIGINS:
    print("⚠️  AVISO: ALLOW_ORIGINS está vazio. Usando padrão localhost.", file=sys.stderr)

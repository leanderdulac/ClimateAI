"""
Configurações do Framework Integrado de Modelagem Climático-Econômica (FIMCE)
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Configurações do servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Configurações de API
    METEOBLUE_API_KEY: Optional[str] = None
    OPENWEATHER_API_KEY: Optional[str] = None
    YAHOO_FINANCE_ENABLED: bool = True
    
    # Configurações de banco de dados
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/fimce"
    
    # Configurações de cache
    REDIS_URL: str = "redis://localhost:6379"
    
    # Configurações de modelos
    MODEL_PATH: str = "./models"
    
    class Config:
        env_file = ".env"


settings = Settings()
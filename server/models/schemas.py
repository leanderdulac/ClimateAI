"""
Modelos de dados para o Framework Integrado de Modelagem Climático-Econômica (FIMCE)
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ClimaTipo(str, Enum):
    TEMPERATURA = "temperatura"
    PRECIPITACAO = "precipitacao"
    UMIDADE = "umidade"
    VENTO = "vento"
    PRESSAO = "pressao"


class EventoClimaticoTipo(str, Enum):
    SECA = "seca"
    ENCHENTE = "enchente"
    ONDA_CALOR = "onda_calor"
    GEADA = "geada"
    SECA_FLASH = "seca_flash"


class ClimaData(BaseModel):
    """Modelo para dados climáticos"""
    latitude: float
    longitude: float
    data: datetime
    temperatura: Optional[float] = None
    precipitacao: Optional[float] = None
    umidade: Optional[float] = None
    vento_velocidade: Optional[float] = None
    vento_direcao: Optional[float] = None
    pressao: Optional[float] = None
    indice_spi: Optional[float] = None  # Standardized Precipitation Index
    fonte: Optional[str] = None


class PrevisaoClima(BaseModel):
    """Modelo para previsões climáticas"""
    latitude: float
    longitude: float
    data_inicio: datetime
    data_fim: datetime
    variaveis: List[ClimaData]
    metodo: str
    confianca: float


class EventoClimatico(BaseModel):
    """Modelo para eventos climáticos extremos"""
    tipo: EventoClimaticoTipo
    latitude: float
    longitude: float
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    intensidade: float
    probabilidade: float
    descricao: str
    nivel_alerta: int  # 1-5, sendo 5 o mais grave


class PrevisaoPreco(BaseModel):
    """Modelo para previsões de preços de commodities"""
    simbolo: str
    descricao: str
    data_referencia: datetime
    preco_atual: float
    preco_previsto: float
    variacao_prevista: float
    confianca: float
    fatores_climaticos: List[Dict[str, Any]]


class Alerta(BaseModel):
    """Modelo para alertas do sistema"""
    id: str
    tipo: str
    titulo: str
    descricao: str
    nivel: int  # 1-5, sendo 5 o mais crítico
    localizacao: Optional[Dict[str, float]] = None
    data_criacao: datetime
    data_validade: Optional[datetime] = None
    lido: bool = False
"""
Modelos de dados para o Framework Integrado de Modelagem Climático-Econômica (FIMCE)
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    USER = "user"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class UserBase(BaseModel):
    """Modelo base para usuário"""
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    organization: Optional[str] = None


class UserCreate(UserBase):
    """Modelo para criação de usuário"""
    password: str


class UserUpdate(BaseModel):
    """Modelo para atualização de usuário"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    organization: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    """Modelo completo de usuário"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Modelo para tokens JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class TokenData(BaseModel):
    """Modelo para dados extraídos do token"""
    user_id: str
    email: str
    role: UserRole
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Modelo para requisição de login"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Modelo para requisição de refresh token"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Modelo para requisição de reset de senha"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Modelo para confirmação de reset de senha"""
    token: str
    new_password: str


class UserPermissions(BaseModel):
    """Modelo para permissões do usuário"""
    can_access_climate_data: bool = True
    can_access_pricing_models: bool = False
    can_access_audit_logs: bool = False
    can_manage_users: bool = False
    can_access_admin_panel: bool = False
    api_rate_limit: int = 100  # requests per hour


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
    probabilidade_precipitacao: Optional[float] = None
    umidade: Optional[float] = None
    vento_velocidade: Optional[float] = None
    vento_rajada: Optional[float] = None
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
    probabilidade_precipitacao: Optional[float] = None
    umidade: Optional[float] = None
    vento_velocidade: Optional[float] = None
    vento_rajada: Optional[float] = None
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
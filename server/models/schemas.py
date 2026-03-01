"""
Modelos de dados para o Framework Integrado de Modelagem Climático-Econômica (FIMCE)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, EmailStr


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


# ============================================================
# Atlas Digital de Desastres - Schemas
# ============================================================

class AtlasDisasterType(str, Enum):
    """Tipos de desastres naturais"""
    INUNDACAO = "inundacao"
    SECA = "seca"
    DESLIZAMENTO = "deslizamento"
    GRANIZO = "granizo"
    VENDAVA = "vendaval"
    INCENDIO = "incendio"
    GEADA = "geada"
    ALUVIAO = "aluviao"
    OUTRO = "outro"


class AtlasDisasterSeverity(str, Enum):
    """Níveis de severidade de desastres"""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    MUITO_ALTA = "muito_alta"


class AtlasDisasterRecord(BaseModel):
    """Registro individual de desastre do Atlas"""
    record_id: str
    ano: int
    uf: str
    municipio: str
    codigo_municipio: Optional[str] = None
    tipo_desastre: str
    subtipo_desastre: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    intensidade: Optional[str] = None
    mortes_diretas: int = 0
    mortes_indiretas: int = 0
    feridos: int = 0
    desabrigados: int = 0
    desalojados: int = 0
    afetados: int = 0
    prejuizo_estimado: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AtlasDisasterAggregation(BaseModel):
    """Agregação de dados do Atlas"""
    grupo: Dict[str, Any]
    qtd_ocorrencias: int
    total_mortes: int
    total_afetados: int
    total_prejuizo: float
    municipios_atingidos: List[str] = []
    anos_ocorrencia: List[int] = []


class AtlasStatistics(BaseModel):
    """Estatísticas do Atlas"""
    total_registros: int
    periodo: Dict[str, Any]
    uf: Dict[str, Any]
    tipos_desastre: Dict[str, Any]
    impacto: Dict[str, Any]


class AtlasFilterRequest(BaseModel):
    """Filtros para dados do Atlas"""
    anos: Optional[Tuple[int, int]] = None
    uf: Optional[str] = None
    municipio: Optional[str] = None
    tipo_desastre: Optional[str] = None
    intensidade: Optional[str] = None
    min_afetados: Optional[int] = None
    min_mortes: Optional[int] = None


class AtlasDownloadRequest(BaseModel):
    """Requisição para download de dados do Atlas"""
    url: str
    filename: Optional[str] = None
    force: bool = False


class AtlasDataStatus(BaseModel):
    """Status dos dados do Atlas"""
    arquivo_carregado: Optional[str] = None
    total_registros: int = 0
    cache_timestamp: Optional[str] = None
    data_dir: str

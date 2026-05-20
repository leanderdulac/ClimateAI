from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Float, Integer, ForeignKey, Date, JSON, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.schema import MetaData
from sqlalchemy.ext.declarative import declarative_base

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)

Base = declarative_base(metadata=metadata)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    role = Column(String, default="user")  # Assuming role is a string for simplicity

    # Add any other fields that might be expected by the Pydantic User model
    # For example, if 'organization' is expected in the Pydantic model, add it here
    organization = Column(String, nullable=True)
    partner_id = Column(String, ForeignKey("partners.id"), nullable=True)


    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, ForeignKey("partners.id"), nullable=True) # Location belongs to partner?
    name = Column(String, nullable=False)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)



class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, ForeignKey("partners.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=True)
    
    policy_number = Column(String, unique=True, nullable=False)
    policy_type = Column(String, nullable=False)
    status = Column(String, default="draft")
    
    coverage_amount = Column(DECIMAL(15, 2), nullable=False)
    premium = Column(DECIMAL(15, 2), nullable=False)
    
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    
    # New columns for Parametric Trigger
    trigger_conditions = Column(JSON, default={})
    payout_structure = Column(JSON, default={})
    
    # Detailed Risk Factors (Geo, Space, News, etc)
    risk_factors = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships (optional for now, but good practice)
    # claims = relationship("Claim", back_populates="policy")

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    
    claim_number = Column(String, unique=True, nullable=False)
    claim_type = Column(String, nullable=False)
    status = Column(String, default="reported")
    
    event_date = Column(Date, nullable=False)
    event_description = Column(Text)
    
    claimed_amount = Column(DECIMAL(15, 2), nullable=False)
    approved_amount = Column(DECIMAL(15, 2))
    paid_amount = Column(DECIMAL(15, 2))
    
    weather_data = Column(JSON, default={}) # To store trigger evidence
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ClimateData(Base):
    __tablename__ = "climate_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id = Column(String, ForeignKey("locations.id"), nullable=True)
    
    recorded_date = Column(Date, nullable=False)
    
    temperature_avg = Column(DECIMAL(5, 2))
    temperature_max = Column(DECIMAL(5, 2))
    precipitation = Column(DECIMAL(8, 2))
    
    source = Column(String, default='openmeteo')
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # partner = relationship("Partner") # Add relationship later


class ClimateEnsoSignal(Base):
    """Persistent ENSO signal snapshot used by ClimateWise pricing/risk services."""

    __tablename__ = "climate_enso_signals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_date = Column(Date, nullable=False, index=True)

    roni = Column(Float)
    oni = Column(Float)
    soi = Column(Float)
    olr = Column(Float)

    nino12 = Column(Float)
    nino3 = Column(Float)
    nino34 = Column(Float)
    nino4 = Column(Float)

    regime_label = Column(String(32), index=True)
    regime_confidence = Column(String(16), index=True)
    provisional_flag = Column(Boolean, default=False)

    source_url = Column(String)
    ingestion_timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    enso_score = Column(Float)
    p_el_nino = Column(Float)
    p_la_nina = Column(Float)
    p_neutral = Column(Float)
    coupling_score = Column(Float)
    transition_score = Column(Float)
    impact_risk_modifier = Column(Float)

    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Partner(Base):
    __tablename__ = "partners"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False) # e.g. "acme-coop"
    
    # Metadata
    contact_email = Column(String)
    api_enabled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, ForeignKey("partners.id"), nullable=False)
    
    key_hash = Column(String, unique=True, nullable=False) # Store hashed key
    prefix = Column(String, nullable=False) # To show "sk_live_123..."
    name = Column(String) # e.g. "Backend Integration"
    
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # partner = relationship("Partner", back_populates="api_keys")


class QuoteJourneyEvent(Base):
    """Persistent quote journey events for audit and analytics."""

    __tablename__ = "quote_journey_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)

    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)

    quote_premium = Column(Float, nullable=True)
    quote_coverage_period = Column(Integer, nullable=True)
    quote_frequency = Column(Float, nullable=True)
    quote_severity = Column(Float, nullable=True)
    quote_event_id = Column(String, nullable=True)
    quote_status = Column(String, nullable=True)

    payload = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# ATLAS DIGITAL DE DESASTRES - Modelos
# ============================================================

class AtlasDisaster(Base):
    """
    Modelo para registros do Atlas Digital de Desastres Naturais
    Tabela: atlas_disasters
    """
    __tablename__ = "atlas_disasters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identificação
    record_id_original = Column(String, index=True)  # ID original do arquivo
    ano = Column(Integer, nullable=False, index=True)
    
    # Localização
    uf = Column(String(2), nullable=False, index=True)
    municipio = Column(String(100), nullable=False, index=True)
    codigo_municipio = Column(String(7), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Tipo de desastre
    tipo_desastre = Column(String(50), nullable=False, index=True)
    subtipo_desastre = Column(String(100))
    intensidade = Column(String(20), index=True)
    
    # Datas
    data_inicio = Column(Date)
    data_fim = Column(Date)
    
    # Impacto humano
    mortes_diretas = Column(Integer, default=0)
    mortes_indiretas = Column(Integer, default=0)
    feridos = Column(Integer, default=0)
    desabrigados = Column(Integer, default=0)
    desalojados = Column(Integer, default=0)
    afetados = Column(Integer, default=0)
    
    # Impacto econômico
    prejuizo_estimado = Column(DECIMAL(15, 2))
    
    # Metadados
    fonte = Column(String(100), default="Atlas Digital MDR")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AtlasDisaster(id='{self.id}', municipio='{self.municipio}', ano={self.ano})>"


class AtlasMunicipioGeocode(Base):
    """
    Modelo para geocodificação de municípios
    Tabela: atlas_municipios_geocode
    
    Armazena coordenadas e informações geográficas dos municípios
    para permitir visualizações em mapa e análises espaciais.
    """
    __tablename__ = "atlas_municipios_geocode"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identificação
    codigo_municipio_ibge = Column(String(7), unique=True, nullable=False, index=True)
    municipio = Column(String(100), nullable=False)
    uf = Column(String(2), nullable=False, index=True)
    
    # Coordenadas
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Informações adicionais
    populacao = Column(Integer)
    area_km2 = Column(Float)
    regiao = Column(String(20))  # Norte, Nordeste, etc.
    mesorregiao = Column(String(100))
    microrregiao = Column(String(100))
    
    # Metadados
    fonte_geocodigo = Column(String(50), default="IBGE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AtlasMunicipioGeocode(municipio='{self.municipio}', uf='{self.uf}')>"


# ============================================================
# CLIMATE ORACLE & BLOCKCHAIN TRANSACTION - Modelos
# ============================================================

class OracleEvent(Base):
    """
    Modelo para eventos avaliados pelo Climate Oracle
    Tabela: oracle_events
    """
    __tablename__ = "oracle_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    event_id = Column(String, unique=True, index=True, nullable=False)
    token_id = Column(String, index=True) # ID of the associated policy token
    
    # Location
    municipio = Column(String)
    uf = Column(String(2))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Event Data
    disaster_type = Column(String)
    severity_score = Column(Float) # 1.0 - 5.0
    ndvi = Column(Float)
    soil_moisture = Column(Float)
    
    # Oracle Decision
    payout_triggered = Column(Boolean, default=False)
    payout_percentage = Column(Float, default=0.0)
    payout_amount = Column(DECIMAL(15, 2), default=0.0)
    
    # Blockchain Reference
    blockchain_tx_id = Column(String, index=True, nullable=True) # Linked transaction if payout
    status = Column(String, default="EVALUATED") # PENDING, EVALUATED, TRIGGERED, PAID
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<OracleEvent(event_id='{self.event_id}', severity='{self.severity_score}')>"


class BlockchainTransaction(Base):
    """
    Modelo genérico para transações Hathor registradas
    Tabela: blockchain_transactions
    """
    __tablename__ = "blockchain_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    tx_hash = Column(String, unique=True, index=True, nullable=False)
    token_uid = Column(String, index=True) # UID of the created Hathor token (e.g. CLMT)
    
    from_address = Column(String)
    to_address = Column(String)
    amount = Column(DECIMAL(20, 4))
    
    block_height = Column(Integer, nullable=True)
    confirmations = Column(Integer, default=0)
    
    status = Column(String, default="PENDING") # PENDING, CONFIRMED, FAILED
    
    # Metadata and Feedback
    message = Column(String, nullable=True)
    explorer_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BlockchainTransaction(tx='{self.tx_hash}', status='{self.status}')>"


# ============================================================
# CELESTRAK SPACE WEATHER - Modelos
# ============================================================

class SpaceWeatherLog(Base):
    """
    Modelo para armazenamento permanente do clima espacial
    Tabela: space_weather_logs
    """
    __tablename__ = "space_weather_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    timestamp = Column(DateTime, index=True, nullable=False) # Data da leitura
    
    kp_index = Column(Float, nullable=True)
    ap_index = Column(Float, nullable=True)
    solar_flux = Column(Float, nullable=True)
    
    # Magnetic and Radiation Storms
    geomagnetic_storm = Column(Boolean, default=False)
    storm_level = Column(String, nullable=True) # G1-G5
    solar_radiation_storm = Column(Boolean, default=False)
    radiation_level = Column(String, nullable=True) # S1-S5
    radio_blackout = Column(Boolean, default=False)
    blackout_level = Column(String, nullable=True) # R1-R5
    
    # Risco de Conjunção e Anomalia
    conjunction_risk_level = Column(String, default="LOW")
    anomaly_flag = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SpaceWeatherLog(time='{self.timestamp}', kp='{self.kp_index}')>"

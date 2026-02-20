from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Float, Integer, ForeignKey, Date, JSON, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
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

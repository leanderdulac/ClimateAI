
import logging
import uuid
import secrets
import hashlib
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from config.database import get_db_session
from models.sqlalchemy_models import Partner, APIKey, User
from middleware.auth_middleware import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Partners"])

# --- Pydantic Models ---
class PartnerCreate(BaseModel):
    name: str
    slug: str
    contact_email: Optional[str] = None

class PartnerResponse(BaseModel):
    id: str
    name: str
    slug: str
    contact_email: Optional[str]
    api_enabled: bool
    created_at: datetime

    class Config:
        orm_mode = True

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: str
    prefix: str
    name: Optional[str]
    created_at: datetime
    # We DO NOT return the full key hash or the key itself here (key is shown only once on creation)
    
class APIKeyCreatedResponse(APIKeyResponse):
    secret_key: str # The actual key, shown only once

# --- Endpoints ---

@router.post("/partners", response_model=PartnerResponse)
async def create_partner(
    partner_data: PartnerCreate,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Register a new B2B Partner (Tenant).
    """
    # Check if slug exists
    stmt = select(Partner).where(Partner.slug == partner_data.slug)
    existing = await session.execute(stmt)
    if existing.scalars().first():
        raise HTTPException(400, "Partner slug already exists.")
        
    new_partner = Partner(
        id=str(uuid.uuid4()),
        name=partner_data.name,
        slug=partner_data.slug,
        contact_email=partner_data.contact_email,
        api_enabled=True # Enable by default for now
    )
    
    session.add(new_partner)
    await session.commit()
    await session.refresh(new_partner)
    
    logger.info(f"Partner created: {new_partner.name} by {current_user.email}")
    return new_partner

@router.get("/partners", response_model=List[PartnerResponse])
async def list_partners(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List all registered partners.
    """
    stmt = select(Partner)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.post("/partners/{partner_id}/api-keys", response_model=APIKeyCreatedResponse)
async def generate_api_key(
    partner_id: str,
    key_data: APIKeyCreate,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Generate a new API Key for a Partner.
    Returns the raw secret key ONCE.
    """
    # Verify partner exists
    stmt = select(Partner).where(Partner.id == partner_id)
    result = await session.execute(stmt)
    partner = result.scalars().first()
    if not partner:
        raise HTTPException(404, "Partner not found")
        
    # Generate Key
    raw_key = f"sk_live_{secrets.token_urlsafe(24)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    new_key = APIKey(
        id=str(uuid.uuid4()),
        partner_id=partner_id,
        key_hash=key_hash,
        prefix=raw_key[:10],
        name=key_data.name,
        created_at=datetime.utcnow()
    )
    
    session.add(new_key)
    await session.commit()
    
    logger.warning(f"API Key generated for {partner.slug} by {current_user.email}")
    
    return APIKeyCreatedResponse(
        id=new_key.id,
        prefix=new_key.prefix,
        name=new_key.name,
        created_at=new_key.created_at,
        secret_key=raw_key
    )

@router.delete("/partners/{partner_id}/api-keys/{key_id}")
async def revoke_api_key(
    partner_id: str,
    key_id: str,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Revoke (delete) an API Key.
    """
    stmt = select(APIKey).where(APIKey.id == key_id, APIKey.partner_id == partner_id)
    result = await session.execute(stmt)
    key = result.scalars().first()
    
    if not key:
        raise HTTPException(404, "API Key not found")
        
    await session.delete(key)
    await session.commit()
    
    return {"message": "API Key revoked successfully"}

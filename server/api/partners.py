"""Admin API for B2B partners and live API keys."""

from __future__ import annotations

import hashlib
import logging
import re
import secrets
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session
from middleware.auth_middleware import get_current_active_user
from models.sqlalchemy_models import APIKey, Partner, User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Partners"])
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower().replace("_", "-"))
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug or not _SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="Slug inválido. Use letras minúsculas, números e hífen.")
    return slug


class PartnerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    slug: Optional[str] = Field(default=None, max_length=80)
    contact_email: Optional[str] = None


class PartnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    contact_email: Optional[str]
    api_enabled: bool
    created_at: datetime


class PartnerUpdate(BaseModel):
    api_enabled: Optional[bool] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    contact_email: Optional[str] = None


class APIKeyCreate(BaseModel):
    name: str = Field(default="Integração", min_length=1, max_length=80)


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prefix: str
    name: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime


class APIKeyCreatedResponse(APIKeyResponse):
    secret_key: str


@router.post("/partners", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def create_partner(
    partner_data: PartnerCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    slug = _normalize_slug(partner_data.slug or partner_data.name)
    existing = await session.execute(select(Partner).where(Partner.slug == slug))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Já existe um parceiro com este slug.")

    partner = Partner(
        id=str(uuid.uuid4()),
        name=partner_data.name.strip(),
        slug=slug,
        contact_email=partner_data.contact_email,
        api_enabled=True,
    )
    session.add(partner)
    await session.commit()
    await session.refresh(partner)
    logger.info("Partner created: %s by %s", partner.slug, current_user.email)
    return partner


@router.get("/partners", response_model=List[PartnerResponse])
async def list_partners(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(Partner).order_by(Partner.created_at.desc()))
    return result.scalars().all()


@router.patch("/partners/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: str,
    payload: PartnerUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    partner = (await session.execute(select(Partner).where(Partner.id == partner_id))).scalars().first()
    if not partner:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    if payload.api_enabled is not None:
        partner.api_enabled = payload.api_enabled
    if payload.name is not None:
        partner.name = payload.name.strip()
    if payload.contact_email is not None:
        partner.contact_email = payload.contact_email
    await session.commit()
    await session.refresh(partner)
    logger.info("Partner updated: %s by %s", partner.slug, current_user.email)
    return partner


@router.get("/partners/{partner_id}/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    partner_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    partner = (await session.execute(select(Partner).where(Partner.id == partner_id))).scalars().first()
    if not partner:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    result = await session.execute(
        select(APIKey).where(APIKey.partner_id == partner_id).order_by(APIKey.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/partners/{partner_id}/api-keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_api_key(
    partner_id: str,
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    partner = (await session.execute(select(Partner).where(Partner.id == partner_id))).scalars().first()
    if not partner:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    if not partner.api_enabled:
        raise HTTPException(status_code=400, detail="API desabilitada para este parceiro.")

    raw_key = f"sk_live_{secrets.token_urlsafe(24)}"
    new_key = APIKey(
        id=str(uuid.uuid4()),
        partner_id=partner_id,
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        prefix=raw_key[:12],
        name=key_data.name.strip(),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    session.add(new_key)
    await session.commit()
    await session.refresh(new_key)
    logger.warning("API key generated for %s by %s", partner.slug, current_user.email)
    return APIKeyCreatedResponse(
        id=new_key.id,
        prefix=new_key.prefix,
        name=new_key.name,
        is_active=new_key.is_active,
        last_used_at=new_key.last_used_at,
        created_at=new_key.created_at,
        secret_key=raw_key,
    )


@router.delete("/partners/{partner_id}/api-keys/{key_id}")
async def revoke_api_key(
    partner_id: str,
    key_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    key = (
        await session.execute(select(APIKey).where(APIKey.id == key_id, APIKey.partner_id == partner_id))
    ).scalars().first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key não encontrada")
    key.is_active = False
    await session.commit()
    logger.warning("API key revoked for partner %s by %s", partner_id, current_user.email)
    return {"message": "API Key revogada"}

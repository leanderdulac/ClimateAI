
import logging
from typing import Optional
import hashlib
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from models.sqlalchemy_models import APIKey, Partner
from config.database import async_session_maker

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    if not api_key_header:
        return None
    return api_key_header

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow open routes or existing JWT auth to pass through
        # This middleware acts as an *alternative* auth method, enriching the request state
        # It does NOT block requests by default (unless enforced by a dependency)
        
        api_key = request.headers.get("X-API-Key")
        
        if api_key:
            try:
                # Hash the key to look it up
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                
                async with async_session_maker() as session:
                    stmt = select(APIKey).where(
                        APIKey.key_hash == key_hash,
                        APIKey.is_active == True
                    )
                    result = await session.execute(stmt)
                    db_key = result.scalars().first()
                    
                    if db_key:
                        # Fetch Partner info
                        partner_stmt = select(Partner).where(Partner.id == db_key.partner_id)
                        partner_result = await session.execute(partner_stmt)
                        partner = partner_result.scalars().first()
                        
                        if partner and partner.api_enabled:
                            # Context injection: Add partner info to request state
                            request.state.partner = partner
                            request.state.api_key = db_key
                            logger.info(f"Authenticated Partner: {partner.name} (Key: {db_key.prefix}...)")
                        else:
                            logger.warning(f"Valid key but disabled partner/api: {db_key.prefix}...")
                    else:
                         logger.warning("Invalid API Key provided")
            except Exception as e:
                logger.error(f"Error in API Key Middleware: {e}")
                
        response = await call_next(request)
        return response

# Dependency to ENFORCE API Key presence (for M2M routes)
async def require_api_key(request: Request):
    if not hasattr(request.state, "partner") or not request.state.partner:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return request.state.partner

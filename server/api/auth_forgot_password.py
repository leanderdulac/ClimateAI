from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from config.supabase_client import get_supabase_client

router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=500, detail="Supabase client not available")
    try:
        # Supabase expects a redirect URL that exists in frontend; use generic /auth route
        await client.auth.reset_password_for_email(payload.email, redirect_to="/auth")
    except Exception as e:
        # Log but do not expose details for security
        import logging
        logging.getLogger(__name__).warning(f"Supabase forgot password error: {e}")
    return {"detail": "If the e‑mail is registered you will receive instructions."}

import logging
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from config.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

_SAFE_MSG = "Se o e-mail estiver cadastrado, você receberá as instruções de recuperação."


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """
    Solicita reset de senha via Supabase.
    Sempre retorna 200 com mensagem genérica (segurança: não revela se o e-mail existe).
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Supabase client not available — skipping password reset email")
        return {"detail": _SAFE_MSG}

    try:
        # Supabase Python client is SYNCHRONOUS — do NOT use await
        client.auth.reset_password_for_email(
            payload.email,
            options={"redirect_to": "/auth"},
        )
    except Exception as exc:
        logger.warning("Supabase forgot password error: %s", exc)

    return {"detail": _SAFE_MSG}


"""
Authenticate against Supabase Auth (GoTrue).

Prefers supabase-py ``sign_in_with_password`` / ``sign_up``. When the client
library is unavailable, talks to the GoTrue REST API with SUPABASE_URL + anon key.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from config.supabase_client import (
    get_supabase_anon_key,
    get_supabase_auth_issuer,
    get_supabase_client,
    get_supabase_url,
    is_supabase_configured,
)

logger = logging.getLogger(__name__)

GOTRUE_TIMEOUT_SECONDS = 15.0
SUPABASE_MANAGED_PASSWORD_MARKER = "SUPABASE-MANAGED"


class SupabaseAuthError(Exception):
    """Raised when Supabase Auth rejects or cannot complete a request."""

    def __init__(
        self,
        message: str,
        *,
        invalid_credentials: bool = False,
        unavailable: bool = False,
        already_registered: bool = False,
    ):
        super().__init__(message)
        self.invalid_credentials = invalid_credentials
        self.unavailable = unavailable
        self.already_registered = already_registered


@dataclass(frozen=True)
class SupabaseAuthUser:
    id: str
    email: str
    full_name: Optional[str] = None


def _gotrue_headers(anon_key: str) -> dict[str, str]:
    return {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json",
    }


def _full_name_from_metadata(metadata: Any) -> Optional[str]:
    if not isinstance(metadata, dict):
        return None
    for key in ("full_name", "name", "display_name"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _user_from_gotrue_payload(payload: dict[str, Any]) -> SupabaseAuthUser:
    user = payload.get("user") if isinstance(payload.get("user"), dict) else payload
    user_id = str(user.get("id") or "").strip()
    email = str(user.get("email") or "").strip()
    if not user_id or not email:
        raise SupabaseAuthError(
            "Resposta do Supabase Auth sem id/email",
            unavailable=True,
        )
    metadata = user.get("user_metadata") or user.get("user_meta_data") or {}
    return SupabaseAuthUser(
        id=user_id,
        email=email,
        full_name=_full_name_from_metadata(metadata),
    )


def _user_from_supabase_py(response: Any) -> SupabaseAuthUser:
    user = getattr(response, "user", None)
    if user is None and isinstance(response, dict):
        return _user_from_gotrue_payload(response)
    user_id = str(getattr(user, "id", "") or "").strip()
    email = str(getattr(user, "email", "") or "").strip()
    if not user_id or not email:
        raise SupabaseAuthError(
            "Resposta do Supabase Auth sem id/email",
            unavailable=True,
        )
    metadata = getattr(user, "user_metadata", None) or {}
    return SupabaseAuthUser(
        id=user_id,
        email=email,
        full_name=_full_name_from_metadata(metadata),
    )


def _classify_gotrue_error(status_code: int, payload: Any) -> SupabaseAuthError:
    message = "Falha na autenticação Supabase"
    error_code = ""
    if isinstance(payload, dict):
        message = (
            payload.get("error_description")
            or payload.get("msg")
            or payload.get("message")
            or payload.get("error")
            or message
        )
        error_code = str(payload.get("error_code") or payload.get("error") or "").lower()
    lowered = str(message).lower()
    invalid = status_code in (400, 401, 403, 422) and (
        "invalid login" in lowered
        or "invalid_grant" in lowered
        or "invalid credentials" in lowered
        or "email not confirmed" in lowered
        or error_code in {"invalid_credentials", "invalid_grant"}
    )
    already = "already registered" in lowered or "user already" in lowered
    unavailable = status_code >= 500 or status_code in (404, 408, 429)
    return SupabaseAuthError(
        str(message),
        invalid_credentials=invalid and not already,
        unavailable=unavailable,
        already_registered=already,
    )


def _gotrue_post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    base = get_supabase_url()
    anon_key = get_supabase_anon_key()
    if not base or not anon_key:
        raise SupabaseAuthError("Supabase Auth não configurado", unavailable=True)

    url = f"{base}{path}"
    try:
        with httpx.Client(timeout=GOTRUE_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=body, headers=_gotrue_headers(anon_key))
    except httpx.HTTPError as exc:
        logger.warning("GoTrue request failed: %s", exc)
        raise SupabaseAuthError(
            "Supabase Auth indisponível",
            unavailable=True,
        ) from exc

    payload: Any
    try:
        payload = response.json()
    except ValueError:
        payload = {"message": response.text}

    if response.status_code >= 400:
        raise _classify_gotrue_error(response.status_code, payload)
    if not isinstance(payload, dict):
        raise SupabaseAuthError("Resposta inválida do Supabase Auth", unavailable=True)
    return payload


def sign_in_with_password(email: str, password: str) -> SupabaseAuthUser:
    """Authenticate against Supabase Auth. Raises SupabaseAuthError on failure."""
    if not is_supabase_configured():
        raise SupabaseAuthError("Supabase Auth não configurado", unavailable=True)

    client = get_supabase_client()
    if client is not None:
        try:
            response = client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            return _user_from_supabase_py(response)
        except SupabaseAuthError:
            raise
        except Exception as exc:
            lowered = str(exc).lower()
            if "invalid login" in lowered or "invalid_grant" in lowered:
                raise SupabaseAuthError(
                    "Email ou senha incorretos",
                    invalid_credentials=True,
                ) from exc
            logger.warning("supabase-py sign_in_with_password failed, trying GoTrue REST: %s", exc)

    payload = _gotrue_post(
        "/auth/v1/token?grant_type=password",
        {"email": email, "password": password},
    )
    return _user_from_gotrue_payload(payload)


def sign_up(email: str, password: str, *, full_name: Optional[str] = None) -> SupabaseAuthUser:
    """Create a user in Supabase Auth. Raises SupabaseAuthError on failure."""
    if not is_supabase_configured():
        raise SupabaseAuthError("Supabase Auth não configurado", unavailable=True)

    metadata = {"full_name": full_name} if full_name else {}
    client = get_supabase_client()
    if client is not None:
        try:
            payload: dict[str, Any] = {"email": email, "password": password}
            if metadata:
                payload["options"] = {"data": metadata}
            response = client.auth.sign_up(payload)
            return _user_from_supabase_py(response)
        except SupabaseAuthError:
            raise
        except Exception as exc:
            lowered = str(exc).lower()
            if "already registered" in lowered or "user already" in lowered:
                raise SupabaseAuthError(
                    "Email já cadastrado",
                    already_registered=True,
                ) from exc
            logger.warning("supabase-py sign_up failed, trying GoTrue REST: %s", exc)

    body: dict[str, Any] = {"email": email, "password": password}
    if metadata:
        body["data"] = metadata
    payload = _gotrue_post("/auth/v1/signup", body)
    return _user_from_gotrue_payload(payload)


__all__ = [
    "SUPABASE_MANAGED_PASSWORD_MARKER",
    "SupabaseAuthError",
    "SupabaseAuthUser",
    "get_supabase_auth_issuer",
    "is_supabase_configured",
    "sign_in_with_password",
    "sign_up",
]

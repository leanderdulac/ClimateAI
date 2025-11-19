"""
Security middleware for production hardening
"""

import logging
import os

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers - Proteção contra principais vulnerabilidades
        response.headers["X-Content-Type-Options"] = (
            "nosniff"  # Evita MIME type sniffing
        )
        response.headers["X-Frame-Options"] = "DENY"  # Evita clickjacking
        response.headers["X-XSS-Protection"] = "1; mode=block"  # XSS protection
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"  # HTTPS enforcer
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"  # CSP
        )
        response.headers["Referrer-Policy"] = (
            "strict-origin-when-cross-origin"  # Referrer policy
        )
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"  # Feature policy
        )

        # Remover headers informativos que podem expor versões
        try:
            del response.headers["Server"]
        except KeyError:
            pass
        try:
            del response.headers["X-Powered-By"]
        except KeyError:
            pass

        # Log de requisições suspeitas
        if (
            "union" in str(request.query_params).lower()
            or "script" in str(request.body).lower()
        ):
            logger.warning(
                f"⚠️  Requisição suspeita de {request.client.host}: {request.url.path}"
            )

        return response

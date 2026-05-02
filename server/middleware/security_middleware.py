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
            "default-src 'none'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'"  # Hardened CSP — no unsafe-inline
        )
        response.headers["Referrer-Policy"] = (
            "strict-origin-when-cross-origin"  # Referrer policy
        )
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"  # Feature policy
        )
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Remover headers informativos que podem expor versões
        try:
            del response.headers["Server"]
        except KeyError:
            pass
        try:
            del response.headers["X-Powered-By"]
        except KeyError:
            pass

        # Log de requisições maliciosas óbvias (padrões de SQL injection comuns)
        if request.method != "OPTIONS":
            path_lower = str(request.url.path).lower()
            query_lower = str(request.query_params).lower()
            
            if "union select" in query_lower or "union all" in query_lower:
                logger.warning(
                    f"⚠️  Possível tentativa de SQL Injection de {request.client.host}: {request.url.path}"
                )

        return response

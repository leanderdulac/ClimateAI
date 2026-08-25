"""FastAPI application factory for ClimateWise."""

import os
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from config.config import settings
from lib.security import rate_limiter
from middleware.auth_middleware import default_deny_middleware
from middleware.error_handling import setup_error_middleware
from middleware.redaction import redact_payload
from middleware.security_middleware import SecurityHeadersMiddleware
from services.otel import init_otel

API_PREFIX = os.getenv("API_PREFIX", "/api/v1").rstrip("/") or "/api/v1"

DEPRECATED_PRICING_PREFIXES = (
    f"{API_PREFIX}/policy-pricing",
    f"{API_PREFIX}/unified-pricing",
    f"{API_PREFIX}/comprehensive-pricing",
    f"{API_PREFIX}/ensemble-pricing",
    f"{API_PREFIX}/climate-premium",
    f"{API_PREFIX}/integrated-pricing-framework",
    f"{API_PREFIX}/pricing/extreme-value",
)

CANONICAL_PRICING_QUOTE = f"{API_PREFIX}/pricing/quote"


def create_app() -> FastAPI:
    """Build the FastAPI app with security middleware and router registry."""
    app = FastAPI(
        title="FIMCE API",
        description="API do Framework Integrado de Modelagem Climático-Econômica",
        version="1.0.0",
        validate_responses=True,
        docs_url="/docs" if settings.ENVIRONMENT.lower() != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT.lower() != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT.lower() != "production" else None,
    )

    setup_error_middleware(app)
    init_otel(app)

    allow_origins = settings.ALLOW_ORIGINS
    allow_credentials = "*" not in allow_origins
    if "*" in allow_origins and not settings.DEBUG:
        raise RuntimeError("ALLOW_ORIGINS='*' não é permitido fora de DEBUG")

    app.add_middleware(SecurityHeadersMiddleware)

    if settings.DOMAIN and not settings.DEBUG:
        normalized_domain = settings.DOMAIN.strip().lower()
        placeholder_domains = {"yourdomain.com", "example.com", "localhost"}
        if normalized_domain and normalized_domain not in placeholder_domains:
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=[
                    settings.DOMAIN,
                    f"*.{settings.DOMAIN}",
                    "localhost",
                    "127.0.0.1",
                    "[::1]",
                ],
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(default_deny_middleware)
    app.middleware("http")(_feature_gate_middleware)
    app.middleware("http")(_request_id_middleware)
    app.middleware("http")(_rate_limit_middleware)
    app.middleware("http")(_redaction_middleware)
    app.middleware("http")(_pricing_deprecation_middleware)

    from router_registry import register_routers

    register_routers(app, API_PREFIX)
    return app


async def _feature_gate_middleware(request: Request, call_next):
    from lib.features import disabled_feature_for_path

    feature = disabled_feature_for_path(request.url.path)
    if feature:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Feature '{feature}' is disabled"},
        )
    return await call_next(request)


async def _request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def _rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Limite de requisições excedido. Tente novamente em alguns minutos."},
            headers={
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Window": str(rate_limiter.window_seconds),
                "Retry-After": str(rate_limiter.window_seconds),
                "X-Request-ID": getattr(request.state, "request_id", ""),
            },
        )
    response = await call_next(request)
    response.headers["X-Request-ID"] = getattr(request.state, "request_id", "")
    return response


async def _redaction_middleware(request: Request, call_next):
    if hasattr(request.state, "log_context"):
        request.state.log_context = redact_payload(request.state.log_context)
    return await call_next(request)


async def _pricing_deprecation_middleware(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if any(path.startswith(prefix) for prefix in DEPRECATED_PRICING_PREFIXES):
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = f'<{CANONICAL_PRICING_QUOTE}>; rel="successor-version"'
        response.headers["Sunset"] = "Thu, 01 Jul 2027 00:00:00 GMT"
    return response

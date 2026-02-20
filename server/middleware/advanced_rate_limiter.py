"""
Rate Limiter Avançado com Configuração por Rota e Tipo de Cliente
Implementa padrões de WAF/Rate-limit para proteção na borda
"""

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class ClientTier(Enum):
    """Níveis de clientes com limites diferenciados"""
    ANONYMOUS = "anonymous"      # Usuários não autenticados
    BASIC = "basic"             # Usuários básicos
    PREMIUM = "premium"         # Usuários premium
    ENTERPRISE = "enterprise"   # Clientes enterprise
    INTERNAL = "internal"       # Serviços internos


@dataclass
class RateLimitConfig:
    """Configuração de rate limit por rota/tier"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_size: int = 0  # Permite explosões curtas (0 = desativado)
    
    def __post_init__(self):
        if self.burst_size == 0:
            self.burst_size = self.requests_per_minute


# Configurações padrão por tier
DEFAULT_LIMITS: Dict[ClientTier, RateLimitConfig] = {
    ClientTier.ANONYMOUS: RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=500,
        burst_size=15
    ),
    ClientTier.BASIC: RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=2000,
        burst_size=45
    ),
    ClientTier.PREMIUM: RateLimitConfig(
        requests_per_minute=100,
        requests_per_hour=2000,
        requests_per_day=10000,
        burst_size=150
    ),
    ClientTier.ENTERPRISE: RateLimitConfig(
        requests_per_minute=500,
        requests_per_hour=10000,
        requests_per_day=50000,
        burst_size=750
    ),
    ClientTier.INTERNAL: RateLimitConfig(
        requests_per_minute=1000,
        requests_per_hour=50000,
        requests_per_day=200000,
        burst_size=1500
    ),
}

# Configurações específicas por rota (override dos limites por tier)
ROUTE_LIMITS: Dict[str, Dict[ClientTier, RateLimitConfig]] = {
    "/api/v1/policy_pricing": {
        ClientTier.ANONYMOUS: RateLimitConfig(5, 30, 100, 8),
        ClientTier.BASIC: RateLimitConfig(20, 200, 1000, 30),
        ClientTier.PREMIUM: RateLimitConfig(100, 1000, 5000, 150),
    },
    "/api/v1/ml/": {
        ClientTier.ANONYMOUS: RateLimitConfig(2, 10, 50, 3),
        ClientTier.BASIC: RateLimitConfig(10, 100, 500, 15),
        ClientTier.PREMIUM: RateLimitConfig(50, 500, 2500, 75),
    },
    "/api/v1/external/": {
        ClientTier.ANONYMOUS: RateLimitConfig(5, 50, 200, 8),
        ClientTier.BASIC: RateLimitConfig(30, 300, 1500, 45),
        ClientTier.PREMIUM: RateLimitConfig(150, 1500, 7500, 225),
    },
    "/api/v1/audit/": {
        ClientTier.ANONYMOUS: RateLimitConfig(0, 0, 0, 0),  # Bloqueado
        ClientTier.BASIC: RateLimitConfig(10, 50, 200, 15),
        ClientTier.PREMIUM: RateLimitConfig(50, 500, 2500, 75),
    },
    "/health": {
        ClientTier.ANONYMOUS: RateLimitConfig(60, 600, 6000, 90),
        ClientTier.BASIC: RateLimitConfig(60, 600, 6000, 90),
        ClientTier.PREMIUM: RateLimitConfig(60, 600, 6000, 90),
    },
}


@dataclass
class RateLimitWindow:
    """Janela de rate limit para um cliente"""
    minute_count: int = 0
    hour_count: int = 0
    day_count: int = 0
    minute_window_start: float = field(default_factory=time.time)
    hour_window_start: float = field(default_factory=time.time)
    day_window_start: float = field(default_factory=time.time)
    burst_tokens: float = field(default_factory=lambda: DEFAULT_LIMITS[ClientTier.ANONYMOUS].burst_size)
    last_burst_refill: float = field(default_factory=time.time)


class AdvancedRateLimiter:
    """
    Rate Limiter avançado com configuração por rota e tipo de cliente.
    
    Uso:
        limiter = AdvancedRateLimiter()
        allowed, retry_after, headers = limiter.is_allowed(client_id, "/api/v1/endpoint", tier)
    """
    
    def __init__(
        self,
        default_limits: Optional[Dict[ClientTier, RateLimitConfig]] = None,
        route_limits: Optional[Dict[str, Dict[ClientTier, RateLimitConfig]]] = None,
        window_size_minutes: int = 1,
        window_size_hours: int = 1,
        window_size_days: int = 24,
    ):
        self.default_limits = default_limits or DEFAULT_LIMITS
        self.route_limits = route_limits or ROUTE_LIMITS
        self.windows: Dict[str, RateLimitWindow] = {}
        self.window_size_minutes = window_size_minutes * 60
        self.window_size_hours = window_size_hours * 3600
        self.window_size_days = window_size_days * 3600
        
        # Estatísticas para monitoramento
        self.stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "by_tier": defaultdict(lambda: {"allowed": 0, "blocked": 0}),
            "by_route": defaultdict(lambda: {"allowed": 0, "blocked": 0}),
        }
    
    def _get_client_key(self, client_id: str, route: str, tier: ClientTier) -> str:
        """Gera chave única para o cliente/rota/tier"""
        key = f"{tier.value}:{client_id}:{route}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_config(self, route: str, tier: ClientTier) -> RateLimitConfig:
        """Obtém configuração de rate limit para rota/tier"""
        # Verificar configurações específicas por rota
        for route_pattern, tier_configs in self.route_limits.items():
            if route.startswith(route_pattern):
                if tier in tier_configs:
                    return tier_configs[tier]
        
        # Fallback para configuração padrão do tier
        return self.default_limits[tier]
    
    def _reset_window_if_needed(self, window: RateLimitWindow, config: RateLimitConfig) -> None:
        """Reseta janelas expiradas"""
        current_time = time.time()
        
        # Reset janela de minuto
        if current_time - window.minute_window_start >= self.window_size_minutes:
            window.minute_count = 0
            window.minute_window_start = current_time
        
        # Reset janela de hora
        if current_time - window.hour_window_start >= self.window_size_hours:
            window.hour_count = 0
            window.hour_window_start = current_time
        
        # Reset janela de dia
        if current_time - window.day_window_start >= self.window_size_days:
            window.day_count = 0
            window.day_window_start = current_time
        
        # Refill burst tokens (token bucket)
        time_since_refill = current_time - window.last_burst_refill
        tokens_to_add = time_since_refill * (config.burst_size / 60.0)  # Tokens por segundo
        window.burst_tokens = min(config.burst_size, window.burst_tokens + tokens_to_add)
        if tokens_to_add > 0:
            window.last_burst_refill = current_time
    
    def is_allowed(
        self,
        client_id: str,
        route: str,
        tier: ClientTier = ClientTier.ANONYMOUS,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, int, Dict[str, str]]:
        """
        Verifica se requisição é permitida.
        
        Args:
            client_id: Identificador único do cliente (IP, user_id, etc.)
            route: Rota da requisição
            tier: Nível do cliente
            extra_data: Dados adicionais para logging
            
        Returns:
            Tuple[allowed, retry_after_seconds, headers]
        """
        self.stats["total_requests"] += 1
        
        # Obter configuração
        config = self._get_config(route, tier)
        
        # Verificar se rota está bloqueada para este tier
        if config.requests_per_minute == 0:
            self._record_decision(route, tier, False)
            headers = self._generate_headers(config, 0, 0, 0, retry_after=3600)
            return False, 3600, headers
        
        # Obter/criar janela
        key = self._get_client_key(client_id, route, tier)
        if key not in self.windows:
            window = RateLimitWindow(burst_tokens=config.burst_size)
            self.windows[key] = window
        else:
            window = self.windows[key]
        
        # Resetar janelas expiradas
        self._reset_window_if_needed(window, config)
        
        # Verificar limites
        current_time = time.time()
        
        # Verificar burst (token bucket)
        if window.burst_tokens >= 1:
            window.burst_tokens -= 1
            window.minute_count += 1
            window.hour_count += 1
            window.day_count += 1
            self._record_decision(route, tier, True)
            headers = self._generate_headers(
                config,
                max(0, config.requests_per_minute - window.minute_count),
                max(0, config.requests_per_hour - window.hour_count),
                max(0, config.requests_per_day - window.day_count)
            )
            return True, 0, headers
        
        # Verificar limite de minuto
        if window.minute_count >= config.requests_per_minute:
            retry_after = int(self.window_size_minutes - (current_time - window.minute_window_start)) + 1
            self._record_decision(route, tier, False)
            headers = self._generate_headers(config, 0, 0, 0, retry_after=retry_after)
            return False, retry_after, headers
        
        # Verificar limite de hora
        if window.hour_count >= config.requests_per_hour:
            retry_after = int(self.window_size_hours - (current_time - window.hour_window_start)) + 1
            self._record_decision(route, tier, False)
            headers = self._generate_headers(config, 0, 0, 0, retry_after=retry_after)
            return False, retry_after, headers
        
        # Verificar limite de dia
        if window.day_count >= config.requests_per_day:
            retry_after = int(self.window_size_days - (current_time - window.day_window_start)) + 1
            self._record_decision(route, tier, False)
            headers = self._generate_headers(config, 0, 0, 0, retry_after=retry_after)
            return False, retry_after, headers
        
        # Permitir requisição
        window.minute_count += 1
        window.hour_count += 1
        window.day_count += 1
        self._record_decision(route, tier, True)
        
        headers = self._generate_headers(
            config,
            max(0, config.requests_per_minute - window.minute_count),
            max(0, config.requests_per_hour - window.hour_count),
            max(0, config.requests_per_day - window.day_count)
        )
        return True, 0, headers
    
    def _record_decision(self, route: str, tier: ClientTier, allowed: bool) -> None:
        """Registrar decisão para estatísticas"""
        if allowed:
            self.stats["allowed_requests"] += 1
            self.stats["by_tier"][tier.value]["allowed"] += 1
            self.stats["by_route"][route]["allowed"] += 1
        else:
            self.stats["blocked_requests"] += 1
            self.stats["by_tier"][tier.value]["blocked"] += 1
            self.stats["by_route"][route]["blocked"] += 1
    
    def _generate_headers(
        self,
        config: RateLimitConfig,
        remaining_minute: int,
        remaining_hour: int,
        remaining_day: int,
        retry_after: int = 0
    ) -> Dict[str, str]:
        """Gerar headers de rate limit"""
        headers = {
            "X-RateLimit-Limit-Minute": str(config.requests_per_minute),
            "X-RateLimit-Remaining-Minute": str(remaining_minute),
            "X-RateLimit-Limit-Hour": str(config.requests_per_hour),
            "X-RateLimit-Remaining-Hour": str(remaining_hour),
            "X-RateLimit-Limit-Day": str(config.requests_per_day),
            "X-RateLimit-Remaining-Day": str(remaining_day),
            "X-RateLimit-Reset-Minute": str(int(time.time() + self.window_size_minutes)),
        }
        
        if retry_after > 0:
            headers["Retry-After"] = str(retry_after)
        
        return headers
    
    def get_client_usage(self, client_id: str, tier: ClientTier = ClientTier.ANONYMOUS) -> Dict[str, Any]:
        """Obter uso atual do cliente"""
        result = {}
        for route_pattern in self.route_limits.keys():
            key = self._get_client_key(client_id, route_pattern, tier)
            if key in self.windows:
                window = self.windows[key]
                config = self._get_config(route_pattern, tier)
                result[route_pattern] = {
                    "minute_usage": f"{window.minute_count}/{config.requests_per_minute}",
                    "hour_usage": f"{window.hour_count}/{config.requests_per_hour}",
                    "day_usage": f"{window.day_count}/{config.requests_per_day}",
                    "burst_tokens": window.burst_tokens,
                }
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do rate limiter"""
        return {
            "total_requests": self.stats["total_requests"],
            "allowed_requests": self.stats["allowed_requests"],
            "blocked_requests": self.stats["blocked_requests"],
            "block_rate": (
                self.stats["blocked_requests"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0 else 0
            ),
            "by_tier": dict(self.stats["by_tier"]),
            "by_route": dict(self.stats["by_route"]),
            "active_clients": len(self.windows),
        }
    
    def cleanup_old_windows(self, max_age_hours: int = 24) -> int:
        """Limpar janelas antigas para economizar memória"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        keys_to_remove = []
        for key, window in self.windows.items():
            if (current_time - window.day_window_start) > max_age_seconds:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.windows[key]
        
        return len(keys_to_remove)


# Instância global para uso no middleware
rate_limiter = AdvancedRateLimiter()


# Middleware para FastAPI
async def rate_limit_middleware(request, call_next):
    """
    Middleware para FastAPI com rate limiting avançado.
    
    Uso no main.py:
        from middleware.advanced_rate_limiter import rate_limit_middleware
        app.middleware("http")(rate_limit_middleware)
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    if not isinstance(request, Request):
        return await call_next(request)
    
    # Obter identificador do cliente
    client_ip = request.client.host if request.client else "unknown"
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    
    # Determinar tier do cliente
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # Em produção, validar token e obter tier do usuário
        tier = ClientTier.BASIC  # Placeholder
    else:
        tier = ClientTier.ANONYMOUS
    
    # Verificar rate limit
    path = request.url.path
    allowed, retry_after, headers = rate_limiter.is_allowed(
        client_id=client_ip,
        route=path,
        tier=tier
    )
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit excedido. Tente novamente mais tarde.",
                "retry_after": retry_after,
                "client_tier": tier.value,
            },
            headers=headers
        )
    
    # Executar requisição
    response = await call_next(request)
    
    # Adicionar headers de rate limit
    for key, value in headers.items():
        response.headers[key] = value
    
    return response

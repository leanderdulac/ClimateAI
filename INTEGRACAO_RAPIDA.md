# 🚀 Guia Rápido de Integração - Tier 1

Este guia mostra como integrar as novas funcionalidades Tier 1 no seu código.

---

## 1. Circuit Breaker para APIs Externas

### Uso Básico
```python
from lib.resilient_http_client import create_resilient_client

# Criar cliente
noaa_client = create_resilient_client(
    service_name="noaa",
    base_url="https://api.noaa.gov",
    api_key=settings.NOAA_API_KEY,
    timeout_seconds=30.0,
    max_retries=3,
)

# Usar em um serviço
async def get_weather_data(lat: float, lon: float):
    response = await noaa_client.get(f"/stations?lat={lat}&lon={lon}")
    return response.json()

# Verificar saúde
status = noaa_client.get_health_status()
print(f"Circuit state: {status['circuit_state']}")
```

### Uso Avançado com Configuração Customizada
```python
from lib.resilient_http_client import (
    ResilientHttpClient,
    CircuitBreakerConfig,
    RetryConfig,
    TimeoutConfig,
)

client = ResilientHttpClient(
    service_name="openmeteo",
    base_url="https://api.open-meteo.com",
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=3,      # Abre após 3 falhas
        success_threshold=2,      # Fecha após 2 sucessos
        timeout=30.0,             # Tenta novamente após 30s
    ),
    retry_config=RetryConfig(
        max_attempts=5,
        base_delay=0.5,
        max_delay=10.0,
    ),
    timeout_config=TimeoutConfig(
        connect_timeout=3.0,
        read_timeout=15.0,
        write_timeout=5.0,
    ),
)
```

---

## 2. Caching Redis

### Decorator Simples
```python
from lib.redis_cache import get_cache, initialize_cache

# Inicializar (no startup da aplicação)
await initialize_cache("redis://localhost:6379")

# Usar decorator
cache = get_cache()

@cache.cached(ttl=3600, key_prefix="weather", tags=["weather", "external"])
async def get_weather_data(lat: float, lon: float):
    # Chamada à API externa
    response = await httpx.get(f"https://api.open-meteo.com/...?lat={lat}&lon={lon}")
    return response.json()

# Uso
data = await get_weather_data(-23.55, -46.63)
```

### Cache com Fallback Stale
```python
from lib.redis_cache import external_api_cache

@external_api_cache("openmeteo", ttl=1800, stale_ttl_multiplier=3)
async def get_weather_data(lat: float, lon: float):
    # Se cache expirou, retorna stale enquanto atualiza em background
    response = await httpx.get(f"https://api.open-meteo.com/...")
    return response.json()
```

### Uso Manual
```python
cache = get_cache()

# Set
await cache.set("user:123", {"name": "John"}, ttl=3600)

# Get
user = await cache.get("user:123", default=None)

# Get or Set
user = await cache.get_or_set(
    "user:123",
    lambda: fetch_user_from_db(123),
    ttl=3600
)

# Invalidate by tag
await cache.invalidate_by_tag("weather")
```

---

## 3. Rate Limiting

### Middleware (Automático)
```python
# No main.py
from middleware.advanced_rate_limiter import rate_limit_middleware

app.middleware("http")(rate_limit_middleware)
```

### Uso Manual em Endpoints
```python
from fastapi import Request, HTTPException
from middleware.advanced_rate_limiter import rate_limiter, ClientTier

@app.get("/api/v1/premium-endpoint")
async def premium_endpoint(request: Request):
    client_ip = request.client.host
    tier = ClientTier.PREMIUM  # Determinar tier do usuário
    
    allowed, retry_after, headers = rate_limiter.is_allowed(
        client_id=client_ip,
        route=request.url.path,
        tier=tier,
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit excedido. Tente em {retry_after}s",
            headers=headers,
        )
    
    # Headers de rate limit na resposta
    return {"data": "...", "headers": headers}
```

### Verificar Uso do Cliente
```python
usage = rate_limiter.get_client_usage("192.168.1.1", ClientTier.BASIC)
print(usage)
# {'/api/v1/weather': {'minute_usage': '5/30', 'hour_usage': '50/500', ...}}
```

---

## 4. X-Request-ID no Frontend

### Uso Automático (Já integrado)
```typescript
// Todas as chamadas via api.ts já incluem X-Request-ID
import { externalApi } from '@/lib/api';

const data = await externalApi.getWeatherData(lat, lon);
// Automaticamente inclui headers:
// { 'X-Request-ID': 'uuid-v4', 'X-Correlation-ID': 'uuid-v4' }
```

### Uso Manual
```typescript
import { getDefaultHeaders, fetchWithTracking } from '@/lib/requestId';

// Fetch com tracking
const response = await fetchWithTracking('/api/v1/endpoint', {
    method: 'POST',
    body: JSON.stringify(data),
});

// Obter headers padrão
const headers = getDefaultHeaders();
```

### Hook React
```typescript
import { useRequestIDContext, RequestIDProvider } from '@/lib/requestId';

function App() {
    return (
        <RequestIDProvider>
            <MyComponent />
        </RequestIDProvider>
    );
}

function MyComponent() {
    const requestId = useRequestIDContext();
    return <div>Request ID: {requestId}</div>;
}
```

---

## 5. Banner de Consentimento LGPD

### No App.tsx
```typescript
import { useConsent, ConsentBanner } from '@/hooks/useConsent';

export function App() {
    const {
        showBanner,
        acceptAll,
        acceptNecessary,
        customizeConsent,
        hasCategoryConsent,
    } = useConsent();

    return (
        <>
            <Routes>
                {/* Suas rotas */}
            </Routes>
            
            <ConsentBanner
                show={showBanner}
                onAcceptAll={acceptAll}
                onAcceptNecessary={acceptNecessary}
                onCustomize={customizeConsent}
                onClose={() => {}}
            />
        </>
    );
}
```

### Verificar Consentimento
```typescript
import { useConsent } from '@/hooks/useConsent';

function AnalyticsComponent() {
    const { hasCategoryConsent } = useConsent();

    if (!hasCategoryConsent('analytics')) {
        return <div>Analytics requer consentimento</div>;
    }

    return <GoogleAnalytics />;
}
```

### Timeout de Sessão
```typescript
import { useSessionTimeout } from '@/hooks/useConsent';

function ProtectedComponent() {
    const { isExpired, extendSession } = useSessionTimeout(30); // 30 minutos

    if (isExpired) {
        return (
            <div>
                <p>Sessão expirada por segurança</p>
                <button onClick={extendSession}>Estender Sessão</button>
            </div>
        );
    }

    return <SensitiveData />;
}
```

---

## 6. Redaction de PII

### Uso Automático (Middleware)
```python
# O redaction já está aplicado no middleware
# Logs automaticamente redactam PII
logger.info(f"User email: {user_email}")  # Email será redactado
```

### Uso Manual
```python
from middleware.redaction import redact_payload, redact_url

# Redact payload
data = {"email": "user@example.com", "cpf": "123.456.789-00"}
redacted = redact_payload(data)
# {'email': '[redacted-email]', 'cpf': '[redacted-cpf]'}

# Redact URL
url = "https://api.com/user?token=secret123&email=user@example.com"
redacted_url = redact_url(url)
# 'https://api.com/user?token=[redacted]&email=[redacted-email]'
```

---

## 7. Monitoramento e Métricas

### Métricas Customizadas
```python
from opentelemetry import metrics

meter = metrics.get_meter("climateai")
counter = meter.create_counter("api_calls_total")

# Incrementar contador
counter.add(1, {"endpoint": "/weather", "status": "success"})
```

### Tracing Manual
```python
from opentelemetry import trace

tracer = trace.get_tracer("climateai")

with tracer.start_as_current_span("process_weather_data") as span:
    span.set_attribute("latitude", -23.55)
    span.set_attribute("longitude", -46.63)
    
    # Seu código
    result = process_data()
    
    span.set_attribute("result", result)
```

---

## 8. Health Checks

### Endpoint de Saúde
```python
# Já disponível em /health
# Retorna:
{
    "status": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "external_apis": {
        "noaa": "healthy",
        "openmeteo": "healthy"
    }
}
```

### Health Check do Cache
```python
from lib.redis_cache import get_cache

cache = get_cache()
health = await cache.health_check()
# {'status': 'healthy', 'used_memory_mb': '50MB', ...}
```

### Health Check do Rate Limiter
```python
from middleware.advanced_rate_limiter import rate_limiter

stats = rate_limiter.get_stats()
# {'total_requests': 1000, 'blocked_requests': 50, ...}
```

---

## 9. Configuração no Docker Compose

### Adicionar ao docker-compose.yml
```yaml
services:
  backend:
    environment:
      # OpenTelemetry
      - OTEL_ENABLED=true
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
      - OTEL_SERVICE_NAME=climateai-backend
      
      # Redis
      - REDIS_URL=redis://redis:6379
      
      # Rate Limiting
      - RATE_LIMIT_ENABLED=true
      
    depends_on:
      - redis
      - otel-collector
```

---

## 10. Comandos Úteis

### Iniciar Stack
```bash
# Tudo
./scripts/start-monitoring.sh

# Apenas monitoring
docker-compose -f docker-compose.otel.yml up -d

# Ver logs
docker-compose -f docker-compose.yml -f docker-compose.otel.yml logs -f
```

### Testar Localmente
```bash
# Testar circuit breaker
curl http://localhost:8000/health

# Testar rate limiting
for i in {1..20}; do curl http://localhost:8000/api/v1/test; done

# Ver métricas
curl http://localhost:8000/metrics
```

---

## 📚 Referências Rápidas

| Funcionalidade | Arquivo | Exemplo |
|----------------|---------|---------|
| Circuit Breaker | `server/lib/resilient_http_client.py` | `create_resilient_client()` |
| Caching | `server/lib/redis_cache.py` | `@external_api_cache()` |
| Rate Limiting | `server/middleware/advanced_rate_limiter.py` | `rate_limiter.is_allowed()` |
| X-Request-ID | `client/src/lib/requestId.ts` | `getDefaultHeaders()` |
| Consentimento | `client/src/hooks/useConsent.ts` | `useConsent()` |
| Redaction | `server/middleware/redaction.py` | `redact_payload()` |

---

*Guia criado em: Fevereiro 2026*
*Versão: 1.0*

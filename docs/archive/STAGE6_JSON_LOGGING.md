# 📊 Etapa 6: JSON Logging Estruturado

**Status:** ✅ CONCLUÍDO
**Data:** 20 de outubro de 2025
**Impacto:** Observabilidade em produção, integração ELK Stack, debugging distribuído

## 🎯 Objetivos Alcançados

### 1. **JSON Structured Logging** ✅
```json
{
  "timestamp": "2025-10-20T14:30:45.123Z",
  "level": "INFO",
  "logger": "fimce",
  "message": "API request processed",
  "request_id": "uuid-1234-5678",
  "user_id": "user_123",
  "session_id": "session_456",
  "category": "api_request",
  "source": {
    "file": "main.py",
    "function": "dispatch",
    "line": 45
  },
  "extra": {
    "method": "GET",
    "path": "/api/v1/clima",
    "status_code": 200,
    "response_time_ms": 125.5
  }
}
```

### 2. **Rastreamento Distribuído (Correlation IDs)** ✅
- `request_id`: ID único para rastrear uma requisição através do sistema
- `user_id`: Identificar qual usuário fez a requisição
- `session_id`: Agrupar requisições da mesma sessão
- Context variables para propagação automática

### 3. **Categorias de Eventos** ✅
```python
LogCategory.API_REQUEST         # Requisições HTTP recebidas
LogCategory.API_RESPONSE        # Respostas HTTP enviadas
LogCategory.DATABASE            # Queries ao banco de dados
LogCategory.CACHE               # Operações de cache
LogCategory.EXTERNAL_API        # Chamadas a APIs externas
LogCategory.SECURITY            # Eventos de segurança
LogCategory.PERFORMANCE         # Métricas de performance
LogCategory.ERROR               # Erros e exceções
LogCategory.HEALTH_CHECK        # Verificações de saúde
LogCategory.AUTHENTICATION      # Autenticação
LogCategory.AUTHORIZATION       # Autorização
```

### 4. **Middleware de Logging HTTP** ✅
- Registra todas as requisições e respostas
- Calcula tempo de resposta automaticamente
- Detecta erros HTTP (4xx, 5xx)
- Propaga request_id nos headers da resposta

### 5. **StructuredLogger Helper** ✅
```python
# Logging de queries ao banco de dados
structured_logger.log_database_query(
    query="SELECT * FROM clima WHERE data > ?",
    duration_ms=15.5,
    rows_affected=1250
)

# Logging de operações de cache
structured_logger.log_cache_operation(
    operation="get",
    key="climate_data:lat_-25",
    duration_ms=2.3,
    hit=True
)

# Logging de chamadas a APIs externas
structured_logger.log_external_api_call(
    api_name="open-meteo",
    endpoint="/v1/forecast",
    method="GET",
    status_code=200,
    duration_ms=245.8
)

# Logging de eventos de segurança
structured_logger.log_security_event(
    event_type="login_success",
    user_id="user_123"
)

# Logging de métricas de performance
structured_logger.log_performance_metric(
    metric_name="api_response_time",
    value=125.5,
    unit="ms",
    threshold=100
)
```

## 📁 Arquivos Criados/Modificados

### Novos Arquivos:
1. **`server/api/logging.py`** (500+ linhas)
   - `JSONFormatter`: Formatter personalizado para JSON
   - `LoggingMiddleware`: Middleware para requisições HTTP
   - `StructuredLogger`: Helper para logging estruturado
   - `LogContext`: Context manager para logging automático
   - Context variables para rastreamento distribuído

### Arquivos Modificados:
1. **`server/main.py`**
   - ✅ Adicionadas importações de logging
   - ✅ Inicializado `init_logging()` após criar app
   - ✅ Adicionado `LoggingMiddleware` ao app
   - ✅ Removido logging basicConfig antigo

## 🔗 Integração com ELK Stack

### Docker Compose com Elasticsearch + Logstash + Kibana

```yaml
version: '3.9'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000/udp"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://...
      LOG_LEVEL: INFO
    depends_on:
      - logstash
    # Logs para Logstash
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  elasticsearch_data:
```

### Configuração do Logstash

```conf
input {
  stdin { }
  # Para produção, usar journald, syslog, ou files
  file {
    path => "/var/log/fimce/app.json"
    codec => json
    start_position => "beginning"
  }
}

filter {
  json {
    source => "message"
  }

  # Extrair informações de performance
  if [response_time_ms] {
    mutate {
      convert => { "response_time_ms" => "float" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "fimce-logs-%{+YYYY.MM.dd}"
  }

  # Também para stdout para debug
  stdout {
    codec => rubydebug
  }
}
```

### Queries Kibana

```json
// Requisições lenta (>100ms)
response_time_ms > 100

// Erros HTTP
status_code >= 400

// Eventos de segurança
category: security

// Por usuário
user_id: "user_123"

// Por correlação
request_id: "specific-uuid"

// APIs externas lentas
category: external_api AND response_time_ms > 500
```

## 📊 Campos no JSON Log

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `timestamp` | string | ISO 8601 timestamp |
| `level` | string | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `logger` | string | Nome do logger |
| `message` | string | Mensagem principal |
| `request_id` | string | UUID para rastreamento |
| `user_id` | string | ID do usuário (opcional) |
| `session_id` | string | ID da sessão (opcional) |
| `category` | string | Categoria do evento |
| `source.file` | string | Nome do arquivo .py |
| `source.function` | string | Nome da função |
| `source.line` | number | Número da linha |
| `exception.type` | string | Tipo de exceção (se houver) |
| `exception.message` | string | Mensagem da exceção |
| `exception.traceback` | string | Stack trace completo |
| `extra` | object | Dados estruturados específicos |

## 🚀 Uso na Aplicação

### 1. Logging Manual com StructuredLogger

```python
from api.logging import get_structured_logger

logger = get_structured_logger()

# Database
logger.log_database_query(
    query="SELECT * FROM clima",
    duration_ms=25.3,
    rows_affected=500
)

# Cache
logger.log_cache_operation(
    operation="set",
    key="clima:cache",
    duration_ms=1.2
)

# External API
logger.log_external_api_call(
    api_name="open-meteo",
    endpoint="/v1/forecast",
    method="GET",
    status_code=200,
    duration_ms=234.5
)

# Segurança
logger.log_security_event(
    event_type="failed_auth",
    user_id="user_123",
    details={"reason": "invalid_token"}
)

# Performance
logger.log_performance_metric(
    metric_name="processing_time",
    value=450.2,
    unit="ms",
    threshold=500
)
```

### 2. Usando Context Manager LogContext

```python
from api.logging import LogContext, get_logger

async def process_climate_data():
    async with LogContext(
        get_logger(),
        "processing_climate_data",
        {"region": "south", "year": 2025}
    ):
        # Seu código aqui
        result = await fetch_data()
        # Tempo é registrado automaticamente ao sair
        return result
```

### 3. Middleware Automático de Requisições

```
Todas as requisições HTTP são registradas automaticamente:

GET /api/v1/clima -> 200 (145.2ms)
POST /api/v1/previsao -> 201 (234.5ms)
GET /api/v1/health -> 200 (5.3ms)
```

## 📈 Exemplo de Análise em Kibana

### Dashboard de Performance
- Requisições por segundo
- Tempo médio de resposta por endpoint
- Taxa de erro (5xx)
- Latência p95, p99

### Dashboard de Segurança
- Tentativas de login falhadas
- Rate limit violations
- Acessos não autorizados

### Dashboard de Saúde
- Status dos health checks
- Tempo de resposta do banco de dados
- Conexões ativas no Redis
- CPU/Memória do servidor

## 🔍 Troubleshooting

### Logs não aparecem em Elasticsearch

1. Verificar se a aplicação está escrevendo em arquivo:
```bash
tail -f /var/log/fimce/app.json
```

2. Verificar se Logstash está lendo o arquivo:
```bash
docker logs logstash
```

3. Verificar Elasticsearch:
```bash
curl http://localhost:9200/_cat/indices
```

### Logs muito grandes

Usar sampler em Logstash:
```conf
filter {
  if [category] == "api_request" {
    # Sample 10% dos logs de requisição
    mutate {
      add_field => { "[@metadata][sample]" => "10" }
    }
  }
}
```

## 📋 Checklist de Validação

- ✅ `server/api/logging.py` criado com JSON formatter
- ✅ `server/main.py` importa logging estruturado
- ✅ `LoggingMiddleware` adiciona correlação IDs
- ✅ Todos os logs são em JSON
- ✅ Context variables para user_id, session_id, request_id
- ✅ StructuredLogger com helpers específicos
- ✅ LogContext para logging automático de operações
- ✅ Integração com ELK Stack documentada
- ✅ Middleware registra todas requisições HTTP

## 🔄 Próxima Etapa

**Etapa 7: Database Backups** (Backup Automation)
- Backup automático para S3/Google Cloud
- Verificação de integridade
- Restore procedures
- Retenção e limpeza automática

---

**Tempo Total de Implementação:** ~2 horas
**Complexidade:** ⭐⭐⭐⭐ (Média-Alta)
**Manutenibilidade:** ⭐⭐⭐⭐⭐ (Excelente)

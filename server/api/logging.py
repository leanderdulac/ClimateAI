"""
Sistema de Logging Estruturado em JSON para FIMCE

Integração com ELK Stack (Elasticsearch, Logstash, Kibana) e CloudWatch
Suporta correlation IDs para rastreamento distribuído e análise detalhada
"""

import json
import logging
import time
import traceback
import uuid
import warnings
from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Tentar importar pythonjsonlogger, se não disponível, usar implementação manual
try:
    from pythonjsonlogger import jsonlogger

    HAS_JSON_LOGGER = True
except ImportError:
    jsonlogger = None
    HAS_JSON_LOGGER = False

# ============================================================================
# Context Variables para Rastreamento Distribuído
# ============================================================================

# ID único para rastrear uma requisição através de todo o sistema
request_id_contextvar: ContextVar[Optional[str]] = ContextVar(
    "request_id", default=None
)
user_id_contextvar: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
session_id_contextvar: ContextVar[Optional[str]] = ContextVar(
    "session_id", default=None
)


# ============================================================================
# Enums para Categorização de Logs
# ============================================================================


class LogLevel(Enum):
    """Níveis de log com prioridade"""

    DEBUG = logging.DEBUG  # Informações detalhadas para debugging
    INFO = logging.INFO  # Eventos normais
    WARNING = logging.WARNING  # Situações anormais, mas recuperáveis
    ERROR = logging.ERROR  # Erros que devem ser investigados
    CRITICAL = logging.CRITICAL  # Erros graves que podem derrubar o sistema


class LogCategory(Enum):
    """Categorias de eventos para melhor filtragem"""

    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    HEALTH_CHECK = "health_check"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"


# ============================================================================
# JSON Log Formatter Personalizado
# ============================================================================

if HAS_JSON_LOGGER:

    class JSONFormatter(jsonlogger.JsonFormatter):
        """
        Formatter personalizado para logs em JSON com campos estruturados
        """

        def add_fields(self, log_record, record, message_dict):
            """Adicionar campos customizados ao log JSON"""
            super().add_fields(log_record, record, message_dict)

            # Timestamp em ISO 8601
            log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # Informações de contexto distribuído
            log_record["request_id"] = request_id_contextvar.get()
            log_record["user_id"] = user_id_contextvar.get()
            log_record["session_id"] = session_id_contextvar.get()

            # Nível de log com nome e valor
            log_record["level"] = record.levelname
            log_record["logger"] = record.name

            # Stack trace para erros
            if record.exc_info:
                log_record["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": traceback.format_exc(),
                }

            # Nome do arquivo e linha
            log_record["source"] = {
                "file": record.filename,
                "function": record.funcName,
                "line": record.lineno,
            }

            # Categoria do log (se fornecida)
            if hasattr(record, "category"):
                log_record["category"] = record.category

            # Dados estruturados adicionais
            if hasattr(record, "extra_data"):
                log_record["extra"] = record.extra_data

else:
    # Implementação manual de JSON formatter se pythonjsonlogger não estiver disponível
    class JSONFormatter(logging.Formatter):
        """
        Formatter que escreve logs em JSON (implementação manual)
        """

        def format(self, record: logging.LogRecord) -> str:
            """Formatar record como JSON"""

            log_obj = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "request_id": request_id_contextvar.get(),
                "user_id": user_id_contextvar.get(),
                "session_id": session_id_contextvar.get(),
                "source": {
                    "file": record.filename,
                    "function": record.funcName,
                    "line": record.lineno,
                },
            }

            # Stack trace para erros
            if record.exc_info:
                log_obj["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": traceback.format_exc(),
                }

            # Categoria do log (se fornecida no extra)
            if hasattr(record, "category"):
                log_obj["category"] = record.category

            # Dados estruturados adicionais
            if hasattr(record, "extra_data"):
                log_obj["extra"] = record.extra_data

            return json.dumps(log_obj, default=str)


# ============================================================================
# Logger Factory
# ============================================================================


def setup_json_logging(
    app_name: str = "fimce", level: int = logging.INFO
) -> logging.Logger:
    """
    Configurar logging estruturado em JSON para toda a aplicação

    Args:
        app_name: Nome da aplicação para identificação nos logs
        level: Nível mínimo de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger configurado com JSON formatter
    """

    # Criar logger
    logger = logging.getLogger(app_name)
    logger.setLevel(level)

    # Remover handlers existentes para evitar duplicação
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Handler para console (STDOUT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # Handler para arquivo (opcional em produção, geralmente enviado via ELK)
    try:
        file_handler = logging.FileHandler("/var/log/fimce/app.json")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    except (OSError, PermissionError):
        # Se não conseguir escrever em /var/log, apenas usar console
        pass

    return logger


# ============================================================================
# Middleware de Logging para Requisições HTTP
# ============================================================================


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que registra todas as requisições e respostas HTTP
    em formato JSON estruturado
    """

    def __init__(self, app, logger: logging.Logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next) -> Response:
        """Processar requisição e registrar em log"""

        # Gerar IDs únicos para rastreamento
        request_id = str(uuid.uuid4())
        request_id_contextvar.set(request_id)

        # Extrair informações da requisição
        request_start_time = time.time()

        # Tentar extrair user_id e session_id dos headers/cookies
        user_id = request.headers.get("X-User-ID")
        session_id = request.cookies.get("session_id")

        if user_id:
            user_id_contextvar.set(user_id)
        if session_id:
            session_id_contextvar.set(session_id)

        # Dados da requisição
        request_data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else {},
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # Log da requisição recebida
        self.logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "category": LogCategory.API_REQUEST.value,
                "extra_data": request_data,
            },
        )

        try:
            # Chamar a próxima middleware/rota
            response = await call_next(request)

        except Exception as e:
            # Log de erro durante processamento
            response_time = (time.time() - request_start_time) * 1000

            self.logger.error(
                f"Error processing {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "category": LogCategory.ERROR.value,
                    "extra_data": {
                        **request_data,
                        "error": str(e),
                        "response_time_ms": response_time,
                    },
                },
            )
            raise

        # Calcular tempo de resposta
        response_time = (time.time() - request_start_time) * 1000

        # Dados da resposta
        response_data = {
            "status_code": response.status_code,
            "response_time_ms": response_time,
        }

        # Log da resposta
        log_level = (
            logging.ERROR
            if response.status_code >= 500
            else logging.WARNING if response.status_code >= 400 else logging.INFO
        )

        self.logger.log(
            log_level,
            f"{request.method} {request.url.path} -> {response.status_code}",
            extra={
                "category": LogCategory.API_RESPONSE.value,
                "extra_data": {**request_data, **response_data},
            },
        )

        # Adicionar request_id no header da resposta para facilitar debugging
        response.headers["X-Request-ID"] = request_id

        return response


# ============================================================================
# Helpers de Logging Estruturado
# ============================================================================


class StructuredLogger:
    """
    Wrapper para logging estruturado com métodos convenientes
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_database_query(
        self,
        query: str,
        duration_ms: float,
        rows_affected: int = 0,
        error: Optional[str] = None,
    ):
        """Log de query ao banco de dados"""

        level = logging.ERROR if error else logging.DEBUG
        message = f"Database query: {query[:100]}..."

        extra_data = {
            "query": query,
            "duration_ms": duration_ms,
            "rows_affected": rows_affected,
        }

        if error:
            extra_data["error"] = error

        self.logger.log(
            level,
            message,
            extra={"category": LogCategory.DATABASE.value, "extra_data": extra_data},
        )

    def log_cache_operation(
        self,
        operation: str,  # 'get', 'set', 'delete', 'clear'
        key: str,
        duration_ms: float,
        hit: Optional[bool] = None,
        error: Optional[str] = None,
    ):
        """Log de operação de cache"""

        level = logging.ERROR if error else logging.DEBUG
        message = f"Cache {operation}: {key}"

        extra_data = {
            "operation": operation,
            "key": key,
            "duration_ms": duration_ms,
        }

        if hit is not None:
            extra_data["hit"] = hit
        if error:
            extra_data["error"] = error

        self.logger.log(
            level,
            message,
            extra={"category": LogCategory.CACHE.value, "extra_data": extra_data},
        )

    def log_external_api_call(
        self,
        api_name: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        error: Optional[str] = None,
    ):
        """Log de chamada a API externa"""

        level = (
            logging.ERROR
            if status_code >= 500 or error
            else logging.WARNING if status_code >= 400 else logging.INFO
        )

        message = f"External API: {api_name} {method} {endpoint} -> {status_code}"

        extra_data = {
            "api_name": api_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }

        if error:
            extra_data["error"] = error

        self.logger.log(
            level,
            message,
            extra={
                "category": LogCategory.EXTERNAL_API.value,
                "extra_data": extra_data,
            },
        )

    def log_security_event(
        self,
        event_type: str,  # 'login', 'logout', 'failed_auth', 'rate_limit', etc
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log de evento de segurança"""

        extra_data = {
            "event_type": event_type,
            "user_id": user_id,
        }

        if details:
            extra_data.update(details)

        self.logger.warning(
            f"Security event: {event_type}",
            extra={"category": LogCategory.SECURITY.value, "extra_data": extra_data},
        )

    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        threshold: Optional[float] = None,
    ):
        """Log de métrica de performance"""

        exceeded_threshold = threshold is not None and value > threshold

        level = logging.WARNING if exceeded_threshold else logging.INFO
        message = f"Performance: {metric_name}={value}{unit}"

        extra_data = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
        }

        if threshold is not None:
            extra_data["threshold"] = threshold
            extra_data["exceeded"] = exceeded_threshold

        self.logger.log(
            level,
            message,
            extra={"category": LogCategory.PERFORMANCE.value, "extra_data": extra_data},
        )

    def log_health_check_result(
        self,
        check_name: str,
        status: str,  # 'healthy', 'degraded', 'unhealthy'
        duration_ms: float,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log de resultado de health check"""

        level = (
            logging.ERROR
            if status == "unhealthy"
            else logging.WARNING if status == "degraded" else logging.INFO
        )

        message = f"Health check: {check_name} -> {status}"

        extra_data = {
            "check_name": check_name,
            "status": status,
            "duration_ms": duration_ms,
        }

        if details:
            extra_data.update(details)

        self.logger.log(
            level,
            message,
            extra={
                "category": LogCategory.HEALTH_CHECK.value,
                "extra_data": extra_data,
            },
        )


# ============================================================================
# Context Manager para Logging de Operações
# ============================================================================


class LogContext:
    """
    Context manager para logging automático de blocos de código

    Exemplo:
        async with LogContext(logger, "processing_request", {"user_id": 123}):
            # sua lógica aqui
            pass
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation_name: str,
        context_data: Optional[Dict[str, Any]] = None,
        log_level: int = logging.INFO,
    ):
        self.logger = logger
        self.operation_name = operation_name
        self.context_data = context_data or {}
        self.log_level = log_level
        self.start_time = None

    async def __aenter__(self):
        """Executado ao entrar no bloco"""
        self.start_time = time.time()
        self.logger.log(
            self.log_level,
            f"Starting: {self.operation_name}",
            extra={
                "category": LogCategory.PERFORMANCE.value,
                "extra_data": {
                    "operation": self.operation_name,
                    "started": True,
                    **self.context_data,
                },
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Executado ao sair do bloco"""
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type is not None:
            # Erro ocorreu
            self.logger.error(
                f"Failed: {self.operation_name}",
                exc_info=(exc_type, exc_val, exc_tb),
                extra={
                    "category": LogCategory.ERROR.value,
                    "extra_data": {
                        "operation": self.operation_name,
                        "duration_ms": duration_ms,
                        "error": str(exc_val),
                        **self.context_data,
                    },
                },
            )
        else:
            # Sucesso
            self.logger.log(
                self.log_level,
                f"Completed: {self.operation_name}",
                extra={
                    "category": LogCategory.PERFORMANCE.value,
                    "extra_data": {
                        "operation": self.operation_name,
                        "duration_ms": duration_ms,
                        "completed": True,
                        **self.context_data,
                    },
                },
            )

        return False


# ============================================================================
# Inicialização Padrão
# ============================================================================

# Logger global (inicializar no startup da aplicação)
logger: Optional[logging.Logger] = None
structured_logger: Optional[StructuredLogger] = None


def init_logging(app_name: str = "fimce", level: int = logging.INFO):
    """Inicializar logging estruturado"""
    global logger, structured_logger

    # Silenciar avisos de depreciação de bibliotecas externas para o pitch
    # Mantém os logs limpos de mensagens recorrentes de SDKs
    warnings.filterwarnings("ignore", category=FutureWarning, module="google.*")
    warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.*")

    logger = setup_json_logging(app_name, level)
    structured_logger = StructuredLogger(logger)

    logger.info(
        f"Logging initialized",
        extra={
            "category": LogCategory.STARTUP.value,
            "extra_data": {
                "app_name": app_name,
                "log_level": logging.getLevelName(level),
            },
        },
    )


def get_logger() -> Optional[logging.Logger]:
    """Obter logger global"""
    return logger


def get_structured_logger() -> Optional[StructuredLogger]:
    """Obter structured logger global"""
    return structured_logger

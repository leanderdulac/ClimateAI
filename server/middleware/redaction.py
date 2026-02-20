import re
from typing import Dict, Any, List, Optional, Set
import logging

logger = logging.getLogger(__name__)

# Chaves sensíveis a serem removidas ou redactadas
SENSITIVE_KEYS: Set[str] = {
    "password", "pass", "passwd", "pwd",
    "token", "access_token", "refresh_token", "auth_token", "jwt",
    "secret", "secret_key", "client_secret",
    "api_key", "apikey", "api-key", "x-api-key",
    "authorization", "auth",
    "cookie", "set-cookie",
    "private_key", "privatekey",
    "credential", "credentials",
    "session_id", "sessionid", "sid",
    "user_id", "userid", "uid",
    "email", "e-mail",
    "cpf", "cnpj",
    "credit_card", "creditcard", "card_number", "cc_number",
    "ssn", "social_security",
    "phone", "telephone", "cellphone",
    "address", "street", "logradouro",
    "birth_date", "birthdate", "dob",
    "ip_address", "ip",
    "latitude", "longitude",  # PII geográfico (opcional, dependendo do caso de uso)
}

# Padrões regex para detecção e redaction de PII
SENSITIVE_PATTERNS: List[tuple] = [
    # Email
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[redacted-email]'),
    # CPF (brasileiro)
    (re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'), '[redacted-cpf]'),
    (re.compile(r'\b\d{11}\b'), '[redacted-cpf-plain]'),  # CPF sem formatação (cuidado com falsos positivos)
    # CNPJ (brasileiro)
    (re.compile(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b'), '[redacted-cnpj]'),
    (re.compile(r'\b\d{14}\b'), '[redacted-cnpj-plain]'),  # CNPJ sem formatação
    # Cartão de crédito
    (re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'), '[redacted-cc]'),
    # Telefone (formatos variados)
    (re.compile(r'\+?\d{1,3}[\s.-]?\(?\d{2,3}\)?[\s.-]?\d{3,4}[\s.-]?\d{4}\b'), '[redacted-phone]'),
    # CEP (brasileiro)
    (re.compile(r'\b\d{5}-?\d{3}\b'), '[redacted-cep]'),
    # IP address (IPv4)
    (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), '[redacted-ip]'),
    # URL com query parameters sensíveis
    (re.compile(r'([?&])(password|token|secret|key|api_key|apikey)=([^&]+)'), r'\1\2=[redacted]'),
]

# Campos que devem ser mantidos (whitelist)
ALLOWED_KEYS: Set[str] = {
    "service.name", "service.version", "deployment.environment",
    "http.method", "http.url", "http.status_code", "http.target", "http.route",
    "http.request_content_length", "http.response_content_length",
    "db.system", "db.operation", "db.statement", "db.instance",
    "net.peer.name", "net.peer.port", "net.host.name", "net.host.port",
    "traceparent", "tracestate", "x-request-id", "x-correlation-id",
    "span.kind", "span.status",
    "error.type", "error.message",
    "x-forwarded-for", "x-real-ip",  # Headers de proxy (não redactar para debugging)
}


def redact_value(value: Any, max_length: int = 80) -> Any:
    """
    Redact um valor individual, aplicando padrões regex para PII.
    
    Args:
        value: O valor a ser redactado
        max_length: Comprimento máximo antes de truncar tokens longos
        
    Returns:
        Valor redactado
    """
    if not isinstance(value, str):
        return value
    
    # Aplicar todos os padrões de redaction
    for pattern, replacement in SENSITIVE_PATTERNS:
        value = pattern.sub(replacement, value)
    
    # Mask long tokens (possíveis secrets)
    if len(value) > max_length:
        return value[:6] + "…[redacted]…" + value[-4:] if len(value) > 20 else value[:6] + "…[redacted]…"
    
    return value


def redact_payload(
    data: Any,
    sensitive_keys: Optional[Set[str]] = None,
    allowed_keys: Optional[Set[str]] = None,
    depth: int = 0,
    max_depth: int = 50
) -> Any:
    """
    Redact recursivamente um payload, removendo ou mascarando dados sensíveis.
    
    Args:
        data: Os dados a serem redactados (dict, list, ou valor primitivo)
        sensitive_keys: Conjunto adicional de chaves sensíveis
        allowed_keys: Conjunto de chaves permitidas (whitelist)
        depth: Profundidade atual da recursão
        max_depth: Profundidade máxima para evitar stack overflow
        
    Returns:
        Dados redactados
    """
    if depth > max_depth:
        logger.warning(f"Max redaction depth ({max_depth}) exceeded, returning data as-is")
        return data
    
    # Unir com padrões globais
    effective_sensitive = SENSITIVE_KEYS.union(sensitive_keys or set())
    effective_allowed = ALLOWED_KEYS.union(allowed_keys or set())
    
    if isinstance(data, dict):
        sanitized: Dict[str, Any] = {}
        for k, v in data.items():
            k_lower = k.lower()
            
            # Verificar whitelist primeiro
            if k_lower in effective_allowed or k in effective_allowed:
                sanitized[k] = redact_payload(v, sensitive_keys, allowed_keys, depth + 1, max_depth)
            # Verificar blacklist
            elif k_lower in effective_sensitive:
                sanitized[k] = "[redacted]"
                logger.debug(f"Redacted sensitive key: {k}")
            else:
                sanitized[k] = redact_payload(v, sensitive_keys, allowed_keys, depth + 1, max_depth)
        return sanitized
    
    if isinstance(data, list):
        return [redact_payload(x, sensitive_keys, allowed_keys, depth + 1, max_depth) for x in data]
    
    if isinstance(data, tuple):
        return tuple(redact_payload(x, sensitive_keys, allowed_keys, depth + 1, max_depth) for x in data)
    
    return redact_value(data)


def redact_url(url: str) -> str:
    """
    Redact parâmetros sensíveis em uma URL.
    
    Args:
        url: URL a ser redactada
        
    Returns:
        URL com parâmetros sensíveis redactados
    """
    if not url:
        return url
    
    for pattern, replacement in SENSITIVE_PATTERNS:
        url = pattern.sub(replacement, url)
    
    return url


def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Redact headers HTTP sensíveis.
    
    Args:
        headers: Dicionário de headers HTTP
        
    Returns:
        Headers redactados
    """
    if not headers:
        return headers
    
    sanitized = {}
    for k, v in headers.items():
        k_lower = k.lower()
        if k_lower in SENSITIVE_KEYS:
            sanitized[k] = "[redacted]"
        elif k_lower in ALLOWED_KEYS:
            sanitized[k] = v
        else:
            sanitized[k] = redact_value(v)
    
    return sanitized


def get_redaction_stats(data: Any) -> Dict[str, int]:
    """
    Obter estatísticas sobre o que foi redactado.
    
    Args:
        data: Dados originais (antes do redaction)
        
    Returns:
        Estatísticas de redaction
    """
    stats = {
        "redacted_keys": 0,
        "redacted_values": 0,
        "total_keys": 0,
    }
    
    def count_stats(d: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        if isinstance(d, dict):
            for k, v in d.items():
                stats["total_keys"] += 1
                if k.lower() in SENSITIVE_KEYS:
                    stats["redacted_keys"] += 1
                else:
                    count_stats(v, depth + 1)
        elif isinstance(d, list):
            for item in d:
                count_stats(item, depth + 1)
        elif isinstance(d, str):
            for pattern, _ in SENSITIVE_PATTERNS:
                if pattern.search(d):
                    stats["redacted_values"] += 1
                    break
    
    count_stats(data)
    return stats

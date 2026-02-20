"""
HTTP Client Resiliente com Circuit Breaker, Retry e Timeout
Implementa padrões de resiliência para integrações com APIs externas (NOAA, OpenMeteo, Embrapa, xWeather)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
    RetryCallState,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Estados do Circuit Breaker"""
    CLOSED = "closed"      # Normal, requisições passam
    OPEN = "open"          # Circuito aberto, requisições falham imediatamente
    HALF_OPEN = "half_open"  # Testando se o serviço recuperou


@dataclass
class CircuitBreakerConfig:
    """Configuração do Circuit Breaker"""
    failure_threshold: int = 5          # Número de falhas para abrir o circuito
    success_threshold: int = 2          # Número de sucessos para fechar o circuito
    timeout: float = 60.0               # Tempo em segundos antes de tentar novamente (OPEN -> HALF_OPEN)
    half_open_max_calls: int = 3        # Máximo de chamadas permitidas em HALF_OPEN


@dataclass
class RetryConfig:
    """Configuração de Retry"""
    max_attempts: int = 3
    base_delay: float = 1.0             # Delay base em segundos
    max_delay: float = 60.0             # Delay máximo em segundos
    exponential_base: float = 2.0       # Base para backoff exponencial
    jitter: bool = True                 # Adicionar jitter aleatório
    retryable_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    retryable_exceptions: List[type] = field(default_factory=lambda: [
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.ReadTimeout,
        httpx.WriteTimeout,
        httpx.RemoteProtocolError,
    ])


@dataclass
class TimeoutConfig:
    """Configuração de Timeout"""
    connect_timeout: float = 5.0        # Timeout para conexão
    read_timeout: float = 30.0          # Timeout para leitura
    write_timeout: float = 10.0         # Timeout para escrita
    pool_timeout: float = 5.0           # Timeout para obter conexão do pool


@dataclass
class CircuitBreakerStats:
    """Estatísticas do Circuit Breaker"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    state_changed_at: float = field(default_factory=time.time)


class CircuitBreakerOpen(Exception):
    """Exceção levantada quando o circuit breaker está aberto"""
    def __init__(self, service_name: str, retry_after: float):
        self.service_name = service_name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker OPEN for {service_name}. Retry after {retry_after:.1f}s")


class ResilientHttpClient:
    """
    Cliente HTTP resiliente com Circuit Breaker, Retry e Timeout.
    
    Uso:
        client = ResilientHttpClient("noaa", base_url="https://api.noaa.gov")
        response = await client.get("/stations")
    """
    
    def __init__(
        self,
        service_name: str,
        base_url: str = "",
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        timeout_config: Optional[TimeoutConfig] = None,
        default_headers: Optional[Dict[str, str]] = None,
        api_key: Optional[str] = None,
        api_key_header: str = "X-API-Key",
    ):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        
        self.cb_config = circuit_breaker_config or CircuitBreakerConfig()
        self.retry_config = retry_config or RetryConfig()
        self.timeout_config = timeout_config or TimeoutConfig()
        
        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        # Configurar headers padrão
        self._default_headers = default_headers or {}
        if api_key:
            self._default_headers[api_key_header] = api_key
        
        # Criar cliente HTTP com timeouts
        self._client = self._create_client()
        
        logger.info(f"ResilientHttpClient initialized for {service_name} (base_url={base_url})")
    
    def _create_client(self) -> httpx.AsyncClient:
        """Criar cliente HTTP com configurações de timeout"""
        timeout = httpx.Timeout(
            connect=self.timeout_config.connect_timeout,
            read=self.timeout_config.read_timeout,
            write=self.timeout_config.write_timeout,
            pool=self.timeout_config.pool_timeout,
        )
        
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0,
        )
        
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            limits=limits,
            headers=self._default_headers,
            follow_redirects=True,
        )
    
    @property
    def stats(self) -> CircuitBreakerStats:
        """Retorna estatísticas do circuit breaker"""
        return self._stats
    
    @property
    def state(self) -> CircuitState:
        """Retorna estado atual do circuit breaker"""
        return self._stats.state
    
    @property
    def is_available(self) -> bool:
        """Verifica se o serviço está disponível (circuito fechado ou half-open)"""
        return self._stats.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
    
    async def _check_circuit_breaker(self) -> None:
        """Verifica e atualiza estado do circuit breaker"""
        async with self._lock:
            if self._stats.state == CircuitState.OPEN:
                # Verificar se timeout passou
                if self._stats.last_failure_time:
                    elapsed = time.time() - self._stats.last_failure_time
                    if elapsed >= self.cb_config.timeout:
                        logger.info(f"Circuit breaker {self.service_name}: OPEN -> HALF_OPEN")
                        self._stats.state = CircuitState.HALF_OPEN
                        self._stats.success_count = 0
                        self._stats.state_changed_at = time.time()
                    else:
                        retry_after = self.cb_config.timeout - elapsed
                        raise CircuitBreakerOpen(self.service_name, retry_after)
    
    async def _record_success(self) -> None:
        """Registrar sucesso e atualizar circuit breaker"""
        async with self._lock:
            self._stats.success_count += 1
            self._stats.total_successes += 1
            self._stats.last_success_time = time.time()
            
            if self._stats.state == CircuitState.HALF_OPEN:
                if self._stats.success_count >= self.cb_config.success_threshold:
                    logger.info(f"Circuit breaker {self.service_name}: HALF_OPEN -> CLOSED")
                    self._stats.state = CircuitState.CLOSED
                    self._stats.failure_count = 0
                    self._stats.success_count = 0
                    self._stats.state_changed_at = time.time()
    
    async def _record_failure(self) -> None:
        """Registrar falha e atualizar circuit breaker"""
        async with self._lock:
            self._stats.failure_count += 1
            self._stats.total_failures += 1
            self._stats.last_failure_time = time.time()
            
            if self._stats.state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit breaker {self.service_name}: HALF_OPEN -> OPEN (falha no teste)")
                self._stats.state = CircuitState.OPEN
                self._stats.state_changed_at = time.time()
            elif self._stats.state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.cb_config.failure_threshold:
                    logger.warning(f"Circuit breaker {self.service_name}: CLOSED -> OPEN (threshold atingido)")
                    self._stats.state = CircuitState.OPEN
                    self._stats.state_changed_at = time.time()
    
    def _should_retry(self, response: httpx.Response) -> bool:
        """Verifica se a resposta deve ser retry"""
        return response.status_code in self.retry_config.retryable_status_codes
    
    async def _execute_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> httpx.Response:
        """Executar requisição com retry"""
        
        def after_retry(retry_state: RetryCallState) -> None:
            """Callback após cada tentativa de retry"""
            if retry_state.outcome:
                if retry_state.outcome.failed:
                    logger.warning(
                        f"Tentativa {retry_state.attempt_number} falhou para {method} {url}: "
                        f"{retry_state.outcome.exception()}"
                    )
                else:
                    result = retry_state.outcome.result()
                    if isinstance(result, httpx.Response):
                        logger.warning(
                            f"Tentativa {retry_state.attempt_number} retornou status {result.status_code} "
                            f"para {method} {url}"
                        )
        
        # Criar decorator de retry
        @retry(
            retry=(
                retry_if_exception_type(tuple(self.retry_config.retryable_exceptions)) |
                retry_if_result(self._should_retry)
            ),
            stop=stop_after_attempt(self.retry_config.max_attempts),
            wait=wait_exponential(
                multiplier=self.retry_config.exponential_base,
                min=self.retry_config.base_delay,
                max=self.retry_config.max_delay,
            ),
            after=after_retry,
            reraise=True,
        )
        async def _request() -> httpx.Response:
            return await self._client.request(method, url, **kwargs)
        
        return await _request()
    
    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Fazer requisição HTTP com resiliência completa.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            path: Path da URL (será combinado com base_url)
            headers: Headers adicionais
            max_retries: Sobrescrever número máximo de retries
            timeout: Sobrescrever timeout em segundos
            **kwargs: Argumentos adicionais para httpx
            
        Returns:
            Response da requisição
            
        Raises:
            CircuitBreakerOpen: Se o circuit breaker estiver aberto
            httpx.HTTPError: Se a requisição falhar após todos os retries
        """
        # Verificar circuit breaker
        await self._check_circuit_breaker()
        
        url = f"{self.base_url}{path}" if path.startswith('/') else f"{self.base_url}/{path}"
        
        # Mesclar headers
        request_headers = {**self._default_headers}
        if headers:
            request_headers.update(headers)
        
        # Configurar timeout se especificado
        if timeout:
            kwargs['timeout'] = httpx.Timeout(timeout)
        
        self._stats.total_calls += 1
        
        try:
            # Executar com retry
            response = await self._execute_with_retry(method, url, headers=request_headers, **kwargs)
            
            # Registrar sucesso/falha
            if response.status_code < 500:
                await self._record_success()
            else:
                await self._record_failure()
            
            return response
            
        except Exception as e:
            await self._record_failure()
            
            # Log detalhado para debugging
            logger.error(
                f"Requisição falhou para {self.service_name}: {method} {url} - "
                f"{type(e).__name__}: {str(e)}"
            )
            raise
    
    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Requisição GET"""
        return await self.request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Requisição POST"""
        return await self.request("POST", path, **kwargs)
    
    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Requisição PUT"""
        return await self.request("PUT", path, **kwargs)
    
    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Requisição DELETE"""
        return await self.request("DELETE", path, **kwargs)
    
    async def close(self) -> None:
        """Fechar cliente HTTP"""
        await self._client.aclose()
    
    async def __aenter__(self) -> 'ResilientHttpClient':
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde do cliente"""
        return {
            "service_name": self.service_name,
            "base_url": self.base_url,
            "circuit_state": self._stats.state.value,
            "is_available": self.is_available,
            "stats": {
                "total_calls": self._stats.total_calls,
                "total_successes": self._stats.total_successes,
                "total_failures": self._stats.total_failures,
                "failure_count": self._stats.failure_count,
                "success_count": self._stats.success_count,
                "last_failure_time": self._stats.last_failure_time,
                "last_success_time": self._stats.last_success_time,
            },
            "config": {
                "failure_threshold": self.cb_config.failure_threshold,
                "success_threshold": self.cb_config.success_threshold,
                "timeout": self.cb_config.timeout,
                "max_attempts": self.retry_config.max_attempts,
            }
        }


# Factory para criar clientes padronizados por serviço
def create_resilient_client(
    service_name: str,
    base_url: str,
    api_key: Optional[str] = None,
    api_key_header: str = "X-API-Key",
    timeout_seconds: float = 30.0,
    max_retries: int = 3,
) -> ResilientHttpClient:
    """
    Factory para criar clientes resilientes com configurações padrão.
    
    Args:
        service_name: Nome do serviço (ex: "noaa", "openmeteo", "embrapa")
        base_url: URL base da API
        api_key: API key (opcional)
        api_key_header: Nome do header para API key
        timeout_seconds: Timeout padrão em segundos
        max_retries: Número máximo de retries
        
    Returns:
        ResilientHttpClient configurado
    """
    timeout_config = TimeoutConfig(
        connect_timeout=min(5.0, timeout_seconds / 4),
        read_timeout=timeout_seconds / 2,
        write_timeout=timeout_seconds / 4,
        pool_timeout=5.0,
    )
    
    retry_config = RetryConfig(
        max_attempts=max_retries,
        base_delay=1.0,
        max_delay=30.0,
    )
    
    return ResilientHttpClient(
        service_name=service_name,
        base_url=base_url,
        api_key=api_key,
        api_key_header=api_key_header,
        timeout_config=timeout_config,
        retry_config=retry_config,
    )


# Decorator para adicionar resiliência a funções assíncronas
def with_resilience(
    service_name: str = "unknown",
    max_retries: int = 3,
    timeout: float = 30.0,
):
    """
    Decorator para adicionar resiliência a funções assíncronas.
    Implementa retry com backoff exponencial e timeout.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    last_exception = asyncio.TimeoutError(f"Timeout em {service_name}.{func.__name__} após {timeout}s")
                    logger.warning(f"Tentativa {attempt}/{max_retries} falhou por timeout: {service_name}.{func.__name__}")
                except Exception as e:
                    last_exception = e
                    # Se for erro de rate limit, esperar um pouco mais
                    error_msg = str(e)
                    if "429" in error_msg or "Rate Limit" in error_msg:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limit hit em {service_name}.{func.__name__}. Esperando {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"Tentativa {attempt}/{max_retries} falhou em {service_name}.{func.__name__}: {e}")
                
                # Backoff exponencial simples para outros erros
                if attempt < max_retries:
                    wait_time = 0.5 * (2 ** (attempt - 1))
                    await asyncio.sleep(wait_time)
            
            # Se chegou aqui, falhou após todos os retries
            logger.error(f"Todas as {max_retries} tentativas falharam para {service_name}.{func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator

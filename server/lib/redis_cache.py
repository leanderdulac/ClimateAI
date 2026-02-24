"""
Caching Redis Consistente para APIs Externas
Implementa caching com TTL, invalidação e fallback para provedores climáticos
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Awaitable
from functools import wraps
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStrategy(Enum):
    """Estratégias de caching"""
    CACHE_ALL = "cache_all"           # Cache tudo
    CACHE_SUCCESS_ONLY = "cache_success_only"  # Cache apenas sucessos
    NO_CACHE = "no_cache"             # Não cacheia
    CACHE_WITH_FALLBACK = "cache_with_fallback"  # Cache com fallback para dados stale


@dataclass
class CacheEntry:
    """Entrada de cache com metadata"""
    value: Any
    created_at: float
    expires_at: float
    key: str
    version: int = 1
    tags: List[str] = None
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def ttl_remaining(self) -> float:
        return max(0, self.expires_at - time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "key": self.key,
            "version": self.version,
            "tags": self.tags or [],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        return cls(
            value=data["value"],
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            key=data["key"],
            version=data.get("version", 1),
            tags=data.get("tags", []),
        )


@dataclass
class CacheStats:
    """Estatísticas de cache"""
    hits: int = 0
    misses: int = 0
    errors: int = 0
    stale_serves: int = 0  # Dados stale servidos como fallback
    invalidations: int = 0
    sets: int = 0
    deletes: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def total_requests(self) -> int:
        return self.hits + self.misses + self.errors
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "stale_serves": self.stale_serves,
            "invalidations": self.invalidations,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_rate": self.hit_rate,
            "total_requests": self.total_requests,
        }


class RedisCache:
    """
    Cache Redis consistente com suporte a TTL, tags e fallback.
    
    Uso:
        cache = RedisCache(redis_url="redis://localhost:6379")
        await cache.initialize()
        
        # Cache simples
        await cache.set("key", value, ttl=3600)
        value = await cache.get("key")
        
        # Cache com decorator
        @cache.cached(ttl=3600, key_prefix="weather")
        async def get_weather(lat, lon):
            ...
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
        max_memory_mb: int = 512,
        key_prefix: str = "climateai",
        enabled: bool = True,
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_memory_mb = max_memory_mb
        self.key_prefix = key_prefix
        self.enabled = enabled
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self.stats = CacheStats()
        self._tag_keys: Dict[str, set] = {}  # Tags -> set de chaves (em memória)
        self._inflight: Dict[str, asyncio.Future] = {}  # Request coalescing for stampede protection
    
    async def initialize(self) -> None:
        """Inicializar conexão Redis"""
        if not self.enabled:
            logger.info("Redis cache disabled")
            return
        
        try:
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Testar conexão
            await self._client.ping()
            logger.info(f"Redis cache initialized: {self.redis_url}")
            
            # Configurar política de memória
            await self._client.config_set("maxmemory", f"{self.max_memory_mb}mb")
            await self._client.config_set("maxmemory-policy", "allkeys-lru")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.enabled = False
    
    async def close(self) -> None:
        """Fechar conexão Redis"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
    
    def _make_key(self, key: str, prefix: Optional[str] = None) -> str:
        """Criar chave com prefixo"""
        actual_prefix = prefix if prefix is not None else self.key_prefix
        return f"{actual_prefix}:{key}"
    
    def _serialize(self, value: Any) -> str:
        """Serializar valor para JSON"""
        return json.dumps(value, default=str)
    
    def _deserialize(self, data: str) -> Any:
        """Deserializar valor de JSON"""
        if data is None:
            return None
        return json.loads(data)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Obter valor do cache"""
        if not self.enabled or not self._client:
            return default
        
        try:
            full_key = self._make_key(key)
            data = await self._client.get(full_key)
            
            if data is None:
                self.stats.misses += 1
                return default
            
            entry = CacheEntry.from_dict(json.loads(data))
            
            if entry.is_expired():
                await self.delete(key)
                self.stats.misses += 1
                return default
            
            self.stats.hits += 1
            logger.debug(f"Cache hit: {key} (TTL remaining: {entry.ttl_remaining():.0f}s)")
            return entry.value
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats.errors += 1
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> bool:
        """Armazenar valor no cache"""
        if not self.enabled or not self._client:
            return False
        
        try:
            full_key = self._make_key(key, prefix)
            actual_ttl = ttl if ttl is not None else self.default_ttl
            
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                expires_at=time.time() + actual_ttl,
                key=full_key,
                tags=tags or [],
            )
            
            await self._client.setex(
                full_key,
                actual_ttl,
                json.dumps(entry.to_dict())
            )
            
            # Atualizar índice de tags
            if tags:
                for tag in tags:
                    if tag not in self._tag_keys:
                        self._tag_keys[tag] = set()
                    self._tag_keys[tag].add(full_key)
            
            self.stats.sets += 1
            logger.debug(f"Cache set: {key} (TTL: {actual_ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.stats.errors += 1
            return False
    
    async def delete(self, key: str, prefix: Optional[str] = None) -> bool:
        """Remover valor do cache"""
        if not self.enabled or not self._client:
            return False
        
        try:
            full_key = self._make_key(key, prefix)
            await self._client.delete(full_key)
            self.stats.deletes += 1
            self.stats.invalidations += 1
            logger.debug(f"Cache delete: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.stats.errors += 1
            return False
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidar todas as chaves com uma tag"""
        if not self.enabled or not self._client:
            return 0
        
        count = 0
        if tag in self._tag_keys:
            for key in self._tag_keys[tag]:
                try:
                    await self._client.delete(key)
                    count += 1
                except Exception:
                    pass
            del self._tag_keys[tag]
        
        self.stats.invalidations += count
        logger.info(f"Cache invalidated {count} keys with tag: {tag}")
        return count
    
    async def exists(self, key: str) -> bool:
        """Verificar se chave existe no cache"""
        if not self.enabled or not self._client:
            return False
        
        try:
            full_key = self._make_key(key)
            return await self._client.exists(full_key)
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            self.stats.errors += 1
            return False
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        refresh: bool = False,
    ) -> T:
        """
        Obter do cache ou criar usando factory.
        
        Args:
            key: Chave do cache
            factory: Função assíncrona para criar valor se não existir
            ttl: TTL em segundos
            tags: Tags para invalidação
            refresh: Forçar refresh mesmo se existir
            
        Returns:
            Valor do cache ou criado pela factory
        """
        if not refresh:
            cached = await self.get(key)
            if cached is not None:
                return cached
        
        # Criar novo valor
        value = await factory()
        await self.set(key, value, ttl=ttl, tags=tags)
        return value
    
    async def get_stale_fallback(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
        ttl: Optional[int] = None,
        stale_ttl_multiplier: int = 3,
    ) -> tuple[T, bool]:
        """
        Obter do cache ou fallback para dados stale.
        
        Se o cache expirou mas temos dados stale, retorna os dados stale
        enquanto atualiza em background.
        
        Args:
            key: Chave do cache
            factory: Função para atualizar dados
            ttl: TTL em segundos
            stale_ttl_multiplier: Multiplicador para TTL stale
            
        Returns:
            Tuple[valor, is_stale]
        """
        if not self.enabled or not self._client:
            value = await factory()
            return value, False
        
        full_key = self._make_key(key)
        
        # Check if request is already in flight (stampede protection)
        if full_key in self._inflight:
            logger.debug(f"Coalescing request for key: {key}")
            return await self._inflight[full_key]

        # Create future for this request
        future = asyncio.Future()
        self._inflight[full_key] = future

        try:
            data = await self._client.get(full_key)
            
            result = None
            if data is None:
                # Sem cache, criar novo
                value = await factory()
                await self.set(key, value, ttl=ttl)
                result = (value, False)
            else:
                entry = CacheEntry.from_dict(json.loads(data))
                
                if not entry.is_expired():
                    # Cache válido
                    self.stats.hits += 1
                    result = (entry.value, False)
                else:
                    # Dados stale - servir como fallback enquanto atualiza
                    self.stats.stale_serves += 1
                    logger.warning(f"Serving stale cache for {key}")
                    
                    # Atualizar em background (fire and forget)
                    asyncio.create_task(self._refresh_stale_cache(key, entry, factory, ttl))
                    
                    result = (entry.value, True)
            
            # Resolve future for waiting requests
            if not future.done():
                future.set_result(result)
            return result
            
        except Exception as e:
            # Handle failure
            if not future.done():
                future.set_exception(e)
            
            logger.error(f"Cache stale fallback error: {e}")
            self.stats.errors += 1
            # Fallback to direct factory call if cache logic fails
            try:
                value = await factory()
                return value, False
            except Exception as factory_error:
                raise factory_error
        finally:
            # Cleanup inflight
            if full_key in self._inflight:
                del self._inflight[full_key]
    
    async def _refresh_stale_cache(
        self,
        key: str,
        old_entry: CacheEntry,
        factory: Callable[[], Awaitable[T]],
        ttl: Optional[int],
    ) -> None:
        """Atualizar cache stale em background"""
        try:
            value = await factory()
            await self.set(key, value, ttl=ttl)
            logger.info(f"Refreshed stale cache for {key}")
        except Exception as e:
            logger.error(f"Failed to refresh stale cache for {key}: {e}")
    
    async def clear(self) -> bool:
        """Limpar todo o cache (cuidado em produção!)"""
        if not self.enabled or not self._client:
            return False
        
        try:
            pattern = self._make_key("*")
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self._client.delete(*keys)
            
            self._tag_keys.clear()
            logger.info(f"Cleared {len(keys)} cache keys")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        return self.stats.to_dict()
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar saúde do Redis"""
        if not self.enabled or not self._client:
            return {"status": "disabled", "healthy": True}
        
        try:
            await self._client.ping()
            info = await self._client.info("memory")
            
            return {
                "status": "healthy",
                "healthy": True,
                "used_memory_mb": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", "unknown"),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e),
            }
    
    def cached(
        self,
        ttl: Optional[int] = None,
        key_prefix: str = "",
        tags: Optional[List[str]] = None,
        key_builder: Optional[Callable[..., str]] = None,
    ) -> Callable:
        """
        Decorator para caching de funções assíncronas.
        
        Uso:
            @cache.cached(ttl=3600, key_prefix="weather", tags=["weather", "external"])
            async def get_weather(lat, lon):
                ...
        """
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                # Construir chave
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # Hash dos argumentos
                    args_str = f"{args}:{sorted(kwargs.items())}"
                    args_hash = hashlib.sha256(args_str.encode()).hexdigest()[:16]
                    cache_key = f"{key_prefix}:{func.__name__}:{args_hash}"
                
                # Tentar cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Chamar função e cachear resultado
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl=ttl, tags=tags)
                return result
            
            return wrapper
        return decorator


# Instância global de cache
cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Obter instância global de cache"""
    global cache
    if cache is None:
        cache = RedisCache()
    return cache


async def initialize_cache(redis_url: str = "redis://localhost:6379") -> RedisCache:
    """Inicializar cache global"""
    global cache
    cache = RedisCache(redis_url=redis_url)
    await cache.initialize()
    return cache


# Decorator de conveniência para APIs externas
def external_api_cache(
    provider: str,
    ttl: int = 3600,
    stale_ttl_multiplier: int = 3,
):
    """
    Decorator para caching de APIs externas com fallback stale.
    
    Uso:
        @external_api_cache("openmeteo", ttl=1800)
        async def get_weather_data(lat, lon):
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache_instance = get_cache()

            # Construir chave
            args_str = f"{args}:{sorted(kwargs.items())}"
            args_hash = hashlib.sha256(args_str.encode()).hexdigest()[:16]
            cache_key = f"external:{provider}:{func.__name__}:{args_hash}"
            
            # Obter com fallback stale
            result, is_stale = await cache_instance.get_stale_fallback(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl=ttl,
                stale_ttl_multiplier=stale_ttl_multiplier,
            )
            
            if is_stale:
                logger.info(f"Serving stale data from {provider}")
            
            return result
        
        return wrapper
    return decorator

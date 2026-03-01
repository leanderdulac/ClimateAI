"""
Secrets Manager - HashiCorp Vault Integration
Gerenciamento seguro de secrets, credenciais e chaves de API
"""

import logging
import os
from typing import Any, Dict, Optional
from functools import wraps
import time

logger = logging.getLogger(__name__)

try:
    import hvac
    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False
    logger.warning("hvac not installed. Vault integration disabled.")
    
    # Mock class for when hvac is not available
    class hvac:
        class Client:
            def __init__(self, *args, **kwargs):
                pass
        
        class exceptions:
            class InvalidPath(Exception):
                pass


class VaultSecretsManager:
    """
    Gerenciador de Secrets usando HashiCorp Vault
    
    Features:
    - Armazenamento seguro de credenciais
    - Rotação automática de secrets
    - Audit trail de acesso
    - Cache local com TTL
    - Fallback para variáveis de ambiente
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        namespace: Optional[str] = None,
        cache_ttl: int = 300,  # 5 minutos
    ):
        """
        Inicializa o cliente Vault
        
        Args:
            url: URL do Vault (ex: http://localhost:8200)
            token: Token de autenticação
            namespace: Namespace (para Vault Enterprise)
            cache_ttl: TTL do cache local em segundos
        """
        if not HVAC_AVAILABLE:
            self.enabled = False
            logger.warning("Vault integration disabled - hvac not installed")
            return
        
        self.url = url or os.getenv("VAULT_URL", "http://localhost:8200")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.namespace = namespace or os.getenv("VAULT_NAMESPACE")
        self.cache_ttl = cache_ttl
        
        # Cache local para reduzir chamadas ao Vault
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # Inicializar cliente
        self.client = hvac.Client(url=self.url, namespace=self.namespace)
        self.enabled = False
        
        if self.token:
            self.client.token = self.token
            self.enabled = True
            logger.info(f"Vault client initialized: {self.url}")
        else:
            logger.warning("VAULT_TOKEN not configured. Using environment fallback.")
    
    def _get_from_cache(self, path: str) -> Optional[Dict[str, Any]]:
        """Recupera secret do cache se ainda válido"""
        if path in self._cache:
            timestamp = self._cache_timestamps.get(path, 0)
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for secret: {path}")
                return self._cache[path]
            else:
                # Remove expired entry
                del self._cache[path]
                self._cache_timestamps.pop(path, None)
        return None
    
    def _save_to_cache(self, path: str, data: Dict[str, Any]) -> None:
        """Salva secret no cache"""
        self._cache[path] = data
        self._cache_timestamps[path] = time.time()
        logger.debug(f"Cached secret: {path}")
    
    def is_enabled(self) -> bool:
        """Verifica se Vault está habilitado"""
        return self.enabled and HVAC_AVAILABLE
    
    def is_healthy(self) -> bool:
        """Verifica saúde do Vault"""
        if not self.enabled:
            return False
        
        try:
            status = self.client.sys.read_health_status()
            return status.get('initialized', False)
        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return False
    
    def get_secret(self, path: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Recupera um secret do Vault
        
        Args:
            path: Caminho do secret (ex: 'secret/data/climatewise/api-keys')
            version: Versão específica (para KV v2)
        
        Returns:
            Dicionário com os dados do secret ou None
        """
        if not self.enabled:
            logger.warning(f"Vault disabled, cannot get secret: {path}")
            return None
        
        # Check cache first
        cached = self._get_from_cache(path)
        if cached:
            return cached
        
        try:
            # Try KV v2 first (default)
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                version=version,
            )
            data = response.get('data', {}).get('data', {})
            
            # Save to cache
            self._save_to_cache(path, data)
            
            # Log access for audit
            logger.info(f"Secret accessed: {path}")
            
            return data
            
        except hvac.exceptions.InvalidPath:
            logger.warning(f"Secret not found: {path}")
            return None
        except Exception as e:
            logger.error(f"Error reading secret {path}: {e}")
            return None
    
    def set_secret(
        self,
        path: str,
        data: Dict[str, Any],
        cas: Optional[int] = None,
    ) -> bool:
        """
        Armazena um secret no Vault
        
        Args:
            path: Caminho do secret
            data: Dados do secret
            cas: Check-and-set para concorrência (opcional)
        
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.enabled:
            logger.warning(f"Vault disabled, cannot set secret: {path}")
            return False
        
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                cas=cas,
            )
            
            # Update cache
            self._save_to_cache(path, data)
            
            logger.info(f"Secret stored: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing secret {path}: {e}")
            return False
    
    def delete_secret(self, path: str) -> bool:
        """
        Deleta um secret do Vault
        
        Args:
            path: Caminho do secret
        
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.enabled:
            logger.warning(f"Vault disabled, cannot delete secret: {path}")
            return False
        
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path)
            
            # Remove from cache
            self._cache.pop(path, None)
            self._cache_timestamps.pop(path, None)
            
            logger.info(f"Secret deleted: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting secret {path}: {e}")
            return False
    
    def list_secrets(self, path: str) -> list:
        """
        Lista secrets em um caminho
        
        Args:
            path: Caminho base
        
        Returns:
            Lista de nomes de secrets
        """
        if not self.enabled:
            return []
        
        try:
            response = self.client.secrets.kv.v2.list_secrets(path=path)
            return response.get('data', {}).get('keys', [])
        except Exception as e:
            logger.error(f"Error listing secrets at {path}: {e}")
            return []
    
    def rotate_secret(
        self,
        path: str,
        key: str,
        generator_func=None,
    ) -> Optional[Dict[str, Any]]:
        """
        Rotaciona um secret
        
        Args:
            path: Caminho do secret
            key: Chave a ser rotacionada
            generator_func: Função para gerar novo valor
        
        Returns:
            Novo secret ou None
        """
        if not self.enabled:
            return None
        
        # Get current secret
        current = self.get_secret(path)
        if not current:
            logger.error(f"Cannot rotate non-existent secret: {path}")
            return None
        
        # Generate new value
        if generator_func:
            new_value = generator_func()
        else:
            # Default: generate random string
            import secrets
            new_value = secrets.token_urlsafe(32)
        
        # Update secret
        current[key] = new_value
        
        if self.set_secret(path, current):
            logger.info(f"Secret rotated: {path}.{key}")
            return current
        
        return None
    
    def get_secret_or_env(
        self,
        vault_path: str,
        env_var: str,
        key: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        Tenta obter do Vault, fallback para env var
        
        Args:
            vault_path: Caminho no Vault
            env_var: Variável de ambiente fallback
            key: Chave específica no secret (opcional)
            default: Valor padrão se nada encontrado
        
        Returns:
            Valor do secret ou fallback
        """
        # Try Vault first
        secret_data = self.get_secret(vault_path)
        if secret_data:
            if key:
                return secret_data.get(key, default)
            # If secret_data has only one key, return its value
            if len(secret_data) == 1:
                return list(secret_data.values())[0]
            return secret_data
        
        # Fallback to environment variable
        value = os.getenv(env_var)
        if value:
            logger.debug(f"Using env var fallback: {env_var}")
            return value
        
        logger.warning(f"Secret not found: {vault_path} or {env_var}")
        return default


# Singleton instance
_vault_instance: Optional[VaultSecretsManager] = None


def get_vault() -> VaultSecretsManager:
    """Obtém instância singleton do Vault"""
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = VaultSecretsManager()
    return _vault_instance


def vault_secret(vault_path: str, key: Optional[str] = None):
    """
    Decorator para injetar secrets do Vault
    
    Usage:
        @vault_secret('secret/data/climatewise/api-keys', 'noaa_key')
        def my_function(noaa_key):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            vault = get_vault()
            
            # Get secret from Vault
            secret_data = vault.get_secret(vault_path)
            
            if secret_data:
                if key:
                    # Inject specific key
                    kwargs[key] = secret_data.get(key)
                else:
                    # Inject all keys as kwargs
                    kwargs.update(secret_data)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Exemplo de uso
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Vault
    vault = VaultSecretsManager(
        url=os.getenv("VAULT_URL", "http://localhost:8200"),
        token=os.getenv("VAULT_TOKEN"),
    )
    
    if vault.is_enabled():
        print(f"✓ Vault enabled: {vault.is_healthy()}")
        
        # Example: Store a secret
        vault.set_secret("secret/data/climatewise/test", {
            "api_key": "test-key-123",
            "password": "secret-password"
        })
        
        # Example: Retrieve a secret
        secret = vault.get_secret("secret/data/climatewise/test")
        print(f"Retrieved secret: {secret}")
        
        # Example: Rotate a secret
        vault.rotate_secret("secret/data/climatewise/test", "api_key")
        
        # Example: List secrets
        secrets = vault.list_secrets("secret/data/climatewise")
        print(f"Available secrets: {secrets}")
    else:
        print("✗ Vault not enabled")

"""
Módulo de Segurança Centralizado para ClimateWise
Implementa funcionalidades críticas de segurança da aplicação
"""

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from fastapi import HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from passlib.context import CryptContext
from config.config import settings

# Configurações de segurança — usar a mesma chave já validada em config.settings
SECRET_KEY = settings.SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Contexto para hashing de senhas
pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__default_rounds=12, bcrypt__ident="2b"
)


def _utcnow() -> datetime:
    """Retorna datetime UTC atual (timezone-aware)."""
    return datetime.now(timezone.utc)


class PasswordManager:
    """Gerenciador de senhas com hashing seguro"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Gera hash da senha usando bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica se senha plain corresponde ao hash"""
        return pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """Gerenciador de tokens JWT"""

    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
        """Cria token de acesso JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = _utcnow() + expires_delta
        else:
            expire = _utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, str]) -> str:
        """Cria token de refresh JWT"""
        to_encode = data.copy()
        expire = _utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, expected_type: str = "access") -> Dict[str, str]:
        """Verifica e decodifica token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_type = payload.get("type")
            if token_type != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token type mismatch: expected {expected_type}, got {token_type}",
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
            )


class RateLimiter:
    """Limitador de taxa de requisições com cleanup automático"""

    # Número máximo de IPs rastreados antes de forçar cleanup
    MAX_TRACKED_IPS = 10000

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
        self._cleanup_counter = 0

    def _cleanup_stale_ips(self) -> None:
        """Remove IPs sem requisições recentes para evitar memory leak."""
        now = _utcnow()
        stale_ips = [
            ip for ip, times in self.requests.items()
            if not times or (now - times[-1]).total_seconds() > self.window_seconds * 2
        ]
        for ip in stale_ips:
            del self.requests[ip]

    def is_allowed(self, client_ip: str) -> bool:
        """Verifica se requisição é permitida para o IP"""
        now = _utcnow()

        # Cleanup periódico a cada 500 requisições ou quando há muitos IPs
        self._cleanup_counter += 1
        if self._cleanup_counter >= 500 or len(self.requests) > self.MAX_TRACKED_IPS:
            self._cleanup_stale_ips()
            self._cleanup_counter = 0

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Remove requisições antigas da janela
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if (now - req_time).total_seconds() < self.window_seconds
        ]

        # Verifica limite
        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        # Adiciona nova requisição
        self.requests[client_ip].append(now)
        return True

    def get_remaining_requests(self, client_ip: str) -> int:
        """Retorna número de requisições restantes na janela"""
        if client_ip not in self.requests:
            return self.max_requests

        now = _utcnow()
        valid_requests = [
            req_time for req_time in self.requests[client_ip]
            if (now - req_time).total_seconds() < self.window_seconds
        ]
        return max(0, self.max_requests - len(valid_requests))


class CSRFProtection:
    """Proteção CSRF com tokens"""

    def __init__(self):
        self.tokens: Dict[str, str] = {}

    def generate_token(self, session_id: str) -> str:
        """Gera token CSRF para sessão"""
        token = secrets.token_urlsafe(32)
        self.tokens[session_id] = token
        return token

    def verify_token(self, session_id: str, token: str) -> bool:
        """Verifica token CSRF"""
        stored_token = self.tokens.get(session_id)
        if stored_token and stored_token == token:
            # Token usado, remove para prevenir reuse
            del self.tokens[session_id]
            return True
        return False


class SecurityConfig:
    """Configuração centralizada de segurança"""

    def __init__(self):
        self.secret_key = SECRET_KEY
        self.allowed_origins = ["http://localhost:3000", "http://localhost:5173"]
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    def validate_config(self):
        """Valida configurações críticas"""
        if not self.secret_key or len(self.secret_key) < 32:
            if not self.debug:
                raise ValueError("SECRET_KEY must be set in environment variables and be at least 32 characters")
        return True


# Instâncias globais
password_manager = PasswordManager()
token_manager = TokenManager()
rate_limiter = RateLimiter()
csrf_protection = CSRFProtection()
security_config = SecurityConfig()
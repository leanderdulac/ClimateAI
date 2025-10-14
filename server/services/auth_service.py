"""
Serviço de Autenticação e Autorização para ClimateAI
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.schemas import (
    User, UserCreate, UserUpdate, LoginRequest, Token,
    TokenData, UserRole, UserPermissions, TokenType
)
from config.config import settings

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Contexto para hashing de senhas
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__ident="2b"
)

# Bearer token scheme
security = HTTPBearer()


class AuthService:
    """Serviço de autenticação e autorização"""

    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha plain corresponde ao hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Gera hash da senha"""
        # bcrypt limita senhas a 72 bytes, truncar se necessário
        truncated_password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(truncated_password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Cria token de acesso JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.ACCESS.value
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Cria token de refresh JWT"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.REFRESH.value
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> TokenData:
        """Verifica e decodifica token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            token_type_claim: str = payload.get("type")

            if user_id is None or email is None or role is None:
                raise JWTError("Token inválido")

            if token_type_claim != token_type.value:
                raise JWTError(f"Tipo de token incorreto. Esperado: {token_type.value}")

            return TokenData(
                user_id=user_id,
                email=email,
                role=UserRole(role),
                exp=datetime.fromtimestamp(payload.get("exp", 0))
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_user_permissions(self, role: UserRole) -> UserPermissions:
        """Retorna permissões baseadas no papel do usuário"""
        permissions = UserPermissions()

        if role == UserRole.ADMIN:
            permissions.can_access_climate_data = True
            permissions.can_access_pricing_models = True
            permissions.can_access_audit_logs = True
            permissions.can_manage_users = True
            permissions.can_access_admin_panel = True
            permissions.api_rate_limit = 1000

        elif role == UserRole.ANALYST:
            permissions.can_access_climate_data = True
            permissions.can_access_pricing_models = True
            permissions.can_access_audit_logs = False
            permissions.can_manage_users = False
            permissions.can_access_admin_panel = False
            permissions.api_rate_limit = 500

        elif role == UserRole.AUDITOR:
            permissions.can_access_climate_data = True
            permissions.can_access_pricing_models = False
            permissions.can_access_audit_logs = True
            permissions.can_manage_users = False
            permissions.can_access_admin_panel = False
            permissions.api_rate_limit = 300

        else:  # USER
            permissions.can_access_climate_data = True
            permissions.can_access_pricing_models = False
            permissions.can_access_audit_logs = False
            permissions.can_manage_users = False
            permissions.can_access_admin_panel = False
            permissions.api_rate_limit = 100

        return permissions

    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Autentica usuário com email e senha"""
        # Simulação de busca no banco (implementar quando houver BD real)
        # Por enquanto, criar usuário admin padrão se não existir
        if email == "admin@climateai.com" and password == "admin123":
            return User(
                id=str(uuid.uuid4()),
                email=email,
                full_name="Administrador ClimateAI",
                role=UserRole.ADMIN,
                is_active=True,
                organization="ClimateAI",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

        # TODO: Implementar busca real no banco de dados
        return None

    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        """Cria novo usuário"""
        user_id = str(uuid.uuid4())
        hashed_password = self.get_password_hash(user_data.password)

        user = User(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=user_data.is_active,
            organization=user_data.organization,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # TODO: Salvar no banco de dados
        return user

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Busca usuário por ID"""
        # TODO: Implementar busca real no banco
        return None

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Busca usuário por email"""
        # TODO: Implementar busca real no banco
        return None

    async def update_user(self, db: AsyncSession, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Atualiza dados do usuário"""
        # TODO: Implementar atualização real no banco
        return None

    async def delete_user(self, db: AsyncSession, user_id: str) -> bool:
        """Remove usuário"""
        # TODO: Implementar remoção real no banco
        return False

    async def login(self, db: AsyncSession, login_data: LoginRequest) -> Token:
        """Processa login do usuário"""
        user = await self.authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário inativo"
            )

        # Atualizar último login
        user.last_login = datetime.utcnow()

        # Criar tokens
        access_token = self.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user=user
        )

    async def refresh_access_token(self, db: AsyncSession, refresh_token: str) -> Token:
        """Renova token de acesso usando refresh token"""
        token_data = self.verify_token(refresh_token, TokenType.REFRESH)

        user = await self.get_user_by_id(db, token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou usuário inativo"
            )

        # Criar novo access token
        access_token = self.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Mantém o mesmo refresh token
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user=user
        )

    async def get_current_user(self, db: AsyncSession, credentials: HTTPAuthorizationCredentials) -> User:
        """Obtém usuário atual a partir do token"""
        token_data = self.verify_token(credentials.credentials, TokenType.ACCESS)
        user = await self.get_user_by_id(db, token_data.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário inativo"
            )

        return user

    def check_permission(self, user: User, required_role: UserRole) -> bool:
        """Verifica se usuário tem permissão baseada no papel"""
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.AUDITOR: 2,
            UserRole.ANALYST: 3,
            UserRole.ADMIN: 4
        }

        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level


# Instância global do serviço
auth_service = AuthService()
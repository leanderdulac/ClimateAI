"""
Serviço de Autenticação e Autorização para ClimateAI
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import settings
from lib.security import password_manager, token_manager
from models.schemas import LoginRequest, Token, TokenData, TokenType
from models.schemas import User as UserSchema
from models.schemas import UserCreate, UserPermissions, UserRole, UserUpdate
from models.sqlalchemy_models import User as UserModel

# Configurações de segurança - usando o módulo centralizado
if not settings.SECRET_KEY:
    import warnings
    warnings.warn(
        "SECRET_KEY is not set! Authentication will not work securely.",
        RuntimeWarning,
    )
SECRET_KEY = settings.SECRET_KEY or "INSECURE-FALLBACK-KEY-SET-SECRET-KEY-ENV-VAR"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

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
        return password_manager.verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Gera hash da senha"""
        return password_manager.hash_password(password)

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Cria token de acesso JWT"""
        return token_manager.create_access_token(data, expires_delta)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Cria token de refresh JWT"""
        return token_manager.create_refresh_token(data)

    def verify_token(
        self, token: str, token_type: TokenType = TokenType.ACCESS
    ) -> TokenData:
        """Verifica e decodifica token JWT"""
        payload = token_manager.verify_token(token, token_type.value)
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or email is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        return TokenData(
            user_id=user_id,
            email=email,
            role=UserRole(role),
            exp=datetime.fromtimestamp(payload.get("exp", 0)),
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
            permissions.api_rate_limit = 500
        elif role == UserRole.AUDITOR:
            permissions.can_access_climate_data = True
            permissions.can_access_audit_logs = True
            permissions.api_rate_limit = 300
        else:  # USER
            permissions.can_access_climate_data = True
            permissions.api_rate_limit = 100
        return permissions

    async def authenticate_user(
        self, db: AsyncSession, email: str, password: str
    ) -> Optional[UserModel]:
        """Autentica usuário com email e senha"""
        result = await db.execute(select(UserModel).filter(UserModel.email == email))
        user = result.scalars().first()
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> UserModel:
        """Cria novo usuário"""
        db_user = UserModel(
            id=str(uuid.uuid4()),
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=self.get_password_hash(user_data.password),
            role=user_data.role.value if hasattr(user_data.role, "value") else str(user_data.role),
            is_active=user_data.is_active,
            organization=user_data.organization,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def get_user_by_id(
        self, db: AsyncSession, user_id: str
    ) -> Optional[UserModel]:
        """Busca usuário por ID"""
        # Ensure user_id is a string for comparison with String column
        search_id = str(user_id)
        result = await db.execute(
            select(UserModel).filter(UserModel.id == search_id)
        )
        return result.scalars().first()

    async def get_user_by_email(
        self, db: AsyncSession, email: str
    ) -> Optional[UserModel]:
        """Busca usuário por email"""
        result = await db.execute(select(UserModel).filter(UserModel.email == email))
        return result.scalars().first()

    async def list_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[UserModel]:
        """Lista usuários com paginação"""
        result = await db.execute(
            select(UserModel).order_by(UserModel.full_name).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update_user(
        self, db: AsyncSession, user_id: str, user_data: UserUpdate
    ) -> Optional[UserModel]:
        """Atualiza dados do usuário"""
        update_values = user_data.dict(exclude_unset=True)
        if "password" in update_values:
            update_values["hashed_password"] = self.get_password_hash(
                update_values.pop("password")
            )

        if not update_values:
            return await self.get_user_by_id(db, user_id)

        stmt = (
            update(UserModel)
            .where(UserModel.id == str(user_id))
            .values(**update_values)
        )
        await db.execute(stmt)
        await db.commit()
        return await self.get_user_by_id(db, user_id)

    async def delete_user(self, db: AsyncSession, user_id: str) -> bool:
        """Remove usuário"""
        stmt = delete(UserModel).where(UserModel.id == str(user_id))
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

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
                status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário inativo"
            )

        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user=UserSchema.from_orm(user),
        )

    async def refresh_access_token(self, db: AsyncSession, refresh_token: str) -> Token:
        """Renova token de acesso usando refresh token"""
        token_data = self.verify_token(refresh_token, TokenType.REFRESH)
        user = await self.get_user_by_id(db, token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou usuário inativo",
            )

        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user=UserSchema.from_orm(user),
        )

    async def get_current_user(
        self, db: AsyncSession, credentials: HTTPAuthorizationCredentials
    ) -> UserModel:
        """Obtém usuário atual a partir do token"""
        token_data = self.verify_token(credentials.credentials, TokenType.ACCESS)
        user = await self.get_user_by_id(db, token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário inativo"
            )
        return user

    def check_permission(self, user: UserModel, required_role: UserRole) -> bool:
        """Verifica se usuário tem permissão baseada no papel"""
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.AUDITOR: 2,
            UserRole.ANALYST: 3,
            UserRole.ADMIN: 4,
        }
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level


auth_service = AuthService()

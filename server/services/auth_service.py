"""
Serviço de Autenticação e Autorização para ClimateWise
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import delete, select, update
from sqlalchemy.exc import InterfaceError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import settings
from config.supabase_client import (
    get_supabase_auth_issuer,
    get_supabase_client,
    is_supabase_configured,
    issuer_matches_supabase,
)
from lib.security import password_manager, token_manager
from models.schemas import LoginRequest, Token, TokenData, TokenType
from models.schemas import User as UserSchema
from models.schemas import UserCreate, UserPermissions, UserRole, UserUpdate
from models.sqlalchemy_models import User as UserModel
from services.supabase_auth import (
    SUPABASE_MANAGED_PASSWORD_MARKER,
    SupabaseAuthError,
    SupabaseAuthUser,
    sign_in_with_password as supabase_sign_in,
    sign_up as supabase_sign_up,
)

logger = logging.getLogger(__name__)

DB_UNAVAILABLE_DETAIL = "Banco de dados indisponível"
AUTH_UNAVAILABLE_DETAIL = "Serviço de autenticação indisponível"
_DB_UNAVAILABLE_EXC = (OperationalError, InterfaceError, ConnectionError, TimeoutError, OSError)

# Configurações de segurança - usando o módulo centralizado
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Bearer token scheme
security = HTTPBearer()


def _is_production() -> bool:
    return (os.getenv("ENVIRONMENT") or settings.ENVIRONMENT or "development").lower() == "production"


def _database_enabled() -> bool:
    raw = os.getenv("DATABASE_ENABLED")
    if raw is not None:
        return raw.lower() == "true"
    return bool(settings.DATABASE_ENABLED)


def raise_database_unavailable(exc: Optional[BaseException] = None) -> None:
    """Always surface DB outages as 503, never as 401."""
    if exc is not None:
        logger.warning("Database unavailable during auth: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=DB_UNAVAILABLE_DETAIL,
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=DB_UNAVAILABLE_DETAIL,
    )


def raise_auth_unavailable(exc: Optional[BaseException] = None) -> None:
    """Surface Supabase Auth outages as 503, never as 401."""
    if exc is not None:
        logger.warning("Auth provider unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=AUTH_UNAVAILABLE_DETAIL,
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=AUTH_UNAVAILABLE_DETAIL,
    )


def ensure_database_available() -> None:
    """In production, DATABASE_ENABLED must be true or auth returns 503."""
    if _is_production() and not _database_enabled():
        raise_database_unavailable()


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
        """Verifica e decodifica token JWT (local ou Supabase)"""
        try:
            # Tentar verificação local primeiro
            payload = token_manager.verify_token(token, token_type.value)
            
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")

            if user_id is None or email is None or role is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token local inválido",
                )

            return TokenData(
                user_id=user_id,
                email=email,
                role=UserRole(role),
                exp=datetime.fromtimestamp(payload.get("exp", 0)),
            )
        except HTTPException as local_err:
            if token_type != TokenType.ACCESS:
                raise local_err
            return self._verify_supabase_access_token(token, local_err)

    def _verify_supabase_access_token(
        self, token: str, local_err: HTTPException
    ) -> TokenData:
        """Validate a Supabase/GoTrue access token against this project's issuer."""
        expected_iss = get_supabase_auth_issuer()
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
        except Exception:
            raise local_err

        iss = decoded.get("iss")
        aud = decoded.get("aud")
        looks_like_gotrue = bool(iss) and str(iss).rstrip("/").endswith("/auth/v1")
        if not looks_like_gotrue:
            raise local_err

        if expected_iss and not issuer_matches_supabase(iss, expected_iss):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Supabase de outro projeto",
            )

        if aud not in ("authenticated", "service_role"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Supabase com audience inválida",
            )

        supabase = get_supabase_client()
        if not supabase:
            raise local_err

        try:
            response = supabase.auth.get_user(token)
            if response and response.user:
                sb_user = response.user
                return TokenData(
                    user_id=sb_user.id,
                    email=sb_user.email,
                    role=UserRole.USER,
                    exp=datetime.utcnow() + timedelta(minutes=30),
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Erro na verificação do Supabase: %s", exc)

        raise local_err

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

    async def _db_execute(self, db: AsyncSession, statement):
        ensure_database_available()
        try:
            return await db.execute(statement)
        except _DB_UNAVAILABLE_EXC as exc:
            raise_database_unavailable(exc)
            raise
        except SQLAlchemyError as exc:
            orig = getattr(exc, "orig", None)
            if isinstance(orig, _DB_UNAVAILABLE_EXC) or isinstance(exc, (OperationalError, InterfaceError)):
                raise_database_unavailable(exc)
                raise
            raise

    async def authenticate_user(
        self, db: AsyncSession, email: str, password: str
    ) -> Optional[UserModel]:
        """Autentica usuário com email e senha (local-dev fallback)."""
        ensure_database_available()
        if not _database_enabled():
            return None

        result = await self._db_execute(
            db, select(UserModel).filter(UserModel.email == email)
        )
        user = result.scalars().first()
                
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def upsert_local_user_from_supabase(
        self,
        db: AsyncSession,
        sb_user: SupabaseAuthUser,
        *,
        password: Optional[str] = None,
        full_name: Optional[str] = None,
        organization: Optional[str] = None,
        role: Optional[str] = None,
        is_active: bool = True,
    ) -> UserModel:
        """Link/create a row in public.users by supabase id or email."""
        ensure_database_available()
        user = await self.get_user_by_id(db, sb_user.id)
        if not user:
            user = await self.get_user_by_email(db, sb_user.email)

        resolved_name = (
            full_name
            or sb_user.full_name
            or (user.full_name if user else None)
            or sb_user.email.split("@")[0]
        )
        hashed = (
            self.get_password_hash(password)
            if password
            else (user.hashed_password if user else SUPABASE_MANAGED_PASSWORD_MARKER)
        )

        if not user:
            user = UserModel(
                id=sb_user.id,
                email=sb_user.email,
                full_name=resolved_name,
                hashed_password=hashed,
                role=role or UserRole.USER.value,
                is_active=is_active,
                organization=organization,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
            )
            db.add(user)
            try:
                await db.commit()
                await db.refresh(user)
            except _DB_UNAVAILABLE_EXC as exc:
                await db.rollback()
                raise_database_unavailable(exc)
            return user

        changed = False
        if user.email != sb_user.email:
            user.email = sb_user.email
            changed = True
        if resolved_name and user.full_name != resolved_name:
            user.full_name = resolved_name
            changed = True
        if organization is not None and user.organization != organization:
            user.organization = organization
            changed = True
        if role is not None and user.role != role:
            user.role = role
            changed = True
        if password and (
            not user.hashed_password
            or user.hashed_password == SUPABASE_MANAGED_PASSWORD_MARKER
        ):
            user.hashed_password = hashed
            changed = True
        user.last_login = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        changed = True
        if changed:
            try:
                await db.commit()
                await db.refresh(user)
            except _DB_UNAVAILABLE_EXC as exc:
                await db.rollback()
                raise_database_unavailable(exc)
        return user

    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> UserModel:
        """Cria novo usuário (Supabase Auth when configured, else local-dev)."""
        ensure_database_available()
        existing = await self.get_user_by_email(db, user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado"
            )

        user_id = str(uuid.uuid4())
        if is_supabase_configured():
            try:
                sb_user = supabase_sign_up(
                    user_data.email,
                    user_data.password,
                    full_name=user_data.full_name,
                )
                return await self.upsert_local_user_from_supabase(
                    db,
                    sb_user,
                    password=user_data.password,
                    full_name=user_data.full_name,
                    organization=user_data.organization,
                    role=user_data.role.value if hasattr(user_data.role, "value") else str(user_data.role),
                    is_active=user_data.is_active,
                )
            except SupabaseAuthError as exc:
                if exc.already_registered:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email já cadastrado",
                    ) from exc
                if exc.unavailable:
                    raise_auth_unavailable(exc)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc) or "Falha ao cadastrar no Supabase Auth",
                ) from exc

        db_user = UserModel(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=self.get_password_hash(user_data.password),
            role=user_data.role.value if hasattr(user_data.role, "value") else str(user_data.role),
            is_active=user_data.is_active,
            organization=user_data.organization,
        )
        db.add(db_user)
        try:
            await db.commit()
            await db.refresh(db_user)
        except _DB_UNAVAILABLE_EXC as exc:
            await db.rollback()
            raise_database_unavailable(exc)
        return db_user

    async def get_user_by_id(
        self, db: AsyncSession, user_id: str
    ) -> Optional[UserModel]:
        """Busca usuário por ID"""
        # Ensure user_id is a string for comparison with String column
        search_id = str(user_id)
        result = await self._db_execute(
            db, select(UserModel).filter(UserModel.id == search_id)
        )
        return result.scalars().first()

    async def get_user_by_email(
        self, db: AsyncSession, email: str
    ) -> Optional[UserModel]:
        """Busca usuário por email"""
        result = await self._db_execute(
            db, select(UserModel).filter(UserModel.email == email)
        )
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
        """Processa login do usuário.

        When SUPABASE_URL + anon key are set, authenticates against Supabase Auth
        then upserts public.users. Otherwise falls back to the local users table
        (local development). Always issues the backend JWT so the existing
        frontend POST /api/v1/auth/login contract stays unchanged.
        """
        ensure_database_available()

        user: Optional[UserModel] = None
        if is_supabase_configured():
            try:
                sb_user = supabase_sign_in(login_data.email, login_data.password)
            except SupabaseAuthError as exc:
                if exc.invalid_credentials:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Email ou senha incorretos",
                        headers={"WWW-Authenticate": "Bearer"},
                    ) from exc
                raise_auth_unavailable(exc)
            user = await self.upsert_local_user_from_supabase(
                db, sb_user, password=login_data.password
            )
        else:
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
        """Obtém usuário atual a partir do token (suporta sync do Supabase)"""
        ensure_database_available()
        token_data = self.verify_token(credentials.credentials, TokenType.ACCESS)
        
        # Buscar usuário localmente
        user = await self.get_user_by_id(db, token_data.user_id)
        
        # Se não encontrar localmente, mas o token for válido (ex: Supabase user novo), criar localmente
        if not user:
            # Tentar buscar por email caso o ID seja diferente entre sistemas
            user = await self.get_user_by_email(db, token_data.email)
            
            if not user:
                logger.info(
                    "Auto-sync: criando usuário %s (%s)",
                    token_data.email,
                    token_data.user_id,
                )
                user = UserModel(
                    id=token_data.user_id,
                    email=token_data.email,
                    full_name=token_data.email.split("@")[0],
                    hashed_password=SUPABASE_MANAGED_PASSWORD_MARKER,
                    role=token_data.role.value if hasattr(token_data.role, "value") else str(token_data.role),
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(user)
                try:
                    await db.commit()
                    await db.refresh(user)
                except _DB_UNAVAILABLE_EXC as exc:
                    await db.rollback()
                    raise_database_unavailable(exc)

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

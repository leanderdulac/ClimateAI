"""
Middleware de Autenticação para ClimateWise
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session
from models.schemas import User, UserRole
from services.auth_service import auth_service

# Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPBearer = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependência para obter usuário atual"""
    return await auth_service.get_current_user(db, credentials)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependência para obter usuário ativo"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user


def require_role(required_role: UserRole):
    """Decorator para requerer papel específico"""

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not auth_service.check_permission(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer papel: {required_role.value}",
            )
        return current_user

    return role_checker


# Dependências específicas para cada papel
require_admin = require_role(UserRole.ADMIN)
require_analyst = require_role(UserRole.ANALYST)
require_auditor = require_role(UserRole.AUDITOR)


async def get_user_permissions(current_user: User = Depends(get_current_active_user)):
    """Obtém permissões do usuário atual"""
    return auth_service.get_user_permissions(current_user.role)


class AuthMiddleware:
    """Middleware para autenticação opcional"""

    def __init__(self, optional: bool = False):
        self.optional = optional

    async def __call__(
        self, request: Request, call_next, db: AsyncSession = Depends(get_db_session)
    ):
        """Middleware que adiciona usuário à requisição se token estiver presente"""
        user = None

        # Tentar extrair token do header Authorization
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                user = await auth_service.get_current_user(
                    db, type("Credentials", (), {"credentials": token})()
                )
            except HTTPException:
                if not self.optional:
                    raise

        # Adicionar usuário à requisição
        request.state.user = user

        # Continuar processamento
        response = await call_next(request)
        return response


# Instância para uso opcional
optional_auth = AuthMiddleware(optional=True)

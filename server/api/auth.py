"""
Endpoints de Autenticação e Gerenciamento de Usuários
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from models.schemas import (
    User, UserCreate, UserUpdate, LoginRequest, Token,
    RefreshTokenRequest, UserPermissions, UserRole
)
from services.auth_service import auth_service
from middleware.auth_middleware import (
    get_current_user, get_current_active_user, require_admin
)
from config.database import get_db_session

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Autentica usuário e retorna tokens JWT

    - **email**: Email do usuário
    - **password**: Senha do usuário
    """
    return await auth_service.login(db, login_data)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Renova token de acesso usando refresh token

    - **refresh_token**: Token de refresh válido
    """
    return await auth_service.refresh_access_token(db, refresh_data.refresh_token)


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Retorna informações do usuário atual
    """
    return current_user


@router.get("/me/permissions", response_model=UserPermissions)
async def get_current_user_permissions(current_user: User = Depends(get_current_active_user)):
    """
    Retorna permissões do usuário atual
    """
    return auth_service.get_user_permissions(current_user.role)


@router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Cria novo usuário (apenas administradores)

    - **email**: Email único do usuário
    - **full_name**: Nome completo
    - **password**: Senha
    - **role**: Papel do usuário (admin, analyst, auditor, user)
    - **organization**: Organização (opcional)
    """
    # Verificar se email já existe
    existing_user = await auth_service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )

    return await auth_service.create_user(db, user_data)


@router.get("/users", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Lista usuários (apenas administradores)

    - **skip**: Número de registros para pular
    - **limit**: Número máximo de registros (1-1000)
    """
    # TODO: Implementar listagem real do banco
    # Por enquanto retorna lista vazia
    return []


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Obtém usuário por ID (apenas administradores)
    """
    user = await auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return user


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Atualiza usuário (apenas administradores)

    - **user_id**: ID do usuário a ser atualizado
    - **user_data**: Dados a serem atualizados
    """
    # Verificar se usuário existe
    existing_user = await auth_service.get_user_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Verificar se email já está em uso por outro usuário
    if user_data.email:
        email_user = await auth_service.get_user_by_email(db, user_data.email)
        if email_user and email_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )

    updated_user = await auth_service.update_user(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar usuário"
        )

    return updated_user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Remove usuário (apenas administradores)

    - **user_id**: ID do usuário a ser removido
    """
    # Não permitir auto-exclusão
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir o próprio usuário"
        )

    # Verificar se usuário existe
    existing_user = await auth_service.get_user_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    success = await auth_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao remover usuário"
        )

    return {"message": "Usuário removido com sucesso"}


@router.put("/users/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Ativa/desativa usuário (apenas administradores)

    - **user_id**: ID do usuário
    - **is_active**: True para ativar, False para desativar
    """
    # Não permitir desativar a si mesmo
    if current_user.id == user_id and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível desativar o próprio usuário"
        )

    # Verificar se usuário existe
    existing_user = await auth_service.get_user_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Atualizar status
    update_data = UserUpdate(is_active=is_active)
    updated_user = await auth_service.update_user(db, user_id, update_data)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar status do usuário"
        )

    action = "ativado" if is_active else "desativado"
    return {"message": f"Usuário {action} com sucesso"}
"""
Testes para o sistema de autenticação
"""

import pytest

from models.schemas import UserRole
from services.auth_service import auth_service


def test_password_hashing():
    """Testa hashing e verificação de senha"""
    password = "testpassword123"
    hashed = auth_service.get_password_hash(password)

    assert auth_service.verify_password(password, hashed)
    assert not auth_service.verify_password("wrongpassword", hashed)


def test_create_access_token():
    """Testa criação de token de acesso"""
    data = {"sub": "user123", "email": "test@example.com", "role": "user"}
    token = auth_service.create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

    # Verificar se o token pode ser decodificado
    decoded = auth_service.verify_token(token, auth_service.TokenType.ACCESS)
    assert decoded.user_id == "user123"
    assert decoded.email == "test@example.com"
    assert decoded.role == UserRole.USER


def test_create_refresh_token():
    """Testa criação de token de refresh"""
    data = {"sub": "user123", "email": "test@example.com", "role": "user"}
    token = auth_service.create_refresh_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

    # Verificar se o token pode ser decodificado
    decoded = auth_service.verify_token(token, auth_service.TokenType.REFRESH)
    assert decoded.user_id == "user123"
    assert decoded.email == "test@example.com"
    assert decoded.role == UserRole.USER


def test_verify_invalid_token():
    """Testa verificação de token inválido"""
    with pytest.raises(Exception):  # Deve lançar HTTPException
        auth_service.verify_token("invalid.token.here")


def test_user_permissions_admin():
    """Testa permissões do usuário admin"""
    permissions = auth_service.get_user_permissions(UserRole.ADMIN)

    assert permissions.can_access_climate_data == True
    assert permissions.can_manage_users == True
    assert permissions.can_access_admin_panel == True
    assert permissions.api_rate_limit == 1000


def test_user_permissions_user():
    """Testa permissões do usuário comum"""
    permissions = auth_service.get_user_permissions(UserRole.USER)

    assert permissions.can_access_climate_data == True
    assert permissions.can_manage_users == False
    assert permissions.can_access_admin_panel == False
    assert permissions.api_rate_limit == 100


def test_check_permission():
    """Testa verificação de permissões baseada em papel"""
    admin_user = type("User", (), {"role": UserRole.ADMIN})()
    user_user = type("User", (), {"role": UserRole.USER})()

    # Admin pode acessar tudo
    assert auth_service.check_permission(admin_user, UserRole.ADMIN)
    assert auth_service.check_permission(admin_user, UserRole.USER)

    # User comum só pode acessar seu próprio nível
    assert auth_service.check_permission(user_user, UserRole.USER)
    assert not auth_service.check_permission(user_user, UserRole.ADMIN)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

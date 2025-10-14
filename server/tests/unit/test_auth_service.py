"""
Testes unitários para o serviço de autenticação
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from jose import jwt

from services.auth_service import AuthService
from models.schemas import User, UserRole, UserCreate


class TestAuthService:
    """Testes para AuthService"""

    @pytest.fixture
    def auth_service(self):
        """Fixture para AuthService"""
        return AuthService()

    @pytest.fixture
    def sample_user(self):
        """Fixture para usuário de exemplo"""
        return User(
            id="test-user-id",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            organization="Test Org",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @patch('services.auth_service.pwd_context')
    def test_verify_password(self, mock_pwd_context, auth_service):
        """Testa verificação de senha"""
        password = "testpassword"
        hashed = "hashed_password"

        mock_pwd_context.verify.return_value = True
        assert auth_service.verify_password(password, hashed)
        mock_pwd_context.verify.assert_called_with(password, hashed)

        mock_pwd_context.verify.return_value = False
        assert not auth_service.verify_password("wrongpassword", hashed)

    @patch('services.auth_service.pwd_context')
    def test_get_password_hash(self, mock_pwd_context, auth_service):
        """Testa geração de hash de senha"""
        password = "testpassword"
        mock_pwd_context.hash.return_value = "hashed_password"

        hashed = auth_service.get_password_hash(password)

        assert hashed == "hashed_password"
        mock_pwd_context.hash.assert_called_once()
        # Verificar que a senha foi truncada para 72 bytes
        call_args = mock_pwd_context.hash.call_args[0][0]
        assert len(call_args.encode('utf-8')) <= 72

    def test_create_access_token(self, auth_service):
        """Testa criação de token de acesso"""
        data = {"sub": "test-user", "email": "test@example.com"}
        token = auth_service.create_access_token(data)

        # Decodificar token
        payload = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])

        assert payload["sub"] == "test-user"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token(self, auth_service):
        """Testa criação de token de refresh"""
        data = {"sub": "test-user", "email": "test@example.com"}
        token = auth_service.create_refresh_token(data)

        # Decodificar token
        payload = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])

        assert payload["sub"] == "test-user"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_token_valid(self, auth_service):
        """Testa verificação de token válido"""
        data = {"sub": "test-user", "email": "test@example.com", "role": "user"}
        token = auth_service.create_access_token(data)

        token_data = auth_service.verify_token(token)

        assert token_data.user_id == "test-user"
        assert token_data.email == "test@example.com"
        assert token_data.role == UserRole.USER

    def test_verify_token_expired(self, auth_service):
        """Testa verificação de token expirado"""
        data = {"sub": "test-user", "email": "test@example.com", "role": "user"}
        # Token expirado há 1 hora
        expired_token = auth_service.create_access_token(data, expires_delta=timedelta(hours=-1))

        with pytest.raises(Exception):  # Deve lançar HTTPException
            auth_service.verify_token(expired_token)

    def test_verify_token_wrong_type(self, auth_service):
        """Testa verificação de token com tipo errado"""
        data = {"sub": "test-user", "email": "test@example.com", "role": "user"}
        refresh_token = auth_service.create_refresh_token(data)

        with pytest.raises(Exception):  # Deve lançar HTTPException
            auth_service.verify_token(refresh_token, UserRole.ACCESS)

    def test_get_user_permissions_admin(self, auth_service):
        """Testa permissões de admin"""
        permissions = auth_service.get_user_permissions(UserRole.ADMIN)

        assert permissions.can_access_climate_data
        assert permissions.can_access_pricing_models
        assert permissions.can_access_audit_logs
        assert permissions.can_manage_users
        assert permissions.can_access_admin_panel
        assert permissions.api_rate_limit == 1000

    def test_get_user_permissions_user(self, auth_service):
        """Testa permissões de usuário comum"""
        permissions = auth_service.get_user_permissions(UserRole.USER)

        assert permissions.can_access_climate_data
        assert not permissions.can_access_pricing_models
        assert not permissions.can_access_audit_logs
        assert not permissions.can_manage_users
        assert not permissions.can_access_admin_panel
        assert permissions.api_rate_limit == 100

    def test_check_permission_hierarchy(self, auth_service, sample_user):
        """Testa hierarquia de permissões"""
        # Admin pode acessar tudo
        admin_user = sample_user.copy(update={"role": UserRole.ADMIN})
        assert auth_service.check_permission(admin_user, UserRole.USER)
        assert auth_service.check_permission(admin_user, UserRole.ANALYST)
        assert auth_service.check_permission(admin_user, UserRole.ADMIN)

        # User não pode acessar admin
        user_user = sample_user.copy(update={"role": UserRole.USER})
        assert auth_service.check_permission(user_user, UserRole.USER)
        assert not auth_service.check_permission(user_user, UserRole.ANALYST)
        assert not auth_service.check_permission(user_user, UserRole.ADMIN)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service):
        """Testa autenticação bem-sucedida"""
        # Mock do banco
        mock_db = AsyncMock()

        # Testar usuário admin padrão
        user = await auth_service.authenticate_user(mock_db, "admin@climateai.com", "admin123")

        assert user is not None
        assert user.email == "admin@climateai.com"
        assert user.role == UserRole.ADMIN
        assert user.is_active

    @pytest.mark.asyncio
    async def test_authenticate_user_failure(self, auth_service):
        """Testa autenticação falhada"""
        mock_db = AsyncMock()

        user = await auth_service.authenticate_user(mock_db, "wrong@email.com", "wrongpass")

        assert user is None

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service):
        """Testa login bem-sucedido"""
        mock_db = AsyncMock()

        result = await auth_service.login(mock_db, type('LoginRequest', (), {
            'email': 'admin@climateai.com',
            'password': 'admin123'
        })())

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"
        assert result.expires_in == 1800  # 30 minutos
        assert result.user.email == "admin@climateai.com"

    @pytest.mark.asyncio
    async def test_login_failure(self, auth_service):
        """Testa login falhado"""
        mock_db = AsyncMock()

        with pytest.raises(Exception):  # Deve lançar HTTPException
            await auth_service.login(mock_db, type('LoginRequest', (), {
                'email': 'wrong@email.com',
                'password': 'wrongpass'
            })())
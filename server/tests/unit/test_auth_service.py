"""
Testes Unitários para Serviços de Autenticação
"""

import unittest
from pydantic import ValidationError


class TestAuthService(unittest.TestCase):
    """Testes para o serviço de autenticação"""

    def test_password_hashing(self):
        """Testa hashing de senha"""
        from lib.security import PasswordManager
        
        # Arrange
        password = "SecurePassword123!"
        
        # Act
        hashed = PasswordManager.hash_password(password)
        
        # Assert
        self.assertTrue(hashed.startswith('$2'))  # bcrypt hash starts with $2
        self.assertTrue(PasswordManager.verify_password(password, hashed))
        self.assertFalse(PasswordManager.verify_password("WrongPassword", hashed))

    def test_password_hashing_different_hashes(self):
        """Testa que senhas iguais geram hashes diferentes"""
        from lib.security import PasswordManager
        
        password = "SamePassword123!"
        
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)
        
        # Hashes devem ser diferentes (devido ao salt)
        self.assertNotEqual(hash1, hash2)
        
        # Mas ambos devem verificar corretamente
        self.assertTrue(PasswordManager.verify_password(password, hash1))
        self.assertTrue(PasswordManager.verify_password(password, hash2))

    def test_public_register_password_policy(self):
        """Cadastro público rejeita senhas fracas."""
        from models.schemas import PublicRegisterRequest

        PublicRegisterRequest(
            email="ok@example.com",
            full_name="Ok User",
            password="admin123",
        )

        with self.assertRaises(ValidationError):
            PublicRegisterRequest(
                email="weak@example.com",
                full_name="Weak User",
                password="short",
            )

        with self.assertRaises(ValidationError):
            PublicRegisterRequest(
                email="letters@example.com",
                full_name="Letters Only",
                password="password",
            )


class TestJWTToken(unittest.TestCase):
    """Testes para tokens JWT"""

    def test_jwt_token_creation(self):
        """Testa criação de token JWT"""
        import jwt
        from datetime import datetime, timedelta
        
        # Arrange
        secret_key = 'test_secret_key_123456789012345678901234567890'
        payload = {
            'sub': 'user123',
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        # Act
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        # Assert
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 50)  # JWT tokens are typically long
        
        # Decode and verify
        decoded = jwt.decode(token, secret_key, algorithms=['HS256'])
        self.assertEqual(decoded['sub'], 'user123')

    def test_jwt_token_expiration(self):
        """Testa expiração de token JWT"""
        import jwt
        from datetime import datetime, timedelta
        
        # Arrange
        secret_key = 'test_secret_key_123456789012345678901234567890'
        expired_payload = {
            'sub': 'user123',
            'exp': datetime.utcnow() - timedelta(hours=1),  # Already expired
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        
        token = jwt.encode(expired_payload, secret_key, algorithm='HS256')
        
        # Act & Assert
        with self.assertRaises(jwt.ExpiredSignatureError):
            jwt.decode(token, secret_key, algorithms=['HS256'])


class TestUserPermissions(unittest.TestCase):
    """Testes para permissões de usuário"""

    def test_user_role_enum(self):
        """Testa enum de papéis de usuário"""
        from models.schemas import UserRole
        
        # Assert
        self.assertEqual(UserRole.USER.value, 'user')
        self.assertEqual(UserRole.ADMIN.value, 'admin')
        self.assertEqual(UserRole.ANALYST.value, 'analyst')

    def test_user_permissions_by_role(self):
        """Testa permissões por papel"""
        from models.schemas import UserPermissions
        
        # Test user permissions
        user_perms = UserPermissions(
            can_access_climate_data=True,
            can_access_pricing_models=False,
            can_manage_users=False
        )
        
        self.assertTrue(user_perms.can_access_climate_data)
        self.assertFalse(user_perms.can_access_pricing_models)
        self.assertFalse(user_perms.can_manage_users)


class TestPublicRegistrationSchema(unittest.TestCase):
    """Testes para o payload de cadastro público."""

    def test_public_registration_rejects_role_injection(self):
        from models.schemas import PublicRegisterRequest

        with self.assertRaises(ValidationError):
            PublicRegisterRequest(
                email='test@example.com',
                full_name='Test User',
                password='SecurePassword123!',
                role='admin',
            )


if __name__ == '__main__':
    unittest.main()

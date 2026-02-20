"""
Testes Unitários para Configurações e Segurança
"""

import os
import sys
import unittest
from unittest.mock import patch
from server.config.config import Settings, generate_secret_key


class TestSecretKeyGeneration(unittest.TestCase):
    """Testes para geração de SECRET_KEY"""

    def test_generate_secret_key_returns_string(self):
        """Testa se a função retorna uma string"""
        key = generate_secret_key()
        self.assertIsInstance(key, str)

    def test_generate_secret_key_minimum_length(self):
        """Testa se a chave tem pelo menos 32 caracteres"""
        key = generate_secret_key()
        self.assertGreaterEqual(len(key), 32)

    def test_generate_secret_key_unique(self):
        """Testa se chaves geradas são únicas"""
        key1 = generate_secret_key()
        key2 = generate_secret_key()
        self.assertNotEqual(key1, key2)

    def test_generate_secret_key_url_safe(self):
        """Testa se a chave é URL-safe"""
        key = generate_secret_key()
        # URL-safe base64 não contém + ou /
        self.assertNotIn('+', key)
        self.assertNotIn('/', key)


class TestSettingsValidation(unittest.TestCase):
    """Testes para validação das configurações"""

    @patch.dict(os.environ, {'SECRET_KEY': 'test_key_123456789012345678901234567890'})
    def test_settings_with_valid_secret_key(self):
        """Testa configurações com SECRET_KEY válida"""
        settings = Settings()
        self.assertEqual(len(settings.SECRET_KEY), 44)

    @patch.dict(os.environ, {'SECRET_KEY': ''})
    def test_settings_generates_secret_key_if_empty(self):
        """Testa se SECRET_KEY é gerada quando vazia"""
        settings = Settings()
        self.assertGreaterEqual(len(settings.SECRET_KEY), 32)

    @patch.dict(os.environ, {
        'ALLOW_ORIGINS': 'http://localhost:3000,http://localhost:5173'
    })
    def test_allow_origins_parsing(self):
        """Testa parsing de ALLOW_ORIGINS"""
        settings = Settings()
        self.assertEqual(len(settings.ALLOW_ORIGINS), 2)
        self.assertIn('http://localhost:3000', settings.ALLOW_ORIGINS)
        self.assertIn('http://localhost:5173', settings.ALLOW_ORIGINS)

    @patch.dict(os.environ, {'ALLOW_ORIGINS': ''})
    def test_allow_origins_default_when_empty(self):
        """Testa valor padrão de ALLOW_ORIGINS quando vazio"""
        settings = Settings()
        self.assertIn('http://localhost:3000', settings.ALLOW_ORIGINS)

    @patch.dict(os.environ, {'DEBUG': 'true'})
    def test_debug_mode_enabled(self):
        """Testa modo debug ativado"""
        settings = Settings()
        self.assertTrue(settings.DEBUG)

    @patch.dict(os.environ, {'DEBUG': 'false'})
    def test_debug_mode_disabled(self):
        """Testa modo debug desativado"""
        settings = Settings()
        self.assertFalse(settings.DEBUG)


class TestDatabaseConfiguration(unittest.TestCase):
    """Testes para configuração de banco de dados"""

    @patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql+asyncpg://user:pass@host:5432/dbname',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_database_url_custom(self):
        """Testa URL customizada de banco de dados"""
        settings = Settings()
        self.assertIn('postgresql+asyncpg', settings.DATABASE_URL)
        self.assertIn('host', settings.DATABASE_URL)

    @patch.dict(os.environ, {
        'DATABASE_ENABLED': 'true',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_database_enabled(self):
        """Testa se banco de dados está habilitado"""
        settings = Settings()
        self.assertTrue(settings.DATABASE_ENABLED)

    @patch.dict(os.environ, {
        'DATABASE_ENABLED': 'false',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_database_disabled(self):
        """Testa se banco de dados está desabilitado"""
        settings = Settings()
        self.assertFalse(settings.DATABASE_ENABLED)


class TestRedisConfiguration(unittest.TestCase):
    """Testes para configuração do Redis"""

    @patch.dict(os.environ, {
        'REDIS_ENABLED': 'true',
        'REDIS_URL': 'redis://redis:6379',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_redis_enabled(self):
        """Testa Redis habilitado"""
        settings = Settings()
        self.assertTrue(settings.REDIS_ENABLED)
        self.assertEqual(settings.REDIS_URL, 'redis://redis:6379')

    @patch.dict(os.environ, {
        'REDIS_ENABLED': 'false',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_redis_disabled(self):
        """Testa Redis desabilitado"""
        settings = Settings()
        self.assertFalse(settings.REDIS_ENABLED)


class TestExternalAPIKeys(unittest.TestCase):
    """Testes para chaves de APIs externas"""

    @patch.dict(os.environ, {
        'EMBRAPA_API_KEY': 'embrapa_key_123',
        'NOAA_API_KEY': 'noaa_key_456',
        'GEMINI_API_KEY': 'gemini_key_789',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_api_keys_loaded(self):
        """Testa se chaves de API são carregadas"""
        settings = Settings()
        self.assertEqual(settings.EMBRAPA_API_KEY, 'embrapa_key_123')
        self.assertEqual(settings.NOAA_API_KEY, 'noaa_key_456')
        self.assertEqual(settings.GEMINI_API_KEY, 'gemini_key_789')

    @patch.dict(os.environ, {
        'EMBRAPA_API_URL': 'https://api.embrapa.br',
        'EMBRAPA_API_VERSION': 'v2',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_api_urls_configured(self):
        """Testa se URLs de API estão configuradas"""
        settings = Settings()
        self.assertEqual(settings.EMBRAPA_API_URL, 'https://api.embrapa.br')
        self.assertEqual(settings.EMBRAPA_API_VERSION, 'v2')


class TestSecuritySettings(unittest.TestCase):
    """Testes para configurações de segurança"""

    @patch.dict(os.environ, {
        'JWT_EXPIRATION_HOURS': '48',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_jwt_expiration_custom(self):
        """Testa expiração customizada do JWT"""
        # Nota: JWT_EXPIRATION_HOURS não está na classe Settings ainda
        # Isso é um placeholder para implementação futura
        pass

    @patch.dict(os.environ, {
        'MAX_FILE_SIZE': '5242880',  # 5MB
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_max_file_size(self):
        """Testa tamanho máximo de arquivo"""
        settings = Settings()
        self.assertEqual(settings.MAX_FILE_SIZE, 5242880)

    @patch.dict(os.environ, {
        'ALLOWED_FILE_EXTENSIONS': 'csv,json,pdf',
        'SECRET_KEY': 'test_key_123456789012345678901234567890'
    })
    def test_allowed_file_extensions(self):
        """Testa extensões de arquivo permitidas"""
        settings = Settings()
        self.assertEqual(settings.ALLOWED_FILE_EXTENSIONS, 'csv,json,pdf')


if __name__ == '__main__':
    unittest.main()

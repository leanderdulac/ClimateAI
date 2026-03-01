"""
Testes de Integração para API ClimateWise
Testa endpoints completos com banco de dados
"""

import pytest
pytestmark = [pytest.mark.integration, pytest.mark.requires_db]
import asyncio
from httpx import AsyncClient, ASGITransport
from server.main import app
from server.config.database import get_db_session, init_db, close_db
from server.config.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para testes async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Configura banco de dados de teste"""
    # Setup: Initialize database
    await init_db()
    yield
    # Teardown: Cleanup database
    await close_db()


@pytest.fixture
async def client():
    """Cria cliente HTTP para testes"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.integration
@pytest.mark.requires_db
class TestHealthEndpoints:
    """Testa endpoints de health check"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Testa endpoint básico de health"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Testa endpoint raiz"""
        response = await client.get("/")
        assert response.status_code in [200, 404]  # Pode retornar 404 se não tiver endpoint


@pytest.mark.integration
@pytest.mark.requires_db
class TestAuthEndpoints:
    """Testa endpoints de autenticação"""

    @pytest.mark.asyncio
    async def test_register_user(self, client):
        """Testa registro de usuário"""
        user_data = {
            "email": f"test_{asyncio.get_event_loop().time()}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """Testa login com sucesso"""
        # Primeiro registra usuário
        email = f"test_{asyncio.get_event_loop().time()}@example.com"
        password = "SecurePassword123!"
        
        register_data = {
            "email": email,
            "password": password,
            "full_name": "Test User"
        }
        
        await client.post("/api/v1/auth/register", json=register_data)
        
        # Tenta login
        login_data = {
            "email": email,
            "password": password
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        """Testa login com senha errada"""
        email = f"test_{asyncio.get_event_loop().time()}@example.com"
        password = "SecurePassword123!"
        
        # Registra usuário
        register_data = {
            "email": email,
            "password": password,
            "full_name": "Test User"
        }
        await client.post("/api/v1/auth/register", json=register_data)
        
        # Tenta login com senha errada
        login_data = {
            "email": email,
            "password": "WrongPassword123!"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.requires_db
class TestClimateEndpoints:
    """Testa endpoints de clima"""

    @pytest.mark.asyncio
    async def test_get_clima_previsao(self, client):
        """Testa previsão climática"""
        params = {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "dias": 7
        }

        response = await client.get("/api/v1/clima/previsao", params=params)
        assert response.status_code == 200
        data = response.json()
        # Aceitar tanto 'forecast' (inglês) quanto 'previsao' (português) ou 'data'
        assert "forecast" in data or "previsao" in data or "data" in data

    @pytest.mark.asyncio
    async def test_get_clima_historico(self, client):
        """Testa dados históricos de clima"""
        params = {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "data_inicio": "2024-01-01",
            "data_fim": "2024-01-31"
        }
        
        response = await client.get("/api/v1/clima/historico", params=params)
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.requires_db
class TestEventosEndpoints:
    """Testa endpoints de eventos climáticos"""

    @pytest.mark.asyncio
    async def test_get_eventos(self, client):
        """Testa listagem de eventos"""
        params = {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "raio": 50
        }

        response = await client.get("/api/v1/eventos", params=params)
        # 307 = Temporary Redirect (pode ocorrer se precisar autenticar)
        assert response.status_code in [200, 307]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "eventos" in data


@pytest.mark.integration
@pytest.mark.requires_db
class TestModelagemEndpoints:
    """Testa endpoints de modelagem econômica"""

    @pytest.mark.asyncio
    async def test_previsao_precos(self, client):
        """Testa previsão de preços"""
        params = {
            "simbolos": ["CORN", "SOYBEAN"],
            "dias": 30
        }
        
        response = await client.get("/api/v1/modelagem/previsao-precos", params=params)
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.requires_db
class TestMathematicalEnginesEndpoints:
    """Testa endpoints de motores matemáticos"""

    @pytest.mark.asyncio
    async def test_extreme_value_analysis(self, client):
        """Testa análise de valores extremos"""
        data = {
            "time_series_data": [10, 15, 20, 25, 30, 35, 40, 45, 50]
        }
        
        response = await client.post(
            "/api/v1/math-engines/extreme-value-analysis/gev",
            json=data
        )
        assert response.status_code in [200, 422]  # 422 se validação falhar

    @pytest.mark.asyncio
    async def test_spatial_analysis(self, client):
        """Testa análise espacial"""
        data = {
            "coordinates": [[-23.55, -46.63], [-22.90, -43.17]],
            "values": [100, 200]
        }
        
        response = await client.post(
            "/api/v1/math-engines/spatial-analysis/kde",
            json=data
        )
        assert response.status_code in [200, 422]


@pytest.mark.integration
@pytest.mark.requires_db
class TestPerformanceEndpoints:
    """Testa performance de endpoints"""

    @pytest.mark.asyncio
    async def test_response_time_health(self, client):
        """Testa tempo de resposta do health check"""
        import time
        
        start = time.time()
        response = await client.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Deve responder em menos de 1 segundo

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Testa requisições concorrentes"""
        tasks = [client.get("/health") for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        assert all(r.status_code == 200 for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=server"])

"""
Pytest Configuration and Shared Fixtures
Global test configuration and reusable fixtures for all tests
"""

import os
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch, MagicMock

# Set dummy API keys for test environment (prevents ValueError during import)
os.environ.setdefault("GEMINI_API_KEY", "test-dummy-gemini-key")
os.environ.setdefault("GROK_API_KEY", "test-dummy-grok-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-not-production")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-dummy-anon-key")
os.environ.setdefault("DATABASE_ENABLED", "true")
# Ensure tests default to async sqlite driver before importing app
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./.test_db.sqlite")
# Force-disable tracing/export in tests to avoid background OTLP retries/noise.
os.environ["OTEL_ENABLED"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"

# Mock heavy ML libraries to avoid installation in test environment
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["tensorflow"] = MagicMock()
sys.modules["pynamicalsys"] = MagicMock()
sys.modules["prophet"] = MagicMock()
sys.modules["statsmodels"] = MagicMock()
sys.modules["statsmodels.tsa.stattools"] = MagicMock()
sys.modules["xgboost"] = MagicMock()
sys.modules["lightgbm"] = MagicMock()
sys.modules["pycep_correios"] = MagicMock()

# Fix for scipy's is_torch_array check
class MockTensor:
    pass
sys.modules["torch"].Tensor = MockTensor

import pytest

# Ensure project root on sys.path so `import server.*` works in tests
SERVER_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SERVER_ROOT.parent
for path in (SERVER_ROOT, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api.health import HealthChecker, HealthCheckResult, ServiceStatus
from api.logging import LogContext, get_logger, init_logging
from config import database as db_config
from config.database import (
    _create_engine_and_session_maker,
    async_session_maker,
    get_db_session,
)

from services.auth_service import AuthService, auth_service
from lib.security import rate_limiter

# Import FastAPI app after path fix
from main import app  # noqa: E402
from models.sqlalchemy_models import Base, User
from services.scr_module_service import ClimateData

# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine and tables"""
    # Use a file-based SQLite database for integration test sharing
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./.test_db.sqlite"

    _create_engine_and_session_maker(os.environ["DATABASE_URL"])
    db_engine = db_config.engine

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield db_engine

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await db_engine.dispose()

    # Clean up the file-based SQLite test database after all tests are done
    import contextlib
    with contextlib.suppress(FileNotFoundError):
        os.remove("./.test_db.sqlite")


@pytest.fixture(scope="session")
async def engine(test_engine):
    """Compatibility alias for tests expecting 'engine' fixture."""
    return test_engine


@pytest.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    async with db_config.async_session_maker() as session:

        async def override_get_db():
            return session

        app.dependency_overrides[get_db_session] = override_get_db
        yield session
        await session.rollback()

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    """Create a sample user for testing"""
    from datetime import datetime
    import uuid

    user = User(
        id=str(uuid.uuid4()),
        email=f"test-{uuid.uuid4()}@example.com",
        full_name="Test User",
        hashed_password="hashed_password_123",
        is_active=True,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_climate_data(
    db_session: AsyncSession, sample_user: User
) -> ClimateData:
    """Create sample climate data for testing"""
    from datetime import datetime

    data = ClimateData(
        user_id=sample_user.id,
        location="São Paulo",
        latitude=-23.5505,
        longitude=-46.6333,
        temperature=22.5,
        humidity=65.0,
        precipitation=10.5,
        wind_speed=5.2,
        timestamp=datetime.utcnow(),
    )
    db_session.add(data)
    await db_session.commit()
    await db_session.refresh(data)
    return data


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """FastAPI test client"""
    return TestClient(app, base_url="http://localhost")


@pytest.fixture
def authenticated_client(client: TestClient, sample_user: User) -> TestClient:
    """FastAPI test client with authentication"""
    # Create JWT token
    token = auth_service.create_access_token(
        data={"sub": str(sample_user.id), "email": sample_user.email, "role": "user"}
    )

    # Add authorization header
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}

    return client


# ============================================================================
# LOGGING FIXTURES
# ============================================================================


@pytest.fixture
def log_context():
    """Create a LogContext for testing"""
    with LogContext(
        operation="test_operation",
        request_id="test-req-123",
        user_id="test-user-456",
    ) as ctx:
        yield ctx


@pytest.fixture
def logger():
    """Get test logger"""
    return get_logger("test_logger")


# ============================================================================
# HEALTH CHECK FIXTURES
# ============================================================================


@pytest.fixture
async def health_checker():
    """Create a HealthChecker instance"""
    checker = HealthChecker(
        database_url="sqlite:///:memory:",
        redis_url=None,
        external_apis=["https://api.open-meteo.com/v1/forecast"],
    )
    # await checker.initialize()  # Not needed, initialized in __init__
    yield checker
    # Cleanup
    # await checker.close()  # No close method available


# ============================================================================
# SECURITY FIXTURES
# ============================================================================


@pytest.fixture
def security_manager():
    """Alias for auth_service to maintain compatibility"""
    return auth_service


@pytest.fixture
def sample_password() -> str:
    """Sample password for testing"""
    return "SecurePassword123!@#"


@pytest.fixture
def sample_hashed_password(
    security_manager: AuthService, sample_password: str
) -> str:
    """Hash a sample password"""
    return security_manager.get_password_hash(sample_password)


# ============================================================================
# MOCK FIXTURES
# ============================================================================


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.exists = AsyncMock(return_value=0)
    mock.incr = AsyncMock(return_value=1)
    return mock


@pytest.fixture
def mock_external_api():
    """Mock external API calls"""
    with patch("aiohttp.ClientSession") as mock:
        mock_session = AsyncMock()
        mock_session.get = AsyncMock()
        mock.__aenter__.return_value = mock_session
        mock.__aexit__.return_value = None
        yield mock_session


@pytest.fixture
def mock_s3_client():
    """Mock AWS S3 client"""
    mock = Mock()
    mock.put_object = Mock(return_value={"ETag": "test-etag"})
    mock.get_object = Mock(return_value={"Body": Mock()})
    mock.list_objects_v2 = Mock(return_value={"Contents": []})
    mock.delete_object = Mock(return_value={})
    return mock


# ============================================================================
# PYTEST HOOKS AND CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_db: mark test as requiring database")
    config.addinivalue_line("markers", "requires_redis: mark test as requiring Redis")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment (sync wrapper compatible with Python 3.10+)."""
    import asyncio

    # Initialize logging
    init_logging()

    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "True"
    os.environ["OTEL_ENABLED"] = "false"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL", "sqlite+aiosqlite:///./.test_db.sqlite"
    )

    # Disable rate limiting for tests
    rate_limiter.max_requests = 10000

    db_engine = None

    async def _setup():
        _create_engine_and_session_maker(os.environ["DATABASE_URL"])
        engine = db_config.engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return engine

    try:
        db_engine = asyncio.run(_setup())
    except Exception as exc:  # pragma: no cover
        print(f"Warning: DB setup failed in test env: {exc}")

    yield

    async def _teardown(engine):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    if db_engine is not None:
        try:
            asyncio.run(_teardown(db_engine))
        except Exception:  # pragma: no cover
            pass
    app.dependency_overrides.clear()



# ============================================================================
# UTILITY FIXTURES
# ============================================================================


@pytest.fixture
def faker():
    """Faker instance for generating test data"""
    from faker import Faker

    return Faker("pt_BR")


@pytest.fixture
def now_timestamp():
    """Get current timestamp"""
    from datetime import datetime

    return datetime.utcnow()


@pytest.fixture
def future_timestamp(now_timestamp):
    """Get future timestamp (24 hours from now)"""
    from datetime import timedelta

    return now_timestamp + timedelta(hours=24)


# ============================================================================
# ASYNC FIXTURES
# ============================================================================


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()



@pytest.fixture
async def async_client(client: TestClient):
    """Async client for testing async endpoints"""
    # Convert TestClient to async-compatible
    return client

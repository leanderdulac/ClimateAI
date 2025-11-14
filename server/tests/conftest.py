"""
Pytest Configuration and Shared Fixtures
Global test configuration and reusable fixtures for all tests
"""

import os
import sys
from pathlib import Path
from typing import Generator, Any
from unittest.mock import Mock, AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path modification
from main import app, get_db
from api.models import Base, User, ClimateData
from api.logging import LogContext, get_logger, init_logging
from api.health import HealthChecker, HealthCheckResult, ServiceStatus
from core.security import SecurityManager


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_db_url():
    """In-memory SQLite database for testing"""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine(test_db_url):
    """Create test database engine"""
    # SQLite in-memory database for testing
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    # Create new connection and transaction
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    # Configure app to use test session
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create a sample user for testing"""
    from datetime import datetime
    
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password_123",
        is_active=True,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_climate_data(db_session: Session, sample_user: User) -> ClimateData:
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
    db_session.commit()
    db_session.refresh(data)
    return data


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def client(db_session: Session) -> TestClient:
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client: TestClient, sample_user: User) -> TestClient:
    """FastAPI test client with authentication"""
    # Create JWT token
    from core.security import create_access_token
    
    token = create_access_token(
        data={"sub": str(sample_user.id), "email": sample_user.email}
    )
    
    # Add authorization header
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    
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
        external_apis=["https://api.open-meteo.com/v1/forecast"]
    )
    await checker.initialize()
    yield checker
    # Cleanup
    await checker.close()


# ============================================================================
# SECURITY FIXTURES
# ============================================================================

@pytest.fixture
def security_manager():
    """Create a SecurityManager instance"""
    return SecurityManager(
        secret_key="test-secret-key-do-not-use-in-production-1234567890"
    )


@pytest.fixture
def sample_password() -> str:
    """Sample password for testing"""
    return "SecurePassword123!@#"


@pytest.fixture
def sample_hashed_password(security_manager: SecurityManager, sample_password: str) -> str:
    """Hash a sample password"""
    return security_manager.hash_password(sample_password)


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
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring Redis"
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Initialize logging
    init_logging()
    
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "True"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    yield
    
    # Cleanup after all tests
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


@pytest.mark.asyncio
@pytest.fixture
async def async_client(client: TestClient):
    """Async client for testing async endpoints"""
    # Convert TestClient to async-compatible
    return client

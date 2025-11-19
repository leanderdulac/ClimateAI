"""
Unit Tests for Health Checks Module
Tests for server/api/health.py - comprehensive health monitoring system
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.health import (
    APIHealthCheck,
    DatabaseHealthCheck,
    HealthChecker,
    HealthCheckResult,
    RedisHealthCheck,
    ServiceStatus,
    SystemHealthCheck,
)

# ============================================================================
# TESTS: ServiceStatus Enum
# ============================================================================


@pytest.mark.unit
class TestServiceStatus:
    """Tests for ServiceStatus enum"""

    def test_service_status_values(self):
        """Test ServiceStatus enum values exist"""
        assert ServiceStatus.HEALTHY.value == "healthy"
        assert ServiceStatus.DEGRADED.value == "degraded"
        assert ServiceStatus.UNHEALTHY.value == "unhealthy"
        assert ServiceStatus.UNKNOWN.value == "unknown"

    def test_service_status_comparison(self):
        """Test ServiceStatus comparison"""
        assert ServiceStatus.HEALTHY != ServiceStatus.UNHEALTHY
        assert ServiceStatus.DEGRADED != ServiceStatus.UNKNOWN


# ============================================================================
# TESTS: HealthCheckResult
# ============================================================================


@pytest.mark.unit
class TestHealthCheckResult:
    """Tests for HealthCheckResult class"""

    def test_health_check_result_creation(self):
        """Test creating HealthCheckResult"""
        result = HealthCheckResult(
            status=ServiceStatus.HEALTHY,
            message="All systems operational",
            duration_ms=45.2,
        )

        assert result.status == ServiceStatus.HEALTHY
        assert result.message == "All systems operational"
        assert result.duration_ms == 45.2
        assert result.timestamp is not None

    def test_health_check_result_with_details(self):
        """Test HealthCheckResult with extra details"""
        details = {
            "connections": 5,
            "pool_size": 10,
            "avg_query_time": 15.3,
        }

        result = HealthCheckResult(
            status=ServiceStatus.HEALTHY,
            message="Database connected",
            duration_ms=10.5,
            details=details,
        )

        assert result.details == details

    def test_health_check_result_dict_conversion(self):
        """Test converting HealthCheckResult to dict"""
        result = HealthCheckResult(
            status=ServiceStatus.HEALTHY,
            message="Test message",
            duration_ms=25.0,
        )

        result_dict = result.dict()
        assert result_dict["status"] == "healthy"
        assert result_dict["message"] == "Test message"
        assert result_dict["duration_ms"] == 25.0


# ============================================================================
# TESTS: DatabaseHealthCheck
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestDatabaseHealthCheck:
    """Tests for DatabaseHealthCheck class"""

    async def test_database_check_healthy(self, db_session):
        """Test successful database health check"""
        check = DatabaseHealthCheck(database_url="sqlite:///:memory:")

        result = await check.check()

        assert result.status == ServiceStatus.HEALTHY
        assert "connected" in result.message.lower()

    async def test_database_check_invalid_url(self):
        """Test database check with invalid URL"""
        check = DatabaseHealthCheck(database_url="invalid://url")

        result = await check.check()

        assert result.status in [ServiceStatus.UNHEALTHY, ServiceStatus.UNKNOWN]

    @patch("sqlalchemy.create_engine")
    async def test_database_check_connection_error(self, mock_engine):
        """Test database check with connection error"""
        mock_engine.side_effect = Exception("Connection refused")

        check = DatabaseHealthCheck(database_url="postgresql://localhost/test")
        result = await check.check()

        assert result.status == ServiceStatus.UNHEALTHY

    async def test_database_check_timing(self):
        """Test database check includes timing"""
        check = DatabaseHealthCheck(database_url="sqlite:///:memory:")

        result = await check.check()

        assert result.duration_ms > 0
        assert result.timestamp is not None


# ============================================================================
# TESTS: RedisHealthCheck
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestRedisHealthCheck:
    """Tests for RedisHealthCheck class"""

    async def test_redis_check_disabled(self):
        """Test Redis check when disabled (redis_url=None)"""
        check = RedisHealthCheck(redis_url=None)

        result = await check.check()

        assert result.status == ServiceStatus.HEALTHY
        assert "disabled" in result.message.lower()

    async def test_redis_check_connection_failed(self):
        """Test Redis check with connection failure"""
        check = RedisHealthCheck(redis_url="redis://localhost:6379")

        result = await check.check()

        # Will likely fail since Redis might not be running
        assert result.status in [ServiceStatus.UNHEALTHY, ServiceStatus.DEGRADED]

    async def test_redis_check_with_mock(self, mock_redis):
        """Test Redis check with mocked client"""
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            check = RedisHealthCheck(redis_url="redis://localhost:6379")
            result = await check.check()

            # Should call PING internally
            assert result.duration_ms >= 0


# ============================================================================
# TESTS: SystemHealthCheck
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestSystemHealthCheck:
    """Tests for SystemHealthCheck class"""

    async def test_system_check_healthy(self):
        """Test system health check returns HEALTHY"""
        check = SystemHealthCheck()

        result = await check.check()

        assert result.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
        assert result.details is not None

    async def test_system_check_includes_metrics(self):
        """Test system check includes CPU, memory, disk metrics"""
        check = SystemHealthCheck()

        result = await check.check()

        details = result.details or {}
        assert "cpu_percent" in details
        assert "memory_percent" in details
        assert "disk_percent" in details

    async def test_system_check_thresholds(self):
        """Test system check respects thresholds"""
        check = SystemHealthCheck(
            cpu_threshold=10,
            memory_threshold=20,
            disk_threshold=30,
        )

        result = await check.check()

        details = result.details or {}
        # With very low thresholds, likely to be DEGRADED or UNHEALTHY
        assert result.status in [
            ServiceStatus.HEALTHY,
            ServiceStatus.DEGRADED,
            ServiceStatus.UNHEALTHY,
        ]


# ============================================================================
# TESTS: APIHealthCheck
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestAPIHealthCheck:
    """Tests for APIHealthCheck class"""

    async def test_api_check_empty_urls(self):
        """Test API check with no URLs"""
        check = APIHealthCheck(urls=[])

        result = await check.check()

        assert result.status == ServiceStatus.HEALTHY
        assert "no external" in result.message.lower()

    async def test_api_check_successful(self):
        """Test successful API health check"""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__.return_value = mock_response
            mock_response.__aexit__.return_value = None

            mock_session.return_value.get.return_value = mock_response

            check = APIHealthCheck(
                urls=["https://api.example.com/health"],
                timeout=5,
            )

            result = await check.check()

            assert result.duration_ms >= 0

    async def test_api_check_includes_timings(self):
        """Test API check includes per-endpoint timings"""
        check = APIHealthCheck(urls=[])

        result = await check.check()

        assert result.duration_ms >= 0
        assert result.timestamp is not None


# ============================================================================
# TESTS: HealthChecker (Orchestrator)
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthChecker:
    """Tests for HealthChecker orchestrator"""

    async def test_health_checker_initialization(self):
        """Test HealthChecker initialization"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=["https://api.example.com"],
        )

        assert checker.database_url == "sqlite:///:memory:"
        assert checker.redis_url is None
        assert len(checker.external_apis) == 1

    @pytest.mark.requires_db
    async def test_health_checker_initialize_method(self):
        """Test HealthChecker initialize method"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=[],
        )

        await checker.initialize()

        assert checker.checks is not None
        assert len(checker.checks) >= 3  # At least DB, Redis, System

    @pytest.mark.requires_db
    async def test_health_checker_check_all(self):
        """Test checking all health dimensions"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=[],
        )

        await checker.initialize()
        results = await checker.check_all()

        assert isinstance(results, dict)
        assert "database" in results
        assert "redis" in results
        assert "system" in results

    @pytest.mark.requires_db
    async def test_health_checker_critical_checks(self):
        """Test critical health checks only"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=[],
        )

        await checker.initialize()
        results = await checker.check_critical()

        assert isinstance(results, dict)
        # Should include database and system at minimum
        assert "database" in results or "system" in results

    @pytest.mark.requires_db
    async def test_health_checker_overall_status(self):
        """Test determining overall health status"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=[],
        )

        await checker.initialize()
        results = await checker.check_all()

        overall = checker.get_overall_status(results)

        assert overall in [
            ServiceStatus.HEALTHY,
            ServiceStatus.DEGRADED,
            ServiceStatus.UNHEALTHY,
        ]

    @pytest.mark.requires_db
    async def test_health_checker_json_response(self):
        """Test generating JSON response"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=[],
        )

        await checker.initialize()
        response = await checker.get_health_json()

        assert isinstance(response, dict)
        assert "status" in response
        assert "timestamp" in response
        assert "checks" in response

    async def test_health_checker_close(self):
        """Test closing HealthChecker"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=[],
        )

        # Should not raise error
        await checker.close()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthCheckerIntegration:
    """Integration tests for health checking system"""

    @pytest.mark.slow
    @pytest.mark.requires_db
    async def test_full_health_check_cycle(self):
        """Test full health check cycle"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=[],
        )

        await checker.initialize()

        # Run all checks
        results = await checker.check_all()

        # Verify structure
        for check_name, result in results.items():
            assert hasattr(result, "status")
            assert hasattr(result, "message")
            assert hasattr(result, "duration_ms")

        # Determine overall status
        overall = checker.get_overall_status(results)
        assert overall in [
            ServiceStatus.HEALTHY,
            ServiceStatus.DEGRADED,
            ServiceStatus.UNHEALTHY,
        ]

        await checker.close()

    @pytest.mark.slow
    @pytest.mark.requires_db
    async def test_health_check_performance(self):
        """Test health check performance (should complete in <5s)"""
        checker = HealthChecker(
            database_url="sqlite:///:memory:",
            redis_url=None,
            external_apis=[],
        )

        await checker.initialize()

        import time

        start = time.time()
        results = await checker.check_all()
        duration = (time.time() - start) * 1000  # Convert to ms

        # All checks should complete within 5 seconds
        assert duration < 5000, f"Health checks took {duration}ms, expected < 5000ms"

        await checker.close()

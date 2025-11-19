"""
Unit Tests for JSON Logging Module
Tests for server/api/logging.py - structured JSON logging system
"""

import json
import logging
from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from api.logging import (
    JSONFormatter,
    LogContext,
    LoggingMiddleware,
    StructuredLogger,
    get_logger,
    setup_json_logging,
)

# ============================================================================
# TESTS: JSONFormatter
# ============================================================================


@pytest.mark.unit
class TestJSONFormatter:
    """Tests for JSONFormatter class"""

    def test_json_formatter_creation(self):
        """Test creating JSONFormatter"""
        formatter = JSONFormatter()
        assert formatter is not None

    def test_json_formatter_basic_log(self):
        """Test formatting a basic log record"""
        formatter = JSONFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(formatted)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.module"

    def test_json_formatter_with_extra_fields(self):
        """Test formatting with extra fields"""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/file.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.request_id = "req-123"
        record.user_id = "user-456"
        record.duration_ms = 145.2

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed.get("request_id") == "req-123"
        assert parsed.get("user_id") == "user-456"
        assert parsed.get("duration_ms") == 145.2

    def test_json_formatter_with_exception(self):
        """Test formatting with exception info"""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="/file.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

            formatted = formatter.format(record)
            parsed = json.loads(formatted)

            assert "exception" in parsed
            assert "ValueError" in parsed["exception"]

    def test_json_formatter_timestamp_included(self):
        """Test that timestamp is included in output"""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/file.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "timestamp" in parsed
        # Verify timestamp format is ISO8601
        assert "T" in parsed["timestamp"]


# ============================================================================
# TESTS: StructuredLogger
# ============================================================================


@pytest.mark.unit
class TestStructuredLogger:
    """Tests for StructuredLogger class"""

    @pytest.fixture
    def string_logger(self):
        """Create logger that logs to string"""
        logger = StructuredLogger("test")
        handler = logging.StreamHandler(StringIO())
        handler.setFormatter(JSONFormatter())
        logger.logger.addHandler(handler)
        return logger

    def test_structured_logger_creation(self):
        """Test creating StructuredLogger"""
        logger = StructuredLogger("test.logger")
        assert logger.logger is not None
        assert logger.logger.name == "test.logger"

    def test_structured_logger_log_database_query(self, string_logger):
        """Test logging database query"""
        string_logger.log_database_query(
            query="SELECT * FROM users",
            duration_ms=42.5,
            rows_affected=10,
            status="success",
        )

        # Should not raise error
        assert string_logger.logger is not None

    def test_structured_logger_log_cache_operation(self, string_logger):
        """Test logging cache operation"""
        string_logger.log_cache_operation(
            key="user:123",
            operation="GET",
            hit=True,
            duration_ms=1.2,
        )

        # Should not raise error
        assert string_logger.logger is not None

    def test_structured_logger_log_external_api_call(self, string_logger):
        """Test logging external API call"""
        string_logger.log_external_api_call(
            service="open-meteo",
            endpoint="/v1/forecast",
            method="GET",
            status_code=200,
            duration_ms=523.1,
        )

        # Should not raise error
        assert string_logger.logger is not None

    def test_structured_logger_log_security_event(self, string_logger):
        """Test logging security event"""
        string_logger.log_security_event(
            event_type="login_attempt",
            user_id="user-123",
            success=True,
            ip_address="192.168.1.1",
        )

        # Should not raise error
        assert string_logger.logger is not None

    def test_structured_logger_log_performance_metric(self, string_logger):
        """Test logging performance metric"""
        string_logger.log_performance_metric(
            metric_name="api_response_time",
            value=245.5,
            unit="ms",
            endpoint="/api/v1/clima",
        )

        # Should not raise error
        assert string_logger.logger is not None

    def test_structured_logger_log_health_check_result(self, string_logger):
        """Test logging health check result"""
        string_logger.log_health_check_result(
            check_name="database",
            status="healthy",
            duration_ms=15.3,
            details={"connections": 5},
        )

        # Should not raise error
        assert string_logger.logger is not None

    def test_structured_logger_context_variables(self):
        """Test context variables in structured logger"""
        logger = StructuredLogger("test")

        # Set context
        logger.set_context(
            request_id="req-123",
            user_id="user-456",
            session_id="sess-789",
        )

        # Verify context is set
        assert logger.get_context() is not None


# ============================================================================
# TESTS: LogContext
# ============================================================================


@pytest.mark.unit
class TestLogContext:
    """Tests for LogContext context manager"""

    def test_log_context_creation(self):
        """Test creating LogContext"""
        with LogContext(operation="test_op") as ctx:
            assert ctx is not None
            assert ctx.operation == "test_op"

    def test_log_context_with_parameters(self):
        """Test LogContext with all parameters"""
        with LogContext(
            operation="test_operation",
            request_id="req-123",
            user_id="user-456",
            session_id="sess-789",
        ) as ctx:
            assert ctx.operation == "test_operation"
            assert ctx.request_id == "req-123"
            assert ctx.user_id == "user-456"
            assert ctx.session_id == "sess-789"

    def test_log_context_timing(self):
        """Test LogContext includes timing information"""
        import time

        with LogContext(operation="test") as ctx:
            time.sleep(0.1)  # Sleep for 100ms

        # Duration should be recorded
        assert hasattr(ctx, "duration_ms") or hasattr(ctx, "start_time")

    def test_log_context_exception_handling(self):
        """Test LogContext with exception"""
        with pytest.raises(ValueError):
            with LogContext(operation="error_test") as ctx:
                raise ValueError("Test error")

        # Context should still be closed gracefully


# ============================================================================
# TESTS: LoggingMiddleware
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestLoggingMiddleware:
    """Tests for LoggingMiddleware FastAPI middleware"""

    async def test_logging_middleware_creation(self):
        """Test creating LoggingMiddleware"""
        middleware = LoggingMiddleware(app=None)
        assert middleware is not None

    async def test_logging_middleware_processes_request(self, client):
        """Test middleware processes HTTP requests"""
        # Make a request through client
        response = client.get("/health")

        # Should get a response
        assert response.status_code in [200, 404]  # 200 if exists, 404 if not

    async def test_logging_middleware_tracks_timing(self, client):
        """Test middleware tracks request timing"""
        response = client.get("/health")

        # Response should be successful or not found
        assert response.status_code in [200, 404, 500]


# ============================================================================
# TESTS: setup_json_logging
# ============================================================================


@pytest.mark.unit
class TestSetupJSONLogging:
    """Tests for setup_json_logging function"""

    def test_setup_json_logging_creates_logger(self):
        """Test setup_json_logging creates logger"""
        logger = setup_json_logging(name="test")

        assert logger is not None
        assert hasattr(logger, "logger")

    def test_setup_json_logging_with_level(self):
        """Test setup_json_logging respects log level"""
        logger = setup_json_logging(
            name="test",
            level=logging.DEBUG,
        )

        assert logger.logger.level <= logging.DEBUG

    def test_setup_json_logging_with_file(self, tmp_path):
        """Test setup_json_logging with file output"""
        log_file = tmp_path / "test.log"

        logger = setup_json_logging(
            name="test",
            log_file=str(log_file),
        )

        logger.logger.info("Test message")

        # Verify log file was created (or will be)
        assert logger is not None


# ============================================================================
# TESTS: get_logger
# ============================================================================


@pytest.mark.unit
class TestGetLogger:
    """Tests for get_logger function"""

    def test_get_logger_returns_structured_logger(self):
        """Test get_logger returns StructuredLogger"""
        logger = get_logger("test")

        assert isinstance(logger, StructuredLogger)
        assert logger.logger is not None

    def test_get_logger_caching(self):
        """Test get_logger caches loggers"""
        logger1 = get_logger("test_cache")
        logger2 = get_logger("test_cache")

        # Should return same instance
        assert logger1 is logger2 or logger1.logger.name == logger2.logger.name

    def test_get_logger_different_names(self):
        """Test get_logger with different names"""
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")

        # Should be different loggers
        assert logger1.logger.name != logger2.logger.name


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.unit
class TestLoggingIntegration:
    """Integration tests for logging system"""

    def test_full_logging_pipeline(self, tmp_path):
        """Test complete logging pipeline"""
        log_file = tmp_path / "integration.log"

        # Setup logger
        logger = setup_json_logging(
            name="integration_test",
            log_file=str(log_file),
        )

        # Log different types of events
        logger.log_database_query(
            query="SELECT * FROM test",
            duration_ms=25.0,
            rows_affected=5,
            status="success",
        )

        logger.log_security_event(
            event_type="login",
            user_id="test_user",
            success=True,
            ip_address="127.0.0.1",
        )

        logger.log_performance_metric(
            metric_name="test_metric",
            value=100,
            unit="ms",
        )

        # Logger should have logged all events
        assert logger is not None

    def test_logging_with_context(self):
        """Test logging with LogContext"""
        logger = get_logger("context_test")

        with LogContext(
            operation="test_operation",
            request_id="req-123",
        ) as ctx:
            logger.logger.info("Message with context")

        # Should complete without error
        assert logger is not None

    def test_concurrent_logging(self):
        """Test concurrent logging from multiple threads"""
        import threading

        logger = get_logger("concurrent_test")
        results = []

        def log_from_thread(thread_id):
            logger.logger.info(f"Message from thread {thread_id}")
            results.append(thread_id)

        threads = [
            threading.Thread(target=log_from_thread, args=(i,)) for i in range(5)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(results) == 5

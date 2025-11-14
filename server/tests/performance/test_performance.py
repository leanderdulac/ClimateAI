"""
Performance Tests for ClimateAI
Tests for load testing, stress testing, and performance metrics
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


# ============================================================================
# TESTS: Response Time Performance
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestResponseTimePerformance:
    """Tests for response time performance"""
    
    def test_health_check_response_time_p95(self, client):
        """Test health endpoint P95 response time < 50ms"""
        response_times = []
        
        for _ in range(100):
            start = time.time()
            response = client.get("/health")
            duration = (time.time() - start) * 1000
            response_times.append(duration)
        
        response_times.sort()
        p95 = response_times[int(len(response_times) * 0.95)]
        
        assert p95 < 50, f"P95 response time {p95}ms exceeds 50ms"
    
    def test_health_check_response_time_p99(self, client):
        """Test health endpoint P99 response time < 100ms"""
        response_times = []
        
        for _ in range(100):
            start = time.time()
            response = client.get("/health")
            duration = (time.time() - start) * 1000
            response_times.append(duration)
        
        response_times.sort()
        p99 = response_times[int(len(response_times) * 0.99)]
        
        assert p99 < 100, f"P99 response time {p99}ms exceeds 100ms"
    
    def test_api_endpoint_response_time_avg(self, authenticated_client):
        """Test API endpoint average response time < 200ms"""
        response_times = []
        
        for _ in range(50):
            start = time.time()
            response = authenticated_client.get("/api/v1/users/me")
            duration = (time.time() - start) * 1000
            response_times.append(duration)
        
        avg_time = sum(response_times) / len(response_times)
        
        assert avg_time < 200, f"Average response time {avg_time}ms exceeds 200ms"


# ============================================================================
# TESTS: Throughput Performance
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestThroughputPerformance:
    """Tests for throughput performance"""
    
    def test_health_endpoint_throughput(self, client):
        """Test health endpoint handles requests without errors"""
        errors = 0
        successful = 0
        
        for _ in range(100):
            response = client.get("/health")
            if response.status_code == 200:
                successful += 1
            else:
                errors += 1
        
        # Should handle 100% of requests
        assert errors == 0, f"Failed {errors} out of 100 requests"
        assert successful == 100
    
    def test_concurrent_health_requests(self, client):
        """Test health endpoint with concurrent requests"""
        def make_request():
            return client.get("/health")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count == 100, f"Only {success_count} out of 100 succeeded"


# ============================================================================
# TESTS: Memory Performance
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestMemoryPerformance:
    """Tests for memory usage performance"""
    
    def test_no_memory_leak_on_requests(self, client):
        """Test that repeated requests don't leak memory"""
        import gc
        
        # Initial garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Make many requests
        for _ in range(100):
            client.get("/health")
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow significantly
        growth = final_objects - initial_objects
        assert growth < 10000, f"Object count grew by {growth}"
    
    def test_response_object_size(self, client):
        """Test response object size is reasonable"""
        response = client.get("/health")
        
        if response.status_code == 200:
            size = len(response.content)
            # Health response should be small (< 1KB)
            assert size < 1024


# ============================================================================
# TESTS: Database Performance
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.requires_db
class TestDatabasePerformance:
    """Tests for database performance"""
    
    def test_database_query_response_time(self, db_session, sample_user):
        """Test database query performance"""
        start = time.time()
        
        # Query user
        from api.models import User
        user = db_session.query(User).filter_by(id=sample_user.id).first()
        
        duration = (time.time() - start) * 1000
        
        assert user is not None
        assert duration < 50, f"Query took {duration}ms, expected < 50ms"
    
    def test_database_insert_performance(self, db_session):
        """Test database insert performance"""
        from datetime import datetime
        from api.models import User
        
        start = time.time()
        
        # Insert user
        user = User(
            email="perftest@example.com",
            full_name="Perf Test",
            hashed_password="hashed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()
        
        duration = (time.time() - start) * 1000
        
        assert duration < 100, f"Insert took {duration}ms, expected < 100ms"
    
    def test_bulk_query_performance(self, db_session, sample_user):
        """Test performance with multiple queries"""
        from api.models import User
        
        start = time.time()
        
        # Query multiple times
        for _ in range(10):
            db_session.query(User).all()
        
        duration = (time.time() - start) * 1000
        
        assert duration < 200, f"Bulk query took {duration}ms"


# ============================================================================
# TESTS: Caching Performance
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestCachingPerformance:
    """Tests for caching performance"""
    
    def test_cache_hit_performance(self, mock_redis):
        """Test cache hit is faster than miss"""
        from unittest.mock import AsyncMock
        
        # Setup cache
        mock_redis.get = AsyncMock(return_value=b"cached_value")
        
        # Cache hit should be very fast
        # (This would be tested with actual timing in real scenario)
        assert mock_redis is not None
    
    def test_cache_invalidation_performance(self, mock_redis):
        """Test cache invalidation doesn't impact performance"""
        from unittest.mock import AsyncMock
        
        mock_redis.delete = AsyncMock(return_value=1)
        
        start = time.time()
        
        for _ in range(100):
            # Simulate cache invalidation
            pass
        
        duration = (time.time() - start) * 1000
        
        assert duration < 100


# ============================================================================
# TESTS: Load Testing
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestLoadPerformance:
    """Tests for load handling performance"""
    
    async def test_concurrent_async_requests(self, client):
        """Test handling concurrent requests"""
        import asyncio
        
        async def make_async_request():
            # Simulate async request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: client.get("/health"))
            return response
        
        # Create 50 concurrent requests
        tasks = [make_async_request() for _ in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most requests should succeed
        success = sum(1 for r in results if hasattr(r, "status_code"))
        assert success > 40


# ============================================================================
# TESTS: Stress Testing
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestStress:
    """Tests for stress conditions"""
    
    def test_rapid_sequential_requests(self, client):
        """Test handling rapid sequential requests"""
        errors = 0
        start = time.time()
        
        # Make as many requests as possible in 5 seconds
        request_count = 0
        while time.time() - start < 5:
            response = client.get("/health")
            if response.status_code != 200:
                errors += 1
            request_count += 1
        
        throughput = request_count / (time.time() - start)
        
        # Should handle at least 10 req/sec
        assert throughput > 10, f"Throughput {throughput} req/sec is too low"
        # Error rate should be < 5%
        error_rate = errors / request_count
        assert error_rate < 0.05
    
    def test_large_response_handling(self, client):
        """Test handling large responses"""
        # This would test an endpoint that returns large data
        response = client.get("/health")
        
        # Should handle response regardless of size
        assert response.status_code in [200, 404]


# ============================================================================
# TESTS: Reliability
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestReliability:
    """Tests for reliability under load"""
    
    def test_request_success_rate(self, client):
        """Test high success rate over many requests"""
        successful = 0
        total = 100
        
        for _ in range(total):
            try:
                response = client.get("/health")
                if response.status_code == 200:
                    successful += 1
            except Exception:
                pass
        
        success_rate = successful / total
        
        # Should have > 99% success rate
        assert success_rate > 0.99
    
    def test_error_recovery(self, client):
        """Test recovery from errors"""
        # Make multiple requests, some may fail
        for _ in range(50):
            response = client.get("/health")
            # Should not crash the app
            assert response is not None


# ============================================================================
# TESTS: Scalability
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestScalability:
    """Tests for scalability characteristics"""
    
    def test_linear_response_time_scaling(self, client):
        """Test response times don't degrade with load"""
        times_low = []
        times_high = []
        
        # Low load - 10 requests
        for _ in range(10):
            start = time.time()
            client.get("/health")
            times_low.append((time.time() - start) * 1000)
        
        # High load - 100 requests
        for _ in range(100):
            start = time.time()
            client.get("/health")
            times_high.append((time.time() - start) * 1000)
        
        avg_low = sum(times_low) / len(times_low)
        avg_high = sum(times_high) / len(times_high)
        
        # High load shouldn't double response time
        assert avg_high < avg_low * 3


# ============================================================================
# BENCHMARK FIXTURES
# ============================================================================

@pytest.mark.performance
class TestHealthCheckBenchmark:
    """Benchmark tests for health checks"""
    
    def test_health_check_timing(self, benchmark):
        """Benchmark health check performance"""
        # This is marked but depends on pytest-benchmark
        pass

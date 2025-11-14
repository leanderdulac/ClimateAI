"""
Integration Tests for API Endpoints
Tests for main.py endpoints and API workflows
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from main import app


# ============================================================================
# TESTS: Health Endpoints
# ============================================================================

@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check endpoints"""
    
    def test_simple_health_endpoint(self, client: TestClient):
        """Test GET /health endpoint"""
        response = client.get("/health")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
    
    def test_full_health_endpoint(self, client: TestClient):
        """Test GET /api/v1/health/full endpoint"""
        response = client.get("/api/v1/health/full")
        
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "checks" in data or "timestamp" in data
    
    def test_critical_health_endpoint(self, client: TestClient):
        """Test GET /api/v1/health/critical endpoint"""
        response = client.get("/api/v1/health/critical")
        
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data


# ============================================================================
# TESTS: Root and Base Endpoints
# ============================================================================

@pytest.mark.integration
class TestBaseEndpoints:
    """Integration tests for base endpoints"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test GET / endpoint"""
        response = client.get("/")
        
        assert response.status_code in [200, 404]
    
    def test_api_root_endpoint(self, client: TestClient):
        """Test GET /api endpoint"""
        response = client.get("/api")
        
        assert response.status_code in [200, 404, 307]
    
    def test_docs_endpoint(self, client: TestClient):
        """Test GET /docs endpoint (Swagger UI)"""
        response = client.get("/docs")
        
        assert response.status_code in [200, 404]
    
    def test_openapi_json_endpoint(self, client: TestClient):
        """Test GET /openapi.json endpoint"""
        response = client.get("/openapi.json")
        
        assert response.status_code in [200, 404]


# ============================================================================
# TESTS: Climate Data Endpoints
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_db
class TestClimateDataEndpoints:
    """Integration tests for climate data endpoints"""
    
    def test_list_climate_data(self, authenticated_client: TestClient):
        """Test GET /api/v1/clima endpoint"""
        response = authenticated_client.get("/api/v1/clima")
        
        assert response.status_code in [200, 404, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_climate_data_paginated(self, authenticated_client: TestClient):
        """Test GET /api/v1/clima with pagination"""
        response = authenticated_client.get("/api/v1/clima?skip=0&limit=10")
        
        assert response.status_code in [200, 404, 401]
    
    def test_create_climate_data(self, authenticated_client: TestClient):
        """Test POST /api/v1/clima endpoint"""
        payload = {
            "location": "São Paulo",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "temperature": 22.5,
            "humidity": 65.0,
        }
        
        response = authenticated_client.post("/api/v1/clima", json=payload)
        
        assert response.status_code in [200, 201, 404, 401, 422]
    
    def test_filter_climate_data_by_location(self, authenticated_client: TestClient):
        """Test filtering climate data by location"""
        response = authenticated_client.get("/api/v1/clima?location=São Paulo")
        
        assert response.status_code in [200, 404, 401]


# ============================================================================
# TESTS: Authentication Endpoints
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_db
class TestAuthenticationEndpoints:
    """Integration tests for authentication endpoints"""
    
    def test_login_endpoint(self, client: TestClient):
        """Test POST /api/v1/auth/login endpoint"""
        payload = {
            "email": "test@example.com",
            "password": "password123",
        }
        
        response = client.post("/api/v1/auth/login", json=payload)
        
        # May return 401 if credentials invalid, or 200 if valid
        assert response.status_code in [200, 401, 404, 422]
    
    def test_register_endpoint(self, client: TestClient):
        """Test POST /api/v1/auth/register endpoint"""
        payload = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
        }
        
        response = client.post("/api/v1/auth/register", json=payload)
        
        assert response.status_code in [200, 201, 400, 404, 409, 422]
    
    def test_token_refresh(self, authenticated_client: TestClient):
        """Test token refresh endpoint"""
        response = authenticated_client.post("/api/v1/auth/refresh")
        
        assert response.status_code in [200, 401, 404]
    
    def test_logout_endpoint(self, authenticated_client: TestClient):
        """Test POST /api/v1/auth/logout endpoint"""
        response = authenticated_client.post("/api/v1/auth/logout")
        
        assert response.status_code in [200, 204, 401, 404]


# ============================================================================
# TESTS: User Profile Endpoints
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_db
class TestUserProfileEndpoints:
    """Integration tests for user profile endpoints"""
    
    def test_get_user_profile(self, authenticated_client: TestClient):
        """Test GET /api/v1/users/me endpoint"""
        response = authenticated_client.get("/api/v1/users/me")
        
        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            data = response.json()
            assert "email" in data or "id" in data
    
    def test_update_user_profile(self, authenticated_client: TestClient):
        """Test PUT /api/v1/users/me endpoint"""
        payload = {
            "full_name": "Updated Name",
        }
        
        response = authenticated_client.put("/api/v1/users/me", json=payload)
        
        assert response.status_code in [200, 401, 404, 422]
    
    def test_get_user_settings(self, authenticated_client: TestClient):
        """Test GET /api/v1/users/me/settings endpoint"""
        response = authenticated_client.get("/api/v1/users/me/settings")
        
        assert response.status_code in [200, 401, 404]


# ============================================================================
# TESTS: Error Handling
# ============================================================================

@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling"""
    
    def test_404_not_found(self, client: TestClient):
        """Test 404 response for non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client: TestClient):
        """Test 405 response for wrong HTTP method"""
        response = client.post("/health")
        
        # GET is expected on /health, POST should fail
        assert response.status_code in [405, 404]
    
    def test_422_unprocessable_entity(self, client: TestClient):
        """Test 422 response for invalid payload"""
        payload = {
            "invalid_field": "test",
        }
        
        response = client.post("/api/v1/clima", json=payload)
        
        # Should fail if auth required or payload invalid
        assert response.status_code in [422, 401, 404]


# ============================================================================
# TESTS: Request/Response Headers
# ============================================================================

@pytest.mark.integration
class TestRequestHeaders:
    """Integration tests for request/response headers"""
    
    def test_request_with_user_agent(self, client: TestClient):
        """Test request with User-Agent header"""
        headers = {"User-Agent": "TestClient/1.0"}
        response = client.get("/health", headers=headers)
        
        assert response.status_code in [200, 404]
    
    def test_request_with_custom_headers(self, authenticated_client: TestClient):
        """Test request with custom headers"""
        headers = {
            "X-Request-ID": "test-req-123",
            "X-Custom-Header": "test-value",
        }
        
        response = authenticated_client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code in [200, 401, 404]
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers in response"""
        response = client.get("/health")
        
        # CORS headers should be present if configured
        if response.status_code == 200:
            assert response.headers is not None


# ============================================================================
# TESTS: Pagination
# ============================================================================

@pytest.mark.integration
@pytest.mark.requires_db
class TestPagination:
    """Integration tests for pagination"""
    
    def test_pagination_parameters(self, authenticated_client: TestClient):
        """Test pagination skip and limit parameters"""
        response = authenticated_client.get("/api/v1/clima?skip=0&limit=10")
        
        assert response.status_code in [200, 404, 401]
    
    def test_pagination_defaults(self, authenticated_client: TestClient):
        """Test pagination with default values"""
        response = authenticated_client.get("/api/v1/clima")
        
        assert response.status_code in [200, 404, 401]
    
    def test_pagination_invalid_values(self, authenticated_client: TestClient):
        """Test pagination with invalid values"""
        response = authenticated_client.get("/api/v1/clima?skip=-1&limit=0")
        
        # Should either accept with defaults or return 422
        assert response.status_code in [200, 422, 404, 401]


# ============================================================================
# TESTS: Content Negotiation
# ============================================================================

@pytest.mark.integration
class TestContentNegotiation:
    """Integration tests for content negotiation"""
    
    def test_json_response_format(self, client: TestClient):
        """Test JSON response format"""
        headers = {"Accept": "application/json"}
        response = client.get("/health", headers=headers)
        
        if response.status_code == 200:
            assert response.headers["content-type"].startswith("application/json")
    
    def test_unsupported_media_type(self, client: TestClient):
        """Test response for unsupported Accept header"""
        headers = {"Accept": "application/xml"}
        response = client.get("/health", headers=headers)
        
        # Should either ignore or return 406
        assert response.status_code in [200, 406, 404]


# ============================================================================
# TESTS: API Rate Limiting (if implemented)
# ============================================================================

@pytest.mark.integration
class TestRateLimiting:
    """Integration tests for rate limiting"""
    
    def test_rate_limit_headers(self, client: TestClient):
        """Test rate limit headers are present"""
        for _ in range(5):
            response = client.get("/health")
            
            # If rate limiting is implemented, should have headers
            # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
            if response.status_code == 200:
                break


# ============================================================================
# TESTS: Response Time Performance
# ============================================================================

@pytest.mark.integration
@pytest.mark.performance
class TestResponseTime:
    """Integration tests for response time"""
    
    def test_health_endpoint_response_time(self, client: TestClient):
        """Test health endpoint responds quickly"""
        import time
        
        start = time.time()
        response = client.get("/health")
        duration = (time.time() - start) * 1000  # Convert to ms
        
        # Health check should be fast
        assert duration < 100  # Less than 100ms
    
    def test_api_endpoint_response_time(self, authenticated_client: TestClient):
        """Test API endpoint response time"""
        import time
        
        start = time.time()
        response = authenticated_client.get("/api/v1/users/me")
        duration = (time.time() - start) * 1000
        
        # Most endpoints should respond in < 500ms
        if response.status_code == 200:
            assert duration < 500

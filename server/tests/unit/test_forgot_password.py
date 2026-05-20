import pytest
from fastapi.testclient import TestClient
from server.main import app
from unittest.mock import AsyncMock, patch

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("config.supabase_client.get_supabase_client") as mock:
        mock_client = AsyncMock()
        mock_client.auth.reset_password_for_email = AsyncMock()
        mock.return_value = mock_client
        yield mock_client

def test_forgot_password_success(mock_supabase):
    response = client.post("/api/v1/auth/forgot-password", json={"email": "test@example.com"})
    assert response.status_code == 200
    assert "detail" in response.json()
    mock_supabase.auth.reset_password_for_email.assert_awaited_once()

def test_forgot_password_supabase_error(mock_supabase):
    mock_supabase.auth.reset_password_for_email.side_effect = Exception("supabase error")
    response = client.post("/api/v1/auth/forgot-password", json={"email": "test@example.com"})
    assert response.status_code == 200
    assert "detail" in response.json()

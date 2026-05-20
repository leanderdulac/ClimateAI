"""
Unit tests for the /api/v1/auth/forgot-password endpoint.
These tests are self-contained: they instantiate the router directly
to avoid the session-scoped autouse fixtures in the parent conftest.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


# ── App fixture (isolated from main app to avoid conftest session fixtures) ──

@pytest.fixture(scope="module")
def forgot_password_app():
    """Create a minimal FastAPI app with only the forgot-password router."""
    from api.auth_forgot_password import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture(scope="module")
def client(forgot_password_app):
    return TestClient(forgot_password_app)


# ── Tests ────────────────────────────────────────────────────────────────────

def test_forgot_password_returns_200_and_detail(client):
    """Endpoint returns 200 with a 'detail' key regardless of email existence."""
    mock_supabase = MagicMock()
    mock_supabase.auth.reset_password_for_email = MagicMock(return_value=None)

    with patch("api.auth_forgot_password.get_supabase_client", return_value=mock_supabase):
        response = client.post("/forgot-password", json={"email": "user@example.com"})

    assert response.status_code == 200
    assert "detail" in response.json()


def test_forgot_password_calls_supabase_with_correct_email(client):
    """Endpoint passes the submitted email to Supabase's sync method."""
    mock_supabase = MagicMock()
    mock_reset = MagicMock(return_value=None)
    mock_supabase.auth.reset_password_for_email = mock_reset

    with patch("api.auth_forgot_password.get_supabase_client", return_value=mock_supabase):
        client.post("/forgot-password", json={"email": "target@example.com"})

    mock_reset.assert_called_once()
    assert mock_reset.call_args.args[0] == "target@example.com"


def test_forgot_password_supabase_error_still_200(client):
    """Supabase exceptions are swallowed; endpoint always returns 200 (no info leak)."""
    mock_supabase = MagicMock()
    mock_supabase.auth.reset_password_for_email = MagicMock(
        side_effect=Exception("connection timeout")
    )

    with patch("api.auth_forgot_password.get_supabase_client", return_value=mock_supabase):
        response = client.post("/forgot-password", json={"email": "user@example.com"})

    assert response.status_code == 200
    assert "detail" in response.json()


def test_forgot_password_no_supabase_client_still_200(client):
    """When Supabase is not configured (returns None), endpoint still returns 200."""
    with patch("api.auth_forgot_password.get_supabase_client", return_value=None):
        response = client.post("/forgot-password", json={"email": "user@example.com"})

    assert response.status_code == 200
    assert "detail" in response.json()


def test_forgot_password_invalid_email_returns_422(client):
    """Pydantic rejects malformed e-mails with HTTP 422."""
    with patch("api.auth_forgot_password.get_supabase_client", return_value=MagicMock()):
        response = client.post("/forgot-password", json={"email": "not-valid"})

    assert response.status_code == 422

"""GoTrue REST fallback for sign_in_with_password / sign_up."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from services.supabase_auth import SupabaseAuthError, sign_in_with_password, sign_up


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
def test_sign_in_uses_gotrue_rest_when_client_missing(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://tyzmywhvpmdfepxdtyes.supabase.co/")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    payload = {
        "user": {
            "id": "sb-1",
            "email": "user@example.com",
            "user_metadata": {"full_name": "User"},
        }
    }
    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.__exit__.return_value = False
    fake_client.post.return_value = _FakeResponse(200, payload)

    with patch("services.supabase_auth.get_supabase_client", return_value=None), patch(
        "services.supabase_auth.httpx.Client", return_value=fake_client
    ):
        user = sign_in_with_password("user@example.com", "Passw0rd!")

    assert user.id == "sb-1"
    assert user.email == "user@example.com"
    called_url = fake_client.post.call_args.args[0]
    assert called_url == (
        "https://tyzmywhvpmdfepxdtyes.supabase.co/auth/v1/token?grant_type=password"
    )
    headers = fake_client.post.call_args.kwargs["headers"]
    assert headers["apikey"] == "anon-key"
    assert headers["Authorization"] == "Bearer anon-key"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
def test_sign_in_invalid_grant_is_credentials_error(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://tyzmywhvpmdfepxdtyes.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.__exit__.return_value = False
    fake_client.post.return_value = _FakeResponse(
        400, {"error": "invalid_grant", "error_description": "Invalid login credentials"}
    )

    with patch("services.supabase_auth.get_supabase_client", return_value=None), patch(
        "services.supabase_auth.httpx.Client", return_value=fake_client
    ):
        with pytest.raises(SupabaseAuthError) as exc:
            sign_in_with_password("user@example.com", "wrong")

    assert exc.value.invalid_credentials is True
    assert exc.value.unavailable is False


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
def test_sign_up_uses_gotrue_signup(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://tyzmywhvpmdfepxdtyes.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.__exit__.return_value = False
    fake_client.post.return_value = _FakeResponse(
        200, {"id": "new-1", "email": "new@example.com", "user_metadata": {}}
    )

    with patch("services.supabase_auth.get_supabase_client", return_value=None), patch(
        "services.supabase_auth.httpx.Client", return_value=fake_client
    ):
        user = sign_up("new@example.com", "Passw0rd!", full_name="New")

    assert user.id == "new-1"
    called_url = fake_client.post.call_args.args[0]
    assert called_url.endswith("/auth/v1/signup")


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
def test_sign_in_network_error_is_unavailable(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://tyzmywhvpmdfepxdtyes.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.__exit__.return_value = False
    fake_client.post.side_effect = httpx.ConnectError("boom")

    with patch("services.supabase_auth.get_supabase_client", return_value=None), patch(
        "services.supabase_auth.httpx.Client", return_value=fake_client
    ):
        with pytest.raises(SupabaseAuthError) as exc:
            sign_in_with_password("user@example.com", "Passw0rd!")

    assert exc.value.unavailable is True

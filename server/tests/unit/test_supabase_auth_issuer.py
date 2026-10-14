"""Issuer derivation for Supabase/GoTrue JWTs."""

import jwt
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from config.supabase_client import get_supabase_auth_issuer, issuer_matches_supabase
from models.schemas import TokenType
from services.auth_service import AuthService

PROJECT_URL = "https://tyzmywhvpmdfepxdtyes.supabase.co"
EXPECTED_ISS = "https://tyzmywhvpmdfepxdtyes.supabase.co/auth/v1"


@pytest.mark.unit
@pytest.mark.auth
class TestSupabaseIssuer:
    def test_strips_trailing_slash(self):
        assert get_supabase_auth_issuer(PROJECT_URL + "/") == EXPECTED_ISS
        assert get_supabase_auth_issuer(PROJECT_URL) == EXPECTED_ISS
        assert get_supabase_auth_issuer(PROJECT_URL + "///") == EXPECTED_ISS

    def test_empty_url_returns_none(self):
        assert get_supabase_auth_issuer("") is None
        assert get_supabase_auth_issuer("   ") is None

    def test_issuer_match_tolerates_trailing_slash_on_claim(self):
        assert issuer_matches_supabase(EXPECTED_ISS, EXPECTED_ISS)
        assert issuer_matches_supabase(EXPECTED_ISS + "/", EXPECTED_ISS)
        assert not issuer_matches_supabase(
            "https://other-project.supabase.co/auth/v1", EXPECTED_ISS
        )

    def test_reads_runtime_env_with_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", PROJECT_URL + "/")
        assert get_supabase_auth_issuer() == EXPECTED_ISS


def _gotrue_token(iss: str, aud: str = "authenticated") -> str:
    payload = {
        "sub": "user-1",
        "email": "user@example.com",
        "iss": iss,
        "aud": aud,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, "not-the-local-secret", algorithm="HS256")


@pytest.mark.unit
@pytest.mark.auth
class TestVerifyTokenIssuer:
    def test_accepts_project_issuer_derived_from_url_with_slash(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", PROJECT_URL + "/")
        token = _gotrue_token(EXPECTED_ISS)
        supabase_user = MagicMock()
        supabase_user.id = "user-1"
        supabase_user.email = "user@example.com"
        response = MagicMock()
        response.user = supabase_user
        client = MagicMock()
        client.auth.get_user.return_value = response

        service = AuthService()
        with patch("services.auth_service.get_supabase_auth_issuer", return_value=EXPECTED_ISS), patch(
            "services.auth_service.get_supabase_client", return_value=client
        ):
            data = service.verify_token(token, TokenType.ACCESS)

        assert data.user_id == "user-1"
        assert data.email == "user@example.com"
        client.auth.get_user.assert_called_once_with(token)

    def test_rejects_other_project_issuer(self):
        token = _gotrue_token("https://other-project.supabase.co/auth/v1")
        service = AuthService()
        with patch("services.auth_service.get_supabase_auth_issuer", return_value=EXPECTED_ISS), patch(
            "services.auth_service.get_supabase_client", return_value=MagicMock()
        ):
            with pytest.raises(Exception) as exc:
                service.verify_token(token, TokenType.ACCESS)
        assert exc.value.status_code == 401
        assert "Token Supabase de outro projeto" in str(exc.value.detail)

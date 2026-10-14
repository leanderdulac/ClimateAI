"""Login/register against Supabase Auth, local fallback, and 503 on DB outage."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from models.schemas import LoginRequest, UserCreate, UserRole
from models.sqlalchemy_models import User as UserModel
from services.auth_service import (
    AUTH_UNAVAILABLE_DETAIL,
    DB_UNAVAILABLE_DETAIL,
    AuthService,
)
from services.supabase_auth import SupabaseAuthError, SupabaseAuthUser


def _login() -> LoginRequest:
    return LoginRequest(email="user@example.com", password="Passw0rd!")


def _scalar_result(value):
    result = MagicMock()
    result.scalars.return_value.first.return_value = value
    return result


def _db_mock(existing=None):
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(existing))
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    async def _refresh(user):
        if getattr(user, "created_at", None) is None:
            user.created_at = datetime.utcnow()
        if getattr(user, "updated_at", None) is None:
            user.updated_at = datetime.utcnow()

    db.refresh = _refresh
    db.add = MagicMock()
    return db


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
@pytest.mark.asyncio
async def test_login_authenticates_supabase_upserts_user_and_issues_backend_jwt():
    service = AuthService()
    db = _db_mock(existing=None)
    sb_user = SupabaseAuthUser(
        id="11111111-1111-1111-1111-111111111111",
        email="user@example.com",
        full_name="Supabase User",
    )

    with patch("services.auth_service.is_supabase_configured", return_value=True), patch(
        "services.auth_service.supabase_sign_in", return_value=sb_user
    ) as sign_in:
        token = await service.login(db, _login())

    sign_in.assert_called_once_with("user@example.com", "Passw0rd!")
    assert token.access_token
    assert token.refresh_token
    assert token.token_type == "bearer"
    assert token.user.email == "user@example.com"
    assert token.user.id == sb_user.id
    assert token.user.full_name == "Supabase User"
    db.add.assert_called_once()


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
@pytest.mark.asyncio
async def test_login_links_existing_local_user_by_email():
    service = AuthService()
    existing = UserModel(
        id="local-id",
        email="user@example.com",
        full_name="Local User",
        hashed_password="hash",
        role="user",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db = _db_mock()
    db.execute = AsyncMock(
        side_effect=[_scalar_result(None), _scalar_result(existing)]
    )
    sb_user = SupabaseAuthUser(id="sb-id", email="user@example.com", full_name="Local User")

    with patch("services.auth_service.is_supabase_configured", return_value=True), patch(
        "services.auth_service.supabase_sign_in", return_value=sb_user
    ):
        token = await service.login(db, _login())

    assert token.user.id == "local-id"
    assert token.user.email == "user@example.com"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
@pytest.mark.asyncio
async def test_login_invalid_supabase_credentials_is_401():
    service = AuthService()
    db = _db_mock()

    with patch("services.auth_service.is_supabase_configured", return_value=True), patch(
        "services.auth_service.supabase_sign_in",
        side_effect=SupabaseAuthError("bad", invalid_credentials=True),
    ):
        with pytest.raises(HTTPException) as exc:
            await service.login(db, _login())

    assert exc.value.status_code == 401
    assert exc.value.detail == "Email ou senha incorretos"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
@pytest.mark.asyncio
async def test_login_supabase_outage_is_503():
    service = AuthService()
    db = _db_mock()

    with patch("services.auth_service.is_supabase_configured", return_value=True), patch(
        "services.auth_service.supabase_sign_in",
        side_effect=SupabaseAuthError("down", unavailable=True),
    ):
        with pytest.raises(HTTPException) as exc:
            await service.login(db, _login())

    assert exc.value.status_code == 503
    assert exc.value.detail == AUTH_UNAVAILABLE_DETAIL


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.asyncio
async def test_login_local_fallback_when_supabase_env_absent():
    service = AuthService()
    hashed = service.get_password_hash("Passw0rd!")
    existing = UserModel(
        id="local-1",
        email="user@example.com",
        full_name="Local Dev",
        hashed_password=hashed,
        role="user",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db = _db_mock(existing=existing)

    with patch("services.auth_service.is_supabase_configured", return_value=False):
        token = await service.login(db, _login())

    assert token.user.id == "local-1"
    assert token.access_token


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.uses_supabase_auth
@pytest.mark.asyncio
async def test_register_creates_supabase_auth_user():
    service = AuthService()
    db = _db_mock(existing=None)
    sb_user = SupabaseAuthUser(
        id="new-sb-id", email="new@example.com", full_name="New User"
    )
    payload = UserCreate(
        email="new@example.com",
        full_name="New User",
        password="Passw0rd!",
        role=UserRole.USER,
        is_active=True,
    )

    with patch("services.auth_service.is_supabase_configured", return_value=True), patch(
        "services.auth_service.supabase_sign_up", return_value=sb_user
    ) as sign_up:
        user = await service.create_user(db, payload)

    sign_up.assert_called_once()
    assert user.id == "new-sb-id"
    assert user.email == "new@example.com"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.asyncio
async def test_login_returns_503_when_database_unavailable():
    service = AuthService()
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=OperationalError("SELECT 1", {}, Exception("connection refused"))
    )

    with patch("services.auth_service.is_supabase_configured", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await service.login(db, _login())

    assert exc.value.status_code == 503
    assert exc.value.detail == DB_UNAVAILABLE_DETAIL


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.asyncio
async def test_login_returns_503_when_database_disabled_in_production(monkeypatch):
    service = AuthService()
    db = _db_mock()
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_ENABLED", "false")

    with patch("services.auth_service.is_supabase_configured", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await service.login(db, _login())

    assert exc.value.status_code == 503
    assert exc.value.detail == DB_UNAVAILABLE_DETAIL


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.asyncio
async def test_login_wrong_password_stays_401_when_db_is_up():
    service = AuthService()
    hashed = service.get_password_hash("other-pass1")
    existing = UserModel(
        id="local-1",
        email="user@example.com",
        full_name="Local Dev",
        hashed_password=hashed,
        role="user",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db = _db_mock(existing=existing)

    with patch("services.auth_service.is_supabase_configured", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await service.login(db, _login())

    assert exc.value.status_code == 401

import pytest

from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate
from app.services.session import DuplicateEmailError, InvalidCredentialsError, SessionService


@pytest.mark.asyncio
async def test_register_normalizes_email_and_hashes_password(db_session, settings):
    svc = SessionService(db_session, settings)
    out = await svc.register(
        UserCreate(email="USER@Example.COM ", password="correct horse battery staple", name="User")
    )
    assert out.user.email == "user@example.com"
    user = await svc.current_user(out.access_token)
    assert user.email == "user@example.com"


@pytest.mark.asyncio
async def test_duplicate_register_raises(db_session, settings):
    svc = SessionService(db_session, settings)
    await svc.register(UserCreate(email="user@example.com", password="secret123", name="u"))
    with pytest.raises(DuplicateEmailError):
        await svc.register(UserCreate(email="user@example.com", password="secret123", name="u"))


@pytest.mark.asyncio
async def test_login_and_wrong_password(db_session, settings):
    svc = SessionService(db_session, settings)
    await svc.register(UserCreate(email="user@example.com", password="secret123", name="u"))
    ok = await svc.login(LoginRequest(email="user@example.com", password="secret123"))
    assert ok.token_type == "bearer"
    assert ok.expires_in == 1800
    with pytest.raises(InvalidCredentialsError):
        await svc.login(LoginRequest(email="user@example.com", password="bad"))

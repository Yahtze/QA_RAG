from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserOut


class DuplicateEmailError(Exception): ...


class InvalidCredentialsError(Exception): ...


class UnauthorizedError(Exception): ...


class SessionService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings

    async def register(self, data: UserCreate) -> TokenResponse:
        email = data.email.lower().strip()
        user = User(
            email=email, hashed_password=hash_password(data.password), name=data.name
        )
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise DuplicateEmailError from exc
        await self.session.refresh(user)
        token, expires = create_access_token(user.id, self.settings)
        return TokenResponse(
            access_token=token,
            expires_in=expires,
            user=UserOut.model_validate(user, from_attributes=True),
        )

    async def login(self, data: LoginRequest) -> TokenResponse:
        email = data.email.lower().strip()
        user = (
            await self.session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError
        token, expires = create_access_token(user.id, self.settings)
        return TokenResponse(
            access_token=token,
            expires_in=expires,
            user=UserOut.model_validate(user, from_attributes=True),
        )

    async def current_user(self, token: str) -> UserOut:
        try:
            user_id: UUID = decode_access_token(token, self.settings)
        except Exception as exc:
            raise UnauthorizedError from exc
        user = (
            await self.session.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise UnauthorizedError
        return UserOut.model_validate(user, from_attributes=True)

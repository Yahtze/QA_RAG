from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return _password_hash.verify(password, hashed_password)


def create_access_token(
    subject: UUID, settings: Settings, now: datetime | None = None
) -> tuple[str, int]:
    issued = now or datetime.now(UTC)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    payload = {"sub": str(subject), "exp": issued + timedelta(seconds=expires_in)}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256"), expires_in


def decode_access_token(token: str, settings: Settings) -> UUID:
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    return UUID(payload["sub"])

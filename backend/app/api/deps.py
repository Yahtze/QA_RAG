from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models import User
from app.services.session import SessionService, UnauthorizedError

bearer = HTTPBearer(auto_error=False)


def get_settings_dep() -> Settings:
    return get_settings()


async def get_current_user(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Missing token")
    service = SessionService(session, settings)
    try:
        user_out = await service.current_user(creds.credentials)
    except UnauthorizedError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await session.get(User, user_out.id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

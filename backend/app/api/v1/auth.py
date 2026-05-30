from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_settings_dep
from app.core.config import Settings
from app.db.session import get_db_session
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserOut
from app.services.session import (
    DuplicateEmailError,
    InvalidCredentialsError,
    SessionService,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
):
    try:
        return await SessionService(session, settings).register(data)
    except DuplicateEmailError:
        raise HTTPException(status_code=409, detail="Email already exists")


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
):
    try:
        return await SessionService(session, settings).login(data)
    except InvalidCredentialsError:
        raise HTTPException(status_code=400, detail="Invalid credentials")


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut.model_validate(user, from_attributes=True)

from typing import Literal

from pydantic import BaseModel, EmailStr

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut

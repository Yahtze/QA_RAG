from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class UserOut(BaseModel):
    id: UUID
    email: str
    name: str | None
    created_at: datetime
    updated_at: datetime

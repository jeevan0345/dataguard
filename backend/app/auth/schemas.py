"""
DataGuard Authentication Pydantic Schemas
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=6, max_length=72)
    role: str = Field(default="DATA_ENGINEER", pattern="^(ADMIN|DATA_ENGINEER|VIEWER)$")


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

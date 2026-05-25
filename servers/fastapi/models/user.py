"""Pydantic models para gestión de usuarios"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Modelo para crear un nuevo usuario"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(default="user", pattern="^(admin|user)$")


class UserUpdate(BaseModel):
    """Modelo para actualizar un usuario"""
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = Field(None, pattern="^(admin|user)$")
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Modelo de respuesta de usuario (sin password)"""
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

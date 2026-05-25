from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """Roles de usuario en el sistema"""
    ADMIN = "admin"
    USER = "user"


class UserModel(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    hashed_password: str = Field(max_length=255)
    role: str = Field(default=UserRole.USER.value, max_length=20)  # admin o user
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

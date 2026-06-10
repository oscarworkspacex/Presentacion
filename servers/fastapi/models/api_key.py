"""Pydantic models para gestión de API keys"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ApiKeyCreate(BaseModel):
    """Modelo para crear una nueva API key"""
    name: str = Field(..., min_length=3, max_length=255, description="Nombre descriptivo de la API key")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración opcional")


class ApiKeyResponse(BaseModel):
    """Modelo de respuesta de API key"""
    id: str
    key: str  # Solo se muestra en la creación, luego se oculta
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    usage_count: int
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyListResponse(BaseModel):
    """Modelo de respuesta para listar API keys (sin mostrar la key completa)"""
    id: str
    key_preview: str  # Solo los primeros y últimos caracteres
    name: str
    is_active: bool
    created_at: datetime
    usage_count: int
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

"""Endpoints para gestión de API keys (solo admin)"""

import logging
import secrets
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.sql.api_key import ApiKeyModel
from models.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyListResponse
from services.database import get_async_session

logger = logging.getLogger(__name__)

API_KEYS_ROUTER = APIRouter(prefix="/api-keys", tags=["API Key Management"])


def generate_api_key() -> str:
    """Genera una API key segura"""
    return f"sk_{secrets.token_urlsafe(32)}"


def mask_api_key(key: str) -> str:
    """Enmascara una API key mostrando solo primeros y últimos caracteres"""
    if len(key) <= 12:
        return key[:4] + "..." + key[-4:]
    return key[:8] + "..." + key[-8:]


@API_KEYS_ROUTER.get("", response_model=List[ApiKeyListResponse])
async def list_api_keys(
    sql_session: AsyncSession = Depends(get_async_session),
):
    """List all API keys (admin only - verificado por middleware)"""
    try:
        result = await sql_session.scalars(
            select(ApiKeyModel).order_by(ApiKeyModel.created_at.desc())
        )
        api_keys = list(result)
        
        # Convertir a respuesta con key enmascarada
        response = []
        for api_key in api_keys:
            response.append(ApiKeyListResponse(
                id=api_key.id,
                key_preview=mask_api_key(api_key.key),
                name=api_key.name,
                is_active=api_key.is_active,
                created_at=api_key.created_at,
                usage_count=api_key.usage_count,
                last_used_at=api_key.last_used_at,
                expires_at=api_key.expires_at,
            ))
        
        return response
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving API keys"
        )


@API_KEYS_ROUTER.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Create a new API key (admin only)"""
    try:
        # Generar una API key única
        key = generate_api_key()
        
        # Verificar que no exista (extremadamente improbable)
        existing = await sql_session.scalar(
            select(ApiKeyModel).where(ApiKeyModel.key == key)
        )
        
        if existing:
            # Si por alguna razón existe, generar otra
            key = generate_api_key()
        
        # Crear nueva API key
        new_api_key = ApiKeyModel(
            key=key,
            name=api_key_data.name,
            is_active=True,
            expires_at=api_key_data.expires_at,
        )
        
        sql_session.add(new_api_key)
        await sql_session.commit()
        await sql_session.refresh(new_api_key)
        
        logger.info(f"API key created: {new_api_key.name} ({new_api_key.id})")
        
        # Retornar la key completa solo en la creación
        return new_api_key
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating API key"
        )


@API_KEYS_ROUTER.get("/{api_key_id}", response_model=ApiKeyListResponse)
async def get_api_key(
    api_key_id: str,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Get details of an API key (admin only, key is masked)"""
    try:
        api_key = await sql_session.get(ApiKeyModel, api_key_id)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        return ApiKeyListResponse(
            id=api_key.id,
            key_preview=mask_api_key(api_key.key),
            name=api_key.name,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            usage_count=api_key.usage_count,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving API key"
        )


@API_KEYS_ROUTER.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: str,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Delete an API key (admin only)"""
    try:
        api_key = await sql_session.get(ApiKeyModel, api_key_id)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        await sql_session.delete(api_key)
        await sql_session.commit()
        
        logger.info(f"API key deleted: {api_key.name} ({api_key.id})")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting API key"
        )


@API_KEYS_ROUTER.patch("/{api_key_id}/toggle", response_model=ApiKeyListResponse)
async def toggle_api_key(
    api_key_id: str,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Toggle active status of an API key (admin only)"""
    try:
        api_key = await sql_session.get(ApiKeyModel, api_key_id)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        api_key.is_active = not api_key.is_active
        api_key.updated_at = datetime.utcnow()
        
        await sql_session.commit()
        await sql_session.refresh(api_key)
        
        logger.info(f"API key toggled: {api_key.name} - active: {api_key.is_active}")
        
        return ApiKeyListResponse(
            id=api_key.id,
            key_preview=mask_api_key(api_key.key),
            name=api_key.name,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            usage_count=api_key.usage_count,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling API key: {e}")
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error toggling API key"
        )

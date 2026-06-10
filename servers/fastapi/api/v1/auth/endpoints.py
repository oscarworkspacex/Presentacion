from fastapi import APIRouter, HTTPException, status, Response, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime

from models.auth import LoginRequest, TokenResponse
from models.sql.user import UserModel
from models.sql.api_key import ApiKeyModel
from core.auth import verify_password, create_access_token
from services.database import get_async_session
from datetime import timedelta

AUTH_ROUTER = APIRouter(prefix="/auth", tags=["Authentication"])


@AUTH_ROUTER.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    response: Response,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Endpoint de login - Verifica contra la base de datos y devuelve JWT con role
    """
    # Buscar usuario en la base de datos
    result = await sql_session.scalar(
        select(UserModel).where(UserModel.username == credentials.username)
    )
    
    user = result
    
    # Verificar si el usuario existe
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    
    # Verificar si el usuario está activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )
    
    # Verificar contraseña
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    
    # Actualizar last_login
    user.last_login = datetime.utcnow()
    sql_session.add(user)
    await sql_session.commit()
    
    # Crear token JWT con username y role
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(hours=24)
    )
    
    # También establecer cookie para el navegador
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=86400,  # 24 horas
        samesite="lax"
    )
    
    return TokenResponse(
        access_token=access_token,
        username=user.username,
        role=user.role,  # Incluir role en la respuesta
    )


@AUTH_ROUTER.post("/logout")
async def logout(response: Response):
    """
    Endpoint de logout - Elimina la cookie del token
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logout exitoso"}


@AUTH_ROUTER.get("/me")
async def get_current_user(request: Request):
    """
    Obtener información del usuario actual (requiere autenticación)
    El middleware ya verificó el token y lo agregó a request.state
    """
    # El middleware añade user_info a request.state si el token es válido
    user_info = getattr(request.state, "user_info", None)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    return {
        "username": user_info.get("username"),
        "role": user_info.get("role", "user"),
        "authenticated": True,
    }


@AUTH_ROUTER.get("/verify-api-key")
async def verify_api_key(
    api_key: str,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Verificar si una API key es válida
    Este endpoint no requiere autenticación previa
    """
    try:
        # Buscar la API key en la base de datos
        result = await sql_session.scalar(
            select(ApiKeyModel).where(ApiKeyModel.key == api_key)
        )
        
        api_key_model = result
        
        # Verificar si existe
        if not api_key_model:
            return {
                "valid": False,
                "reason": "API key not found"
            }
        
        # Verificar si está activa
        if not api_key_model.is_active:
            return {
                "valid": False,
                "reason": "API key is inactive"
            }
        
        # Verificar si ha expirado
        if api_key_model.expires_at and api_key_model.expires_at < datetime.utcnow():
            return {
                "valid": False,
                "reason": "API key has expired"
            }
        
        # API key válida
        return {
            "valid": True,
            "name": api_key_model.name,
            "id": api_key_model.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying API key: {str(e)}"
        )

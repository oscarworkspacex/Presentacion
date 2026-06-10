import base64
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from fastapi import status
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from utils.get_env import get_can_change_keys_env
from utils.user_config import update_env_with_user_config
from core.auth import verify_token
from models.sql.api_key import ApiKeyModel
from services.database import async_session_maker


class UserConfigEnvUpdateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if get_can_change_keys_env() != "false":
            update_env_with_user_config()
        return await call_next(request)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware para autenticación JWT y API Keys
    Verifica token JWT en cookies o header Authorization, o API key en query params/header
    Guarda user_info en request.state
    """
    
    # Rutas que NO requieren autenticación
    EXCLUDED_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/auth/login",  # Login debe ser público
        "/api/v1/auth/logout",  # Logout debe ser público
        "/api/v1/auth/verify-api-key",  # Verificación de API key debe ser público
    ]
    
    async def _verify_api_key(self, api_key: str) -> dict | None:
        """Verifica una API key y retorna información si es válida"""
        try:
            async with async_session_maker() as session:
                result = await session.scalar(
                    select(ApiKeyModel).where(ApiKeyModel.key == api_key)
                )
                
                api_key_model = result
                
                if not api_key_model:
                    return None
                
                # Verificar si está activa
                if not api_key_model.is_active:
                    return None
                
                # Verificar si ha expirado
                if api_key_model.expires_at and api_key_model.expires_at < datetime.utcnow():
                    return None
                
                # Actualizar usage_count y last_used_at
                api_key_model.usage_count += 1
                api_key_model.last_used_at = datetime.utcnow()
                session.add(api_key_model)
                await session.commit()
                
                return {
                    "api_key_id": api_key_model.id,
                    "api_key_name": api_key_model.name,
                }
        except Exception:
            return None
    
    async def dispatch(self, request: Request, call_next):
        # Verificar si la ruta está excluida
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # PASO 1: Intentar autenticación JWT
        # Intentar obtener token de la cookie
        token = request.cookies.get("access_token")
        
        # Si no hay cookie, intentar obtener del header Authorization
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        else:
            # Si viene de cookie, quitar el prefijo "Bearer "
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
        
        # Si hay token JWT, verificarlo
        if token:
            user_data = verify_token(token)
            
            if user_data:
                # JWT válido - autenticación tradicional
                request.state.user = user_data.get("username")
                request.state.user_info = user_data  # Incluye username y role
                request.state.user_role = user_data.get("role", "user")
                request.state.auth_type = "jwt"
                
                response = await call_next(request)
                return response
        
        # PASO 2: Si no hay JWT válido, intentar API key
        # Buscar API key en query params
        api_key = request.query_params.get("api_key")
        
        # Si no está en query params, buscar en header X-API-Key
        if not api_key:
            api_key = request.headers.get("X-API-Key")
        
        # Si hay API key, verificarla
        if api_key:
            api_key_data = await self._verify_api_key(api_key)
            
            if api_key_data:
                # API key válida - autenticación con API key
                request.state.auth_type = "api_key"
                request.state.user_role = "api_user"  # Rol especial para API keys
                request.state.api_key_id = api_key_data["api_key_id"]
                request.state.api_key_name = api_key_data["api_key_name"]
                request.state.user_info = {
                    "username": f"api_key_{api_key_data['api_key_id']}",
                    "role": "api_user",
                    "auth_type": "api_key"
                }
                
                response = await call_next(request)
                return response
        
        # PASO 3: No hay autenticación válida
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "No autenticado. Por favor inicia sesión o proporciona una API key válida."}
        )


class RoleRequiredMiddleware(BaseHTTPMiddleware):
    """
    Middleware para verificar que el usuario tenga el rol adecuado en rutas protegidas
    - Admin: acceso completo
    - User: lectura y algunas operaciones
    - API User: solo crear presentaciones (acceso limitado)
    """
    
    # Rutas que requieren rol ADMIN (gestión del sistema)
    ADMIN_ONLY_PATHS = [
        "/api/v1/admin",  # Gestión de usuarios y API keys
    ]
    
    # Rutas de escritura que requieren ADMIN (usuarios normales no pueden escribir)
    ADMIN_WRITE_ENDPOINTS = [
        "/api/v1/ppt/presentation",
        "/api/v1/ppt/add-questions-slide",
        "/api/v1/ppt/slides",
        "/api/v1/ppt/images",
    ]
    
    # Rutas permitidas para API users (acceso limitado)
    API_USER_ALLOWED_PATHS = [
        "/api/v1/ppt/presentation/create",
        "/api/v1/ppt/presentation/prepare",
        "/api/v1/ppt/presentation/generate",
        "/api/v1/ppt/presentation/create-from-theme",
    ]
    
    # Rutas GET permitidas para API users (lectura)
    API_USER_READ_PREFIXES = [
        "/api/v1/ppt/",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Obtener role y auth_type del request.state (ya verificado por AuthenticationMiddleware)
        user_role = getattr(request.state, "user_role", "user")
        auth_type = getattr(request.state, "auth_type", "jwt")
        
        # Verificar si la ruta requiere admin
        is_admin_path = any(request.url.path.startswith(path) for path in self.ADMIN_ONLY_PATHS)
        
        # SI ES API USER - Aplicar restricciones especiales
        if auth_type == "api_key" and user_role == "api_user":
            # Bloquear acceso a rutas de admin
            if is_admin_path:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "API keys no tienen acceso a rutas administrativas."}
                )
            
            # Permitir lectura (GET) en rutas de presentaciones
            if request.method == "GET":
                if any(request.url.path.startswith(prefix) for prefix in self.API_USER_READ_PREFIXES):
                    response = await call_next(request)
                    return response
            
            # Permitir solo endpoints específicos de escritura
            if request.method in ["POST", "PUT", "PATCH"]:
                if any(request.url.path.startswith(path) for path in self.API_USER_ALLOWED_PATHS):
                    response = await call_next(request)
                    return response
            
            # Bloquear DELETE y otras operaciones
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "API keys solo pueden crear y leer presentaciones."}
            )
        
        # USUARIOS NORMALES (JWT) - Lógica original
        # Verificar si es una operación de escritura que requiere admin
        is_write_operation = False
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            is_write_operation = any(
                request.url.path.startswith(path) for path in self.ADMIN_WRITE_ENDPOINTS
            )
        
        # Si requiere admin y el usuario no es admin, denegar
        if (is_admin_path or is_write_operation) and user_role != "admin":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Acceso denegado. Se requiere rol de administrador."}
            )
        
        # Continuar con la petición
        response = await call_next(request)
        return response

"""
Script para crear una API key de prueba en la base de datos.
Este script debe ejecutarse después de que el servidor FastAPI haya iniciado
y creado las tablas de la base de datos.

Uso:
    python create_test_api_key.py
"""

import asyncio
import secrets
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

# Importar el modelo
import sys
import os

# Agregar el directorio del servidor al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "servers", "fastapi"))

from models.sql.api_key import ApiKeyModel
from utils.db_utils import get_database_url_and_connect_args


async def create_test_api_key():
    """Crea una API key de prueba en la base de datos"""
    
    # Configurar conexión a la base de datos
    database_url, connect_args = get_database_url_and_connect_args()
    engine = create_async_engine(database_url, connect_args=connect_args)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    # Generar API key
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    # Crear el registro
    async with async_session_maker() as session:
        new_api_key = ApiKeyModel(
            key=api_key,
            name="Test API Key - Demo",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=30),  # Expira en 30 días
        )
        
        session.add(new_api_key)
        await session.commit()
        await session.refresh(new_api_key)
        
        print("=" * 80)
        print("✅ API Key de prueba creada exitosamente!")
        print("=" * 80)
        print(f"\nID: {new_api_key.id}")
        print(f"Nombre: {new_api_key.name}")
        print(f"API Key: {api_key}")
        print(f"Activa: {new_api_key.is_active}")
        print(f"Creada: {new_api_key.created_at}")
        print(f"Expira: {new_api_key.expires_at}")
        print("\n" + "=" * 80)
        print("🔗 URL de prueba:")
        print("=" * 80)
        print(f"\nhttp://localhost:5000/?api_key={api_key}")
        print("\n" + "=" * 80)
        print("📝 Pasos para probar:")
        print("=" * 80)
        print("1. Copia la URL de prueba de arriba")
        print("2. Pégala en tu navegador")
        print("3. Deberías ser redirigido al dashboard automáticamente")
        print("4. Verifica que NO puedes acceder a Settings ni Admin")
        print("5. Intenta crear una nueva presentación")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(create_test_api_key())

"""Script para crear el primer usuario administrador"""

import asyncio
import sys
sys.path.insert(0, '/app/servers/fastapi')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
import os

from models.sql.user import UserModel, UserRole
from core.auth import hash_password


async def create_admin_user():
    """Crear usuario admin inicial"""
    
    # Obtener DATABASE_URL del entorno
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL no configurada")
        return
    
    # Crear engine y session
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Verificar si ya existe un admin
        result = await session.scalar(
            select(UserModel).where(UserModel.role == UserRole.ADMIN.value)
        )
        
        if result:
            print(f"✅ Ya existe un usuario admin: {result.username}")
            return
        
        # Obtener credenciales del .env
        username = os.getenv("AUTH_USERNAME", "admin")
        password = os.getenv("AUTH_PASSWORD", "admin")
        
        # Crear usuario admin
        admin_user = UserModel(
            username=username,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        
        session.add(admin_user)
        await session.commit()
        
        print(f"✅ Usuario admin creado exitosamente:")
        print(f"   Usuario: {username}")
        print(f"   Rol: admin")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_admin_user())

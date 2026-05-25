"""Endpoints para gestión de usuarios (solo admin)"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.sql.user import UserModel, UserRole
from models.user import UserCreate, UserUpdate, UserResponse
from services.database import get_async_session
from core.auth import hash_password

logger = logging.getLogger(__name__)

USERS_ROUTER = APIRouter(prefix="/users", tags=["User Management"])


@USERS_ROUTER.get("", response_model=List[UserResponse])
async def list_users(
    sql_session: AsyncSession = Depends(get_async_session),
):
    """List all users (admin only - verificado por middleware)"""
    try:
        result = await sql_session.scalars(
            select(UserModel).order_by(UserModel.created_at.desc())
        )
        users = list(result)
        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )


@USERS_ROUTER.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Create a new user (admin only)"""
    try:
        # Check if username already exists
        existing = await sql_session.scalar(
            select(UserModel).where(UserModel.username == user_data.username)
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_data.username}' already exists"
            )
        
        # Create new user
        new_user = UserModel(
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            is_active=True,
        )
        
        sql_session.add(new_user)
        await sql_session.commit()
        await sql_session.refresh(new_user)
        
        logger.info(f"User created: {new_user.username} ({new_user.role})")
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@USERS_ROUTER.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Update a user (admin only)"""
    try:
        user = await sql_session.get(UserModel, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        if user_data.password is not None:
            user.hashed_password = hash_password(user_data.password)
        
        if user_data.role is not None:
            user.role = user_data.role
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        await sql_session.commit()
        await sql_session.refresh(user)
        
        logger.info(f"User updated: {user.username}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )


@USERS_ROUTER.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Delete a user (admin only)"""
    try:
        user = await sql_session.get(UserModel, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent deleting the only admin
        if user.role == UserRole.ADMIN.value:
            admins_count = await sql_session.scalar(
                select(UserModel).where(UserModel.role == UserRole.ADMIN.value)
            )
            if len(list(admins_count)) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the only admin user"
                )
        
        await sql_session.delete(user)
        await sql_session.commit()
        
        logger.info(f"User deleted: {user.username}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting user"
        )

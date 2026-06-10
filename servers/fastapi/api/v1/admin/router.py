"""Router para endpoints de administración"""

from fastapi import APIRouter
from api.v1.admin.endpoints.users import USERS_ROUTER
from api.v1.admin.endpoints.api_keys import API_KEYS_ROUTER

API_V1_ADMIN_ROUTER = APIRouter(prefix="/api/v1/admin")
API_V1_ADMIN_ROUTER.include_router(USERS_ROUTER)
API_V1_ADMIN_ROUTER.include_router(API_KEYS_ROUTER)

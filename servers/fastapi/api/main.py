from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from api.lifespan import app_lifespan
from api.middlewares import UserConfigEnvUpdateMiddleware, AuthenticationMiddleware, RoleRequiredMiddleware
from api.v1.ppt.router import API_V1_PPT_ROUTER
from api.v1.webhook.router import API_V1_WEBHOOK_ROUTER
from api.v1.mock.router import API_V1_MOCK_ROUTER
from api.v1.auth.router import API_V1_AUTH_ROUTER
from api.v1.admin.router import API_V1_ADMIN_ROUTER
from utils.get_env import get_app_data_directory_env


app = FastAPI(lifespan=app_lifespan)


# Routers
app.include_router(API_V1_AUTH_ROUTER)  # Auth debe ir primero (antes de protección)
app.include_router(API_V1_ADMIN_ROUTER)  # Admin endpoints
app.include_router(API_V1_PPT_ROUTER)
app.include_router(API_V1_WEBHOOK_ROUTER)
app.include_router(API_V1_MOCK_ROUTER)

# Middlewares
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Role verification middleware (DEBE IR PRIMERO - antes de auth)
app.add_middleware(RoleRequiredMiddleware)

# Authentication middleware (segundo)
app.add_middleware(AuthenticationMiddleware)

app.add_middleware(UserConfigEnvUpdateMiddleware)

# Static assets for local development (production uses nginx)
_fastapi_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_static_dir = os.path.join(_fastapi_root, "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

_app_data_dir = get_app_data_directory_env()
if _app_data_dir and os.path.isdir(_app_data_dir):
    app.mount("/app_data", StaticFiles(directory=_app_data_dir), name="app_data")

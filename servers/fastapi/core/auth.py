import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
import secrets
import bcrypt

# Configuración de seguridad (usando bcrypt directamente)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key para JWT (debe estar en .env en producción)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 horas por defecto


def hash_password(password: str) -> str:
    """Hash a password using bcrypt (max 72 bytes)"""
    # Bcrypt limita a 72 bytes
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (max 72 bytes for bcrypt)"""
    try:
        # Bcrypt limita a 72 bytes
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False


def get_auth_credentials() -> tuple[str, str]:
    """Get authentication credentials from environment"""
    username = os.getenv("AUTH_USERNAME", "admin")
    password = os.getenv("AUTH_PASSWORD", "admin")
    return username, password


def verify_user_credentials(username: str, password: str) -> bool:
    """Verify if username and password are correct"""
    expected_username, expected_password = get_auth_credentials()
    
    if username != expected_username:
        return False
    
    # Para passwords en plain text en .env, comparamos directamente
    # En producción, deberías almacenar hashes
    return password == expected_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with user data including role"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token, returning username and role"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "user")  # Default to 'user' if not present
        
        if username is None:
            return None
        
        return {"username": username, "role": role}
    
    except JWTError:
        return None

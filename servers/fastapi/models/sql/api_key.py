from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class ApiKeyModel(SQLModel, table=True):
    __tablename__ = "api_keys"
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36
    )
    key: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    usage_count: int = Field(default=0)
    last_used_at: Optional[datetime] = None

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class ProviderKey(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    provider_name: str = Field(unique=True, index=True)
    encrypted_api_key: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # TODO: Add user_id when auth is implemented

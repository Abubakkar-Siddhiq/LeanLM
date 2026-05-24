from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint


class ProviderKey(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "provider_name", name="uq_user_provider"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    provider_name: str = Field(index=True)
    encrypted_api_key: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

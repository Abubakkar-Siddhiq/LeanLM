from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from pgvector.sqlalchemy import Vector


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    supabase_user_id: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None)
    plan: str = Field(default="free")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversations: List["Conversation"] = Relationship(back_populates="user")


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    summary: Optional[str] = Field(default=None)
    message_count: int = Field(default=0)
    last_summarized_at_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role: str
    content: str
    embedding: list[float] = Field(sa_column=Column(Vector(384)))

    conversation_id: Optional[UUID] = Field(foreign_key="conversation.id")

    conversation: Optional[Conversation] = Relationship(back_populates="messages")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
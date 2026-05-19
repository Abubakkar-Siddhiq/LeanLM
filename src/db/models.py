from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from pgvector.sqlalchemy import Vector


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    summary: Optional[str] = Field(default=None)
    message_count: int = Field(default=0)
    last_summarized_at_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    messages: List["Message"] = Relationship(
        back_populates="conversation"
    )


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role: str
    content: str
    embedding: list[float] = Field(sa_column=Column(Vector(384)))

    conversation_id: Optional[UUID] = Field(
        foreign_key="conversation.id"
    )

    conversation: Optional[Conversation] = Relationship(
        back_populates="messages"
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
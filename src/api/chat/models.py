from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    messages: List["Message"] = Relationship(
        back_populates="conversation"
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role: str
    content: str

    conversation_id: Optional[UUID] = Field(
        foreign_key="conversation.id"
    )

    conversation: Optional[Conversation] = Relationship(
        back_populates="messages"
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
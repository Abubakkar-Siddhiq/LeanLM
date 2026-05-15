from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    messages: List["Message"] = Relationship(
        back_populates="conversation"
    )


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role: str
    content: str

    conversation_id: UUID = Field(
        foreign_key="conversation.id"
    )

    conversation: Optional[Conversation] = Relationship(
        back_populates="messages"
    )
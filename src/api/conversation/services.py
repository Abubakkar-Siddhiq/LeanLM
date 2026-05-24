from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from db.models import Conversation, Message


class ConversationService:
    def get_conversations(
        self, session: Session, user_id: UUID
    ) -> list[Conversation]:
        conversations = session.exec(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        ).all()
        return list(conversations)

    def get_conversation_messages(
        self, session: Session, conversation_id: UUID, user_id: UUID
    ) -> list[Message]:
        conversation = session.get(Conversation, conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        ).all()
        return list(messages)

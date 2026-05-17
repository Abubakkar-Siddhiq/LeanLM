from uuid import UUID

from sqlmodel import Session, select

from db.models import Conversation, Message


class ConversationService:
    def get_conversations(self, session: Session):
        conversations = session.exec(
            select(Conversation)
            .order_by(Conversation.created_at.desc())
        ).all()

        return conversations

    def get_conversation_messages(
        self,
        conversation_id: UUID,
        session: Session
    ):
        conversation = session.get(
            Conversation,
            conversation_id
        )

        if not conversation:
            return None

        messages = session.exec(
            select(Message)
            .where(
                Message.conversation_id == conversation_id
            )
            .order_by(Message.created_at)
        ).all()

        return {
            "conversation_id": conversation.id,
            "created_at": conversation.created_at,
            "messages": messages
        }

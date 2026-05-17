from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.conversation.services import ConversationService
from db.session import get_session


router = APIRouter()
conversation_service = ConversationService()


@router.get("/conversations")
def get_conversations(
    session: Session = Depends(get_session)
):
    return conversation_service.get_conversations(session)


@router.get("/conversations/{conversation_id}")
def get_conversation_messages(
    conversation_id: UUID,
    session: Session = Depends(get_session)
):
    conversation = conversation_service.get_conversation_messages(
        conversation_id,
        session
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return conversation

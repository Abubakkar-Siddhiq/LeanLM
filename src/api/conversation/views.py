from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import Session

from db.session import get_session
from api.auth.dependencies import get_current_user
from db.models import User
from api.conversation.services import ConversationService


router = APIRouter()
conversation_service = ConversationService()


@router.get("/conversations")
def list_conversations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return conversation_service.get_conversations(session, current_user.id)


@router.get("/conversations/{conversation_id}")
def get_conversation_messages(
    conversation_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return conversation_service.get_conversation_messages(
        session, conversation_id, current_user.id
    )

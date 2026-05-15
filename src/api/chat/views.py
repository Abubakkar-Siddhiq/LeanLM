from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.chat.services import ChatService
from api.chat.schema import ChatRequest
from db.session import get_session


router = APIRouter()
chat_service = ChatService()


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    session: Session = Depends(get_session)
):
    return await chat_service.chat(payload, session)


@router.get("/conversations")
def get_conversations(
    session: Session = Depends(get_session)
):
    return chat_service.get_conversations(session)


@router.get("/conversations/{conversation_id}")
def get_conversation_messages(
    conversation_id: UUID,
    session: Session = Depends(get_session)
):
    conversation = chat_service.get_conversation_messages(
        conversation_id,
        session
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return conversation

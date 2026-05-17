from fastapi import APIRouter, Depends
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

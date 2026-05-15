from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from api.chat.services import ChatService
from api.chat.schema import ChatRequest
from db.session import get_session


router = APIRouter();
chat_service = ChatService();

@router.post("/chat")
async def chat(
        payload: ChatRequest,
        session: Session = Depends(get_session)
    ):
    response = await chat_service.chat(payload, session)
    return response
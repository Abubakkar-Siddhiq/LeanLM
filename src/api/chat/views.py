from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel import Session

from api.chat.services import ChatService
from api.chat.schema import ChatRequest
from api.auth.dependencies import get_current_user
from db.models import User
from db.session import get_session


router = APIRouter()
chat_service = ChatService()


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await chat_service.chat(payload, session, background_tasks, current_user.id)

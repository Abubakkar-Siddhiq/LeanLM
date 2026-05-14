from fastapi import APIRouter, Depends, HTTPException, Query
from api.chat.services import ChatService
from api.chat.schema import ChatRequest


router = APIRouter();
chat_service = ChatService();

@router.post("/chat")
async def chat(prompt: ChatRequest):
    response = await chat_service.chat(prompt.prompt)
    return response
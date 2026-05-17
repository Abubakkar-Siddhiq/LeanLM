from fastapi import HTTPException

from db.models import Conversation, Message
from providers.groq import GroqProvider
from sqlmodel import Session, select
from uuid import UUID
from .schema import ChatRequest
from config.prompts import Prompts
import json

class ChatService:    
    MODEL_MAP = {
        "low": "llama-3.1-8b-instant",
        "medium": "qwen/qwen3-32b",
        "high": "openai/gpt-oss-120b",
    }

    def __init__(self):
        self.llm_provider = GroqProvider()

    async def find_intent(self, prompt: str) -> dict:
        user_prompt = prompt.lower()

        response = await self.llm_provider.generate(
            model="llama-3.1-8b-instant",
            prompt=Prompts.intent_detection(user_prompt)
        )
        print("Intent classification response:", response)
        return response
    
    def select_model(self, complexity: str):
        return self.MODEL_MAP[complexity]
    
    async def chat(self, payload: ChatRequest, session: Session):

        # Destructure payload
        prompt = payload.prompt

        if prompt is None or prompt.strip() == "":
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        if not payload.conversation_id:
            conversation = Conversation()
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            conversation_id = conversation.id
        else:
            conversation_id = payload.conversation_id
            conversation = session.get(Conversation, conversation_id)

            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )
        

        user_message = Message(
            role="user",
            content=payload.prompt,
            conversation_id=conversation_id
        )
        session.add(user_message)
        session.commit()
        session.refresh(user_message)

        # Find intent and select model and generate response based on intent
        intent_response = await self.find_intent(prompt)
        intent = json.loads(intent_response)
        model = self.select_model(intent["complexity"])
        response = await self.llm_provider.generate(model=model, prompt=prompt)

        assistant_message = Message(
            role="assistant",
            content=response,
            conversation_id=conversation_id
        )
        session.add(assistant_message)
        session.commit()

        return {
            "user_message_id": user_message.id,
            "assistant_message_id": assistant_message.id,
            "conversation_id": conversation_id,
            "intent": intent["complexity"],
            "reason": intent["reason"],
            "confidence": intent["confidence"],
            "model": model,
            "response": response,
        }

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
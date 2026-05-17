from fastapi import HTTPException, BackgroundTasks
from sqlmodel import Session, select
from db.models import Conversation, Message
from db.session import SessionLocal
from providers.groq import GroqProvider
from .schema import ChatRequest
from config.prompts import Prompts
import json
from memory.context_builder import ContextBuilder
from memory.summarizer import Summarizer

class ChatService:
    MODEL_MAP = {
        "low": "llama-3.1-8b-instant",
        "medium": "qwen/qwen3-32b",
        "high": "openai/gpt-oss-120b",
    }

    def __init__(self):
        self.llm_provider = GroqProvider()
        self.context_builder = ContextBuilder()
        self.summarizer = Summarizer()
        self.local_model = "llama-3.1-8b-instant"

    async def find_intent(self, prompt: str) -> dict:
        user_prompt = prompt.lower()

        response = await self.llm_provider.generate(
            model=self.local_model,
            messages=[{"role": "user", "content": Prompts.intent_detection(user_prompt)}]
        )
        print("Intent classification response:", response)
        return response

    def select_model(self, complexity: str):
        return self.MODEL_MAP[complexity]

    async def chat(self, payload: ChatRequest, session: Session, background_tasks: BackgroundTasks):
        prompt = payload.prompt

        if prompt is None or prompt.strip() == "":
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        # Get or Create Converation
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

        # Save message to DB
        user_message = Message(
            role="user",
            content=payload.prompt,
            conversation_id=conversation_id
        )
        session.add(user_message)
        session.commit()
        session.refresh(user_message)

        # Fetch conversation history for context
        messages = session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        ).all()

        chat_history = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        # Build context
        context =self.context_builder.build(
            system_prompt=Prompts.system_prompt(),
            summary=conversation.summary or "",
            messages=chat_history
        )

        # Find intent and select model and generate response based on intent
        intent_response = await self.find_intent(prompt)
        intent = json.loads(intent_response)
        model = self.select_model(intent["complexity"])

        # Generate Response
        response = await self.llm_provider.generate(model=model, messages=context)

        # Save assistant response to DB
        assistant_message = Message(
            role="assistant",
            content=response,
            conversation_id=conversation_id
        )
        session.add(assistant_message)

        # Update Conversation Counter
        conversation.message_count += 2  # user + assistant
        session.add(conversation)
        session.commit()
        session.refresh(assistant_message)

        # Calc context tokens
        context_tokens = sum(len(m["content"].split()) for m in context)

        if self.summarizer.should_summarize(conversation, messages, context_tokens):
            background_tasks.add_task(
                self.summarizer.run_summarization,
                conversation_id=conversation_id,
                session=SessionLocal(),
                llm_provider=self.llm_provider,
                local_model=self.local_model
            )

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

import logging
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException
from sqlmodel import Session, select

from db.models import Conversation, Message
from db.session import SessionLocal
from providers.groq import GroqProvider
from .schema import ChatRequest
from config.prompts import Prompts
from memory.context_builder import ContextBuilder
from memory.summarizer import Summarizer
from services.embedder import Embedder
from services.prompt_builder import ChatPromptBuilder
from services.routing import IntentClassifier, ModelSelector

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.llm_provider = GroqProvider()
        self.context_builder = ContextBuilder()
        self.summarizer = Summarizer()
        self.local_model = "llama-3.1-8b-instant"
        self.classifier = IntentClassifier(self.llm_provider, self.local_model)
        self.model_selector = ModelSelector()
        self.embedder = Embedder()
        self.prompt_builder = ChatPromptBuilder()

    def _validate_prompt(self, prompt: str | None) -> str:
        if prompt is None or prompt.strip() == "":
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        return prompt.strip()

    def _get_or_create_conversation(
        self, payload: ChatRequest, session: Session
    ) -> tuple[Conversation, UUID]:
        if not payload.conversation_id:
            conversation = Conversation()
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation, conversation.id

        conversation = session.get(Conversation, payload.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation, payload.conversation_id

    def _save_user_message(
        self, prompt: str, conversation_id: UUID, session: Session
    ) -> Message:
        user_message = Message(
            role="user",
            content=prompt,
            conversation_id=conversation_id
        )
        embedding = self.embedder.embed(user_message.content)
        user_message.embedding = embedding
        session.add(user_message)
        session.commit()
        session.refresh(user_message)
        return user_message

    def _get_conversation_messages(
        self, session: Session, conversation_id: UUID
    ) -> list[Message]:
        return session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        ).all()

    def _format_chat_history(
        self, messages: list[Message]
    ) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def _save_assistant_message(
        self,
        response: str,
        conversation: Conversation,
        conversation_id: UUID,
        session: Session,
    ) -> Message:
        assistant_message = Message(
            role="assistant",
            content=response,
            conversation_id=conversation_id
        )
        session.add(assistant_message)
        conversation.message_count += 2
        session.add(conversation)
        session.commit()
        session.refresh(assistant_message)
        return assistant_message

    def _schedule_summarization_if_needed(
        self,
        conversation: Conversation,
        messages: list[Message],
        context: list[dict[str, str]],
        conversation_id: UUID,
        background_tasks: BackgroundTasks,
    ):
        context_tokens = sum(len(m["content"].split()) for m in context)
        if self.summarizer.should_summarize(conversation, messages, context_tokens):
            background_tasks.add_task(
                self.summarizer.run_summarization,
                conversation_id=conversation_id,
                session=SessionLocal(),
                llm_provider=self.llm_provider,
                local_model=self.local_model,
            )

    async def chat(
        self,
        payload: ChatRequest,
        session: Session,
        background_tasks: BackgroundTasks,
    ):
        prompt = self._validate_prompt(payload.prompt)

        conversation, conversation_id = self._get_or_create_conversation(
            payload, session
        )

        user_message = self._save_user_message(prompt, conversation_id, session)

        messages = self._get_conversation_messages(session, conversation_id)
        chat_history = self._format_chat_history(messages)

        relevant_messages = self.retrieve_relevant_messages(
            session=session,
            query=prompt,
            conversation_id=conversation_id,
        )

        context = self.prompt_builder.build(
            system_prompt=Prompts.system_prompt(),
            summary=conversation.summary or "",
            messages=chat_history,
            relevant_messages=relevant_messages,
        )

        intent = await self.classifier.classify(prompt)
        complexity = intent.get("complexity", "medium")
        try:
            model = self.model_selector.select_model(complexity)
        except KeyError:
            logger.warning("Unknown complexity '%s', falling back to medium", complexity)
            model = self.model_selector.select_model("medium")
            complexity = "medium"

        response = await self.llm_provider.generate(model=model, messages=context)

        assistant_message = self._save_assistant_message(
            response, conversation, conversation_id, session
        )

        self._schedule_summarization_if_needed(
            conversation, messages, context, conversation_id, background_tasks
        )

        return {
            "user_message_id": user_message.id,
            "assistant_message_id": assistant_message.id,
            "conversation_id": conversation_id,
            "intent": complexity,
            "reason": intent.get("reason", "fallback_default"),
            "confidence": intent.get("confidence", 0),
            "model": model,
            "response": response,
        }

    def retrieve_relevant_messages(
        self,
        session: Session,
        query: str,
        conversation_id: UUID,
        limit: int = 5,
    ) -> list[Message]:
        query_embedding = self.embedder.embed(query)
        messages = session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.embedding != None)
            .order_by(Message.embedding.cosine_distance(query_embedding))
            .limit(limit)
        ).all()
        return messages

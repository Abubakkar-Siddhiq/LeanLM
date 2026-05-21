import logging
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException
from sqlmodel import Session, select

from db.models import Conversation, Message
from db.session import SessionLocal
from providers import ProviderFactory
from config.models import CLASSIFIER_MODEL
from config.routing import MODEL_TO_PROVIDER
from schemas.trace import RequestTrace
from schemas.llm import LLMResponse
from schemas.routing import RouteDecision
from services.usage_tracker import UsageTracker
from .schema import ChatRequest
from config.prompts import Prompts
from memory.context_builder import ContextBuilder
from memory.summarizer import Summarizer
from services.embedder import Embedder
from services.prompt_builder import ChatPromptBuilder
from services.routing import IntentClassifier, ModelSelector
from services.usage_logger import UsageLogger
from api.providers.services import ProviderKeyService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.llm_provider = ProviderFactory.get("groq")
        self.provider_key_service = ProviderKeyService()
        self.context_builder = ContextBuilder()
        self.summarizer = Summarizer()
        self.local_model = CLASSIFIER_MODEL
        self.classifier = IntentClassifier(self.llm_provider, self.local_model)
        self.model_selector = ModelSelector()
        self.embedder = Embedder()
        self.prompt_builder = ChatPromptBuilder()
        self.usage_tracker = UsageTracker()
        self.usage_logger = UsageLogger()

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

    def _estimate_cost(
        self,
        context: list[dict[str, str]],
        response: str,
        model: str,
        llm_response=None,
    ):
        input_tokens = (
            llm_response.input_tokens
            if llm_response and llm_response.input_tokens is not None
            else self.usage_tracker.estimate_tokens(context)
        )
        output_tokens = (
            llm_response.output_tokens
            if llm_response and llm_response.output_tokens is not None
            else len(response.split())
        )
        estimated_cost = self.usage_tracker.estimate_cost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return {
            "input_tokens_estimate": input_tokens,
            "output_tokens_estimate": output_tokens,
            "estimated_cost": estimated_cost,
        } 

    async def _generate_with_fallbacks(
        self,
        route: RouteDecision,
        context: list[dict[str, str]],
        session: Session,
    ) -> tuple[LLMResponse, RouteDecision, str]:
        first_error: str | None = None
        models_to_try = [route.model] + route.fallback_models
        provider_source = "env"

        for model in models_to_try:
            try:
                provider_name = MODEL_TO_PROVIDER.get(model, "groq")
                provider = ProviderFactory.get(provider_name)
                if not provider:
                    logger.warning("No provider registered for %s, skipping model %s", provider_name, model)
                    continue

                api_key = self.provider_key_service.get_decrypted_api_key(session, provider_name)
                if api_key:
                    provider_source = "byok"
                else:
                    provider_source = "env"

                llm_response = await provider.generate(model=model, messages=context, api_key=api_key)

                if model != route.model:
                    route.fallback_used = True
                    route.fallback_model = model
                    route.fallback_error = first_error[:500] if first_error else None
                    logger.info("Fallback to %s succeeded", model)

                return llm_response, route, provider_source
            except Exception as e:
                if model == route.model:
                    first_error = str(e)
                    logger.warning("Primary model %s failed: %s", route.model, first_error)
                else:
                    logger.warning("Fallback model %s failed: %s", model, e)
                continue

        raise HTTPException(
            status_code=502,
            detail=f"All models failed. Last error: {(first_error or 'unknown')[:200]}",
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

        groq_key = self.provider_key_service.get_decrypted_api_key(session, "groq")
        intent = await self.classifier.classify(prompt, api_key=groq_key)

        byok_providers = self.provider_key_service.get_available_providers(session)
        if byok_providers:
            available_providers = byok_providers
        else:
            available_providers = ProviderFactory.available_providers()

        if not available_providers:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "provider_unavailable",
                    "message": "No active provider key found. Add a provider key to continue.",
                },
            )

        route = self.model_selector.select(intent, available_providers=available_providers)

        llm_response, route, provider_source = await self._generate_with_fallbacks(route, context, session)
        response = llm_response.content

        actual_model = route.fallback_model if route.fallback_used else route.model

        trace = RequestTrace(
            provider=route.provider,
            model=actual_model,
            complexity=route.complexity,
            classifier_reason=route.classifier_reason,
            confidence=route.confidence,
            prompt_tokens_estimate=sum(len(m["content"].split()) for m in context),
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            total_tokens=llm_response.total_tokens,
            latency_ms=llm_response.latency_ms,
        )

        assistant_message = self._save_assistant_message(
            response, conversation, conversation_id, session
        )

        cost_info = self._estimate_cost(context, response, actual_model, llm_response)
        try:
            self.usage_logger.log_usage(
                session=session,
                conversation_id=conversation_id,
                user_message_id=user_message.id,
                assistant_message_id=assistant_message.id,
                route=route,
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
                total_tokens=llm_response.total_tokens,
                estimated_cost=cost_info["estimated_cost"],
                latency_ms=llm_response.latency_ms,
            )
        except Exception:
            logger.exception("Usage logging failed, chat response still succeeds")

        self._schedule_summarization_if_needed(
            conversation, messages, context, conversation_id, background_tasks
        )

        return {
            "user_message_id": user_message.id,
            "assistant_message_id": assistant_message.id,
            "conversation_id": conversation_id,
            "intent": route.complexity,
            "task_type": route.task_type,
            "classifier_reason": route.classifier_reason,
            "routing_reason": route.routing_reason,
            "confidence": route.confidence,
            "provider": route.provider,
            "model": route.model,
            "fallback_used": route.fallback_used,
            "fallback_model": route.fallback_model,
            "fallback_error": route.fallback_error,
            "available_providers": available_providers,
            "provider_source": provider_source,
            "response": response,
            "usage": {
                "input_tokens": llm_response.input_tokens,
                "output_tokens": llm_response.output_tokens,
                "total_tokens": llm_response.total_tokens,
                "estimated_cost": cost_info["estimated_cost"],
                "latency_ms": llm_response.latency_ms,
            },
            "trace": trace.model_dump(),
            "cost_info": cost_info,
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

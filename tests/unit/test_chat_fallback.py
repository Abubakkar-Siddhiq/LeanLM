"""Unit tests for ChatService fallback execution — mocks providers."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import HTTPException

from schemas.routing import RouteDecision
from schemas.llm import LLMResponse
from schemas.classification import ClassificationResult
from api.chat.services import ChatService


pytestmark = pytest.mark.asyncio


@pytest.fixture
def chat_service():
    mock_provider = AsyncMock()
    mock_pks = MagicMock()
    mock_pks.get_decrypted_api_key.return_value = None
    with patch("api.chat.services.ProviderFactory.get", return_value=mock_provider):
        with patch("api.chat.services.ProviderKeyService", return_value=mock_pks):
            service = ChatService()
            yield service, mock_provider, mock_pks


@pytest.fixture
def route():
    return RouteDecision(
        provider="groq",
        model="qwen/qwen3-32b",
        task_type="coding",
        complexity="medium",
        classifier_reason="Test reason.",
        routing_reason="Test routing.",
        confidence=0.85,
        fallback_models=["openai/gpt-oss-120b", "llama-3.1-8b-instant"],
    )


@pytest.fixture
def context():
    return [{"role": "user", "content": "Hello"}]


class TestChatServiceFallback:
    async def test_primary_succeeds_no_fallback(
        self, chat_service, route, context
    ):
        service, mock_provider, _ = chat_service
        llm_response = LLMResponse(content="OK", provider="groq", model="qwen/qwen3-32b")
        mock_provider.generate.return_value = llm_response

        result_response, result_route, prov_src = await service._generate_with_fallbacks(route, context, session=MagicMock())

        assert result_response.content == "OK"
        assert result_route.fallback_used is False
        assert result_route.fallback_model is None
        assert result_route.fallback_error is None
        mock_provider.generate.assert_awaited_once_with(
            model=route.model, messages=context, api_key=None
        )

    async def test_primary_fails_fallback_succeeds(
        self, chat_service, route, context
    ):
        service, mock_provider, _ = chat_service
        mock_provider.generate = AsyncMock(side_effect=[
            RuntimeError("Primary model down"),
            LLMResponse(content="Fallback OK", provider="groq", model="openai/gpt-oss-120b"),
        ])

        result_response, result_route, prov_src = await service._generate_with_fallbacks(route, context, session=MagicMock())

        assert result_response.content == "Fallback OK"
        assert result_route.fallback_used is True
        assert result_route.fallback_model == "openai/gpt-oss-120b"
        assert "Primary model down" in result_route.fallback_error
        assert mock_provider.generate.await_count == 2

    async def test_primary_fails_fallback_skips_duplicate_model(
        self, chat_service, route, context
    ):
        service, mock_provider, _ = chat_service
        mock_provider.generate = AsyncMock(side_effect=[
            RuntimeError("Primary down"),
            LLMResponse(content="Fallback OK", provider="groq", model="openai/gpt-oss-120b"),
        ])

        result_response, result_route, prov_src = await service._generate_with_fallbacks(route, context, session=MagicMock())

        assert result_response.content == "Fallback OK"
        assert result_route.fallback_model == "openai/gpt-oss-120b"
        assert mock_provider.generate.await_count == 2

    async def test_all_models_fail_raises_502(
        self, chat_service, route, context
    ):
        service, mock_provider, _ = chat_service
        mock_provider.generate = AsyncMock(side_effect=RuntimeError("All models down"))

        with pytest.raises(HTTPException) as exc_info:
            await service._generate_with_fallbacks(route, context, session=MagicMock())

        assert exc_info.value.status_code == 502
        assert "All models failed" in exc_info.value.detail

    async def test_empty_fallback_models_still_raises(
        self, chat_service, context
    ):
        service, mock_provider, _ = chat_service
        route_no_fallback = RouteDecision(
            provider="groq",
            model="llama-3.1-8b-instant",
            task_type="simple_qa",
            complexity="low",
            classifier_reason="Test.",
            routing_reason="Test.",
            confidence=0.9,
            fallback_models=[],
        )
        mock_provider.generate = AsyncMock(side_effect=RuntimeError("Down"))

        with pytest.raises(HTTPException) as exc_info:
            await service._generate_with_fallbacks(route_no_fallback, context, session=MagicMock())

        assert exc_info.value.status_code == 502

    async def test_byok_key_passed_to_provider(self, chat_service, route, context):
        service, mock_provider, mock_pks = chat_service
        mock_pks.get_decrypted_api_key.return_value = "sk-byok-decrypted-key"
        llm_response = LLMResponse(content="BYOK OK", provider="groq", model="qwen/qwen3-32b")
        mock_provider.generate.return_value = llm_response

        result_response, result_route, prov_src = await service._generate_with_fallbacks(route, context, session=MagicMock())

        assert result_response.content == "BYOK OK"
        assert prov_src == "byok"
        mock_provider.generate.assert_awaited_once_with(
            model=route.model, messages=context, api_key="sk-byok-decrypted-key"
        )

    async def test_env_fallback_when_no_byok_key(self, chat_service, route, context):
        service, mock_provider, mock_pks = chat_service
        mock_pks.get_decrypted_api_key.return_value = None
        llm_response = LLMResponse(content="Env OK", provider="groq", model="qwen/qwen3-32b")
        mock_provider.generate.return_value = llm_response

        result_response, result_route, prov_src = await service._generate_with_fallbacks(route, context, session=MagicMock())

        assert result_response.content == "Env OK"
        assert prov_src == "env"
        mock_provider.generate.assert_awaited_once_with(
            model=route.model, messages=context, api_key=None
        )

    async def test_chat_raises_400_when_no_available_providers(self, chat_service):
        from api.chat.schema import ChatRequest
        service, mock_provider, mock_pks = chat_service
        mock_pks.get_available_providers.return_value = []

        service._validate_prompt = MagicMock(return_value="Hello")
        mock_conversation = MagicMock()
        mock_conversation.summary = None
        service._get_or_create_conversation = MagicMock(return_value=(mock_conversation, MagicMock()))
        service._save_user_message = MagicMock(return_value=MagicMock())
        service._get_conversation_messages = MagicMock(return_value=[])
        service._format_chat_history = MagicMock(return_value=[])
        service.retrieve_relevant_messages = MagicMock(return_value=[])
        service.prompt_builder.build = MagicMock(return_value=[{"role": "user", "content": "Hello"}])
        service.classifier.classify = AsyncMock(return_value=ClassificationResult())

        with patch("api.chat.services.ProviderFactory.available_providers", return_value=[]):
            with pytest.raises(HTTPException) as exc_info:
                await service.chat(
                    payload=ChatRequest(prompt="Hello"),
                    session=MagicMock(),
                    background_tasks=MagicMock(),
                )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"] == "provider_unavailable"
        assert "No active provider key found" in exc_info.value.detail["message"]

    async def test_byok_providers_take_priority_over_env(self, chat_service):
        from api.chat.schema import ChatRequest
        service, mock_provider, mock_pks = chat_service
        mock_pks.get_available_providers.return_value = ["groq", "openai"]

        service._validate_prompt = MagicMock(return_value="Hello")
        mock_conversation = MagicMock()
        mock_conversation.summary = None
        mock_conversation.message_count = 0
        mock_conversation.last_summarized_at_count = 0
        service._get_or_create_conversation = MagicMock(return_value=(mock_conversation, MagicMock()))
        service._save_user_message = MagicMock(return_value=MagicMock())
        service._get_conversation_messages = MagicMock(return_value=[])
        service._format_chat_history = MagicMock(return_value=[])
        service.retrieve_relevant_messages = MagicMock(return_value=[])
        service.prompt_builder.build = MagicMock(return_value=[{"role": "user", "content": "Hello"}])
        service.classifier.classify = AsyncMock(return_value=ClassificationResult())
        mock_provider.generate = AsyncMock(return_value=LLMResponse(content="OK", provider="groq", model="qwen/qwen3-32b"))
        mock_pks.get_decrypted_api_key.return_value = "sk-byok-for-groq"

        result = await service.chat(
            payload=ChatRequest(prompt="Hello"),
            session=MagicMock(),
            background_tasks=MagicMock(),
        )

        assert result["provider_source"] == "byok"
        assert "provider_unavailable" not in result

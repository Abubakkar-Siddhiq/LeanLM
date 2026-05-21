"""Unit tests for ChatService fallback execution — mocks GroqProvider."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from schemas.routing import RouteDecision
from schemas.llm import LLMResponse
from api.chat.services import ChatService


pytestmark = pytest.mark.asyncio


@pytest.fixture
def chat_service():
    with patch("api.chat.services.GroqProvider") as mock_provider_cls:
        mock_provider = AsyncMock()
        mock_provider_cls.return_value = mock_provider
        service = ChatService()
        service.llm_provider = mock_provider
        yield service, mock_provider


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
        service, mock_provider = chat_service
        llm_response = LLMResponse(content="OK", provider="groq", model="qwen/qwen3-32b")
        mock_provider.generate.return_value = llm_response

        result_response, result_route = await service._generate_with_fallbacks(route, context)

        assert result_response.content == "OK"
        assert result_route.fallback_used is False
        assert result_route.fallback_model is None
        assert result_route.fallback_error is None
        mock_provider.generate.assert_awaited_once_with(
            model=route.model, messages=context
        )

    async def test_primary_fails_fallback_succeeds(
        self, chat_service, route, context
    ):
        service, mock_provider = chat_service
        mock_provider.generate = AsyncMock(side_effect=[
            RuntimeError("Primary model down"),
            LLMResponse(content="Fallback OK", provider="groq", model="openai/gpt-oss-120b"),
        ])

        result_response, result_route = await service._generate_with_fallbacks(route, context)

        assert result_response.content == "Fallback OK"
        assert result_route.fallback_used is True
        assert result_route.fallback_model == "openai/gpt-oss-120b"
        assert "Primary model down" in result_route.fallback_error
        assert mock_provider.generate.await_count == 2

    async def test_primary_fails_fallback_skips_duplicate_model(
        self, chat_service, route, context
    ):
        service, mock_provider = chat_service
        mock_provider.generate = AsyncMock(side_effect=[
            RuntimeError("Primary down"),
            LLMResponse(content="Fallback OK", provider="groq", model="openai/gpt-oss-120b"),
        ])

        result_response, result_route = await service._generate_with_fallbacks(route, context)

        assert result_response.content == "Fallback OK"
        assert result_route.fallback_model == "openai/gpt-oss-120b"
        assert mock_provider.generate.await_count == 2

    async def test_all_models_fail_raises_502(
        self, chat_service, route, context
    ):
        service, mock_provider = chat_service
        mock_provider.generate = AsyncMock(side_effect=RuntimeError("All models down"))

        with pytest.raises(HTTPException) as exc_info:
            await service._generate_with_fallbacks(route, context)

        assert exc_info.value.status_code == 502
        assert "All models failed" in exc_info.value.detail

    async def test_empty_fallback_models_still_raises(
        self, chat_service, context
    ):
        service, mock_provider = chat_service
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
            await service._generate_with_fallbacks(route_no_fallback, context)

        assert exc_info.value.status_code == 502

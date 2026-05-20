"""Unit tests for LLMResponse schema and GroqProvider integration — no live API calls."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import json
import pytest
from schemas.llm import LLMResponse


class TestLLMResponse:
    def test_create_with_minimal_fields(self):
        resp = LLMResponse(
            content="Hello world",
            provider="groq",
            model="llama-3.1-8b-instant",
        )
        assert resp.content == "Hello world"
        assert resp.provider == "groq"
        assert resp.model == "llama-3.1-8b-instant"
        assert resp.input_tokens is None
        assert resp.output_tokens is None
        assert resp.total_tokens is None
        assert resp.latency_ms is None
        assert resp.raw is None

    def test_create_with_all_fields(self):
        resp = LLMResponse(
            content="Test response",
            provider="groq",
            model="qwen/qwen3-32b",
            input_tokens=50,
            output_tokens=30,
            total_tokens=80,
            latency_ms=420.5,
            raw={"id": "chatcmpl-123", "usage": {"prompt_tokens": 50}},
        )
        assert resp.content == "Test response"
        assert resp.input_tokens == 50
        assert resp.output_tokens == 30
        assert resp.total_tokens == 80
        assert resp.latency_ms == 420.5
        assert resp.raw["id"] == "chatcmpl-123"

    def test_content_is_always_string(self):
        resp = LLMResponse(
            content="",
            provider="groq",
            model="test",
        )
        assert isinstance(resp.content, str)
        assert resp.content == ""

    def test_tokens_are_optional(self):
        resp = LLMResponse(
            content="No usage data",
            provider="groq",
            model="test",
        )
        assert resp.input_tokens is None
        assert resp.output_tokens is None
        assert resp.total_tokens is None

    def test_latency_is_optional_float(self):
        resp = LLMResponse(
            content="Fast response",
            provider="groq",
            model="test",
            latency_ms=123.45,
        )
        assert isinstance(resp.latency_ms, float)
        assert resp.latency_ms == 123.45

    def test_raw_is_optional_dict(self):
        resp = LLMResponse(
            content="With raw",
            provider="groq",
            model="test",
            raw={"key": "value"},
        )
        assert resp.raw == {"key": "value"}


class TestIntentClassifierLLMResponse:
    """IntentClassifier should use llm_response.content, not the LLMResponse object directly."""

    @pytest.mark.asyncio
    async def test_classify_extracts_content_from_llm_response(self):
        """Verify that .content is extracted from LLMResponse before json.loads."""

        class MockProvider:
            async def generate(self, model, messages):
                return LLMResponse(
                    content=json.dumps({
                        "task_type": "simple_qa",
                        "complexity": "low",
                        "confidence": 0.95,
                        "reason": "Simple question.",
                    }),
                    provider="groq",
                    model=model,
                )

        from services.routing import IntentClassifier

        classifier = IntentClassifier(llm_provider=MockProvider(), classify_model="test")
        result = await classifier.classify("What is a variable?")

        assert result.task_type == "simple_qa"
        assert result.complexity == "low"
        assert result.confidence == 0.95
        assert result.reason == "Simple question."

    @pytest.mark.asyncio
    async def test_classify_handles_invalid_json_from_llm_response(self):
        """Should fall back to medium on parse failure."""

        class BrokenProvider:
            async def generate(self, model, messages):
                return LLMResponse(
                    content="not valid json at all",
                    provider="groq",
                    model=model,
                )

        from services.routing import IntentClassifier

        classifier = IntentClassifier(llm_provider=BrokenProvider(), classify_model="test")
        result = await classifier.classify("broken prompt")

        assert result.complexity == "medium"
        assert result.reason == "classification_failed_fallback"
        assert result.confidence == 0.0

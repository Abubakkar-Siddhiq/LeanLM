"""Unit tests for ModelSelector — no live LLM calls, no API keys."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from schemas.classification import ClassificationResult
from services.routing import ModelSelector


@pytest.fixture
def selector():
    return ModelSelector()


class TestModelSelector:
    def test_low_simple_qa_routes_to_cheap_model(self, selector):
        intent = ClassificationResult(
            task_type="simple_qa",
            complexity="low",
            confidence=0.95,
            reason="Simple conceptual explanation.",
        )
        route = selector.select(intent)

        assert route.task_type == "simple_qa"
        assert route.complexity == "low"
        assert route.model == "llama-3.1-8b-instant"
        assert route.provider == "groq"

    def test_medium_coding_routes_to_medium_model(self, selector):
        intent = ClassificationResult(
            task_type="coding",
            complexity="medium",
            confidence=0.85,
            reason="Requires code generation.",
        )
        route = selector.select(intent)

        assert route.task_type == "coding"
        assert route.complexity == "medium"
        assert route.model == "qwen/qwen3-32b"

    def test_medium_debugging_routes_to_medium_model(self, selector):
        intent = ClassificationResult(
            task_type="debugging",
            complexity="medium",
            confidence=0.9,
            reason="Requires framework-specific debugging.",
        )
        route = selector.select(intent)

        assert route.task_type == "debugging"
        assert route.complexity == "medium"
        assert route.model == "qwen/qwen3-32b"

    def test_high_reasoning_routes_to_high_model(self, selector):
        intent = ClassificationResult(
            task_type="reasoning",
            complexity="high",
            confidence=0.98,
            reason="Requires architecture decisions.",
        )
        route = selector.select(intent)

        assert route.task_type == "reasoning"
        assert route.complexity == "high"
        assert route.model == "openai/gpt-oss-120b"

    def test_unknown_complexity_falls_back_to_medium(self, selector):
        intent = ClassificationResult.model_construct(
            task_type="coding",
            complexity="ultra",
            confidence=0.5,
            reason="Unknown complexity.",
        )
        route = selector.select(intent)

        assert route.model == "qwen/qwen3-32b"
        assert "Fallback" in route.routing_reason

    def test_route_decision_contains_classifier_reason(self, selector):
        intent = ClassificationResult(
            task_type="coding",
            complexity="medium",
            confidence=0.85,
            reason="Requires code generation.",
        )
        route = selector.select(intent)

        assert route.classifier_reason == "Requires code generation."

    def test_route_decision_contains_routing_reason(self, selector):
        intent = ClassificationResult(
            task_type="coding",
            complexity="medium",
            confidence=0.85,
            reason="Requires code generation.",
        )
        route = selector.select(intent)

        assert route.routing_reason
        assert isinstance(route.routing_reason, str)
        assert len(route.routing_reason) > 0

    def test_route_decision_contains_all_required_fields(self, selector):
        intent = ClassificationResult(
            task_type="extraction",
            complexity="low",
            confidence=0.9,
            reason="Structured extraction.",
        )
        route = selector.select(intent)

        assert route.task_type == "extraction"
        assert route.complexity == "low"
        assert route.confidence == 0.9
        assert route.provider == "groq"
        assert route.model == "llama-3.1-8b-instant"
        assert route.classifier_reason == "Structured extraction."
        assert route.routing_reason

    def test_summarization_low_routes_to_cheap_model(self, selector):
        intent = ClassificationResult(
            task_type="summarization",
            complexity="low",
            confidence=0.9,
            reason="Straightforward summarization.",
        )
        route = selector.select(intent)

        assert route.model == "llama-3.1-8b-instant"

    def test_extraction_low_routes_to_cheap_model(self, selector):
        intent = ClassificationResult(
            task_type="extraction",
            complexity="low",
            confidence=0.95,
            reason="Simple structured extraction.",
        )
        route = selector.select(intent)

        assert route.model == "llama-3.1-8b-instant"

    def test_writing_low_routes_to_cheap_model(self, selector):
        intent = ClassificationResult(
            task_type="writing",
            complexity="low",
            confidence=0.85,
            reason="Content rewriting task.",
        )
        route = selector.select(intent)

        assert route.model == "llama-3.1-8b-instant"

    def test_fallback_models_included_for_low(self, selector):
        intent = ClassificationResult(
            task_type="simple_qa",
            complexity="low",
            confidence=0.95,
            reason="Simple query.",
        )
        route = selector.select(intent)

        assert route.fallback_models == ["qwen/qwen3-32b"]

    def test_fallback_models_included_for_medium(self, selector):
        intent = ClassificationResult(
            task_type="coding",
            complexity="medium",
            confidence=0.85,
            reason="Requires code generation.",
        )
        route = selector.select(intent)

        assert route.fallback_models == [
            "openai/gpt-oss-120b",
            "llama-3.1-8b-instant",
        ]

    def test_fallback_models_included_for_high(self, selector):
        intent = ClassificationResult(
            task_type="reasoning",
            complexity="high",
            confidence=0.98,
            reason="Complex reasoning.",
        )
        route = selector.select(intent)

        assert route.fallback_models == ["qwen/qwen3-32b"]

    def test_fallback_models_removes_primary_model(self, selector):
        intent = ClassificationResult(
            task_type="writing",
            complexity="low",
            confidence=0.85,
            reason="Writing task.",
        )
        route = selector.select(intent)

        assert route.model == "llama-3.1-8b-instant"
        assert "llama-3.1-8b-instant" not in route.fallback_models

    def test_fallback_defaults_on_route_decision(self, selector):
        intent = ClassificationResult(
            task_type="simple_qa",
            complexity="low",
            confidence=0.95,
            reason="Simple query.",
        )
        route = selector.select(intent)

        assert route.fallback_used is False
        assert route.fallback_model is None
        assert route.fallback_error is None

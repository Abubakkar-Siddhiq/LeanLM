"""Unit tests for UsageAnalytics service — no live LLM calls, no API keys."""

from uuid import UUID, uuid4
from datetime import datetime, timezone

import pytest
from sqlmodel import Session

from db.usage import LLMUsageLog
from api.usage.services import UsageAnalytics


def _seed_logs(session: Session, user_id: UUID, count: int = 5):
    for i in range(count):
        log = LLMUsageLog(
            user_id=user_id,
            conversation_id=uuid4(),
            user_message_id=uuid4(),
            assistant_message_id=uuid4(),
            provider="groq",
            model="llama-3.1-8b-instant" if i % 2 == 0 else "qwen/qwen3-32b",
            task_type="simple_qa" if i < 3 else "coding",
            complexity="low" if i % 2 == 0 else "medium",
            classifier_reason="Test reason.",
            routing_reason="Test routing.",
            confidence=0.9,
            input_tokens=100 + i * 10,
            output_tokens=50 + i * 5,
            total_tokens=150 + i * 15,
            estimated_cost=0.001 * (i + 1),
            latency_ms=200.0 + i * 10,
        )
        session.add(log)
    session.commit()


class TestUsageAnalytics:
    def test_summary_empty(self, db_session: Session, test_user_id: UUID):
        service = UsageAnalytics()
        result = service.get_summary(db_session, test_user_id)

        assert result.total_requests == 0
        assert result.total_input_tokens == 0
        assert result.total_output_tokens == 0
        assert result.total_tokens == 0
        assert result.total_estimated_cost == 0.0
        assert result.average_latency_ms is None

    def test_summary_aggregates_correctly(self, db_session: Session, test_user_id: UUID):
        _seed_logs(db_session, test_user_id, count=3)
        service = UsageAnalytics()
        result = service.get_summary(db_session, test_user_id)

        assert result.total_requests == 3
        assert result.total_input_tokens == 330  # 100 + 110 + 120
        assert result.total_output_tokens == 165  # 50 + 55 + 60
        assert result.total_tokens == 495          # 150 + 165 + 180
        assert result.total_estimated_cost == 0.006  # 0.001 + 0.002 + 0.003
        assert result.average_latency_ms is not None

    def test_by_model_groups_correctly(self, db_session: Session, test_user_id: UUID):
        _seed_logs(db_session, test_user_id, count=5)
        service = UsageAnalytics()
        results = service.get_usage_by_model(db_session, test_user_id)

        models = {r.model: r for r in results}
        assert len(results) == 2
        assert "llama-3.1-8b-instant" in models
        assert "qwen/qwen3-32b" in models
        # 3 even-indexed logs used llama, 2 odd-indexed used qwen
        assert models["llama-3.1-8b-instant"].request_count == 3
        assert models["qwen/qwen3-32b"].request_count == 2
        assert models["llama-3.1-8b-instant"].provider == "groq"

    def test_by_task_type_groups_correctly(self, db_session: Session, test_user_id: UUID):
        _seed_logs(db_session, test_user_id, count=5)
        service = UsageAnalytics()
        results = service.get_usage_by_task_type(db_session, test_user_id)

        types = {r.task_type: r for r in results}
        assert len(results) == 2
        assert "simple_qa" in types
        assert "coding" in types
        assert types["simple_qa"].request_count == 3
        assert types["coding"].request_count == 2

    def test_recent_usage_ordered_by_created_at(self, db_session: Session, test_user_id: UUID):
        _seed_logs(db_session, test_user_id, count=5)
        service = UsageAnalytics()
        results = service.get_recent_usage(db_session, test_user_id, limit=10)

        assert len(results) == 5
        # Most recent first
        for i in range(len(results) - 1):
            assert results[i].created_at >= results[i + 1].created_at

    def test_recent_usage_respects_limit(self, db_session: Session, test_user_id: UUID):
        _seed_logs(db_session, test_user_id, count=10)
        service = UsageAnalytics()
        results = service.get_recent_usage(db_session, test_user_id, limit=3)

        assert len(results) == 3

    def test_recent_usage_returns_min_fields(self, db_session: Session, test_user_id: UUID):
        _seed_logs(db_session, test_user_id, count=1)
        service = UsageAnalytics()
        results = service.get_recent_usage(db_session, test_user_id, limit=10)

        item = results[0]
        assert item.id is not None
        assert item.conversation_id is not None
        assert item.provider == "groq"
        assert item.model is not None
        assert item.task_type is not None
        assert item.complexity is not None
        assert item.classifier_reason is not None
        assert item.routing_reason is not None
        assert item.confidence is not None
        assert item.input_tokens is not None
        assert item.output_tokens is not None
        assert item.total_tokens is not None
        assert item.estimated_cost is not None
        assert item.latency_ms is not None
        assert item.created_at is not None

"""Unit tests for LLMUsageLog model and UsageLogger — no live LLM calls, no API keys."""

from uuid import UUID, uuid4
from datetime import datetime, timezone

import pytest
from sqlmodel import Session, select

from db.usage import LLMUsageLog
from services.usage_logger import UsageLogger
from schemas.routing import RouteDecision
from schemas.classification import ClassificationResult


def make_route():
    intent = ClassificationResult(
        task_type="coding",
        complexity="medium",
        confidence=0.85,
        reason="Requires code generation.",
    )
    return RouteDecision(
        provider="groq",
        model="qwen/qwen3-32b",
        task_type=intent.task_type,
        complexity=intent.complexity,
        classifier_reason=intent.reason,
        routing_reason="Coding tasks routed to medium model.",
        confidence=intent.confidence,
    )


class TestLLMUsageLogModel:
    def test_create_log_minimal(self, db_session: Session, test_user_id: UUID):
        log = LLMUsageLog(
            user_id=test_user_id,
            conversation_id=uuid4(),
            user_message_id=uuid4(),
            assistant_message_id=uuid4(),
            provider="groq",
            model="llama-3.1-8b-instant",
            task_type="simple_qa",
            complexity="low",
            classifier_reason="Simple question.",
            routing_reason="Simple tasks routed to cheap model.",
            confidence=0.95,
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.id is not None
        assert log.provider == "groq"
        assert log.model == "llama-3.1-8b-instant"
        assert log.task_type == "simple_qa"
        assert log.complexity == "low"
        assert log.classifier_reason == "Simple question."
        assert log.routing_reason == "Simple tasks routed to cheap model."
        assert log.confidence == 0.95
        assert log.input_tokens is None
        assert log.output_tokens is None
        assert log.total_tokens is None
        assert log.estimated_cost == 0.0
        assert log.latency_ms is None
        assert isinstance(log.created_at, datetime)

    def test_create_log_with_all_fields(self, db_session: Session, test_user_id: UUID):
        cid = uuid4()
        log = LLMUsageLog(
            user_id=test_user_id,
            conversation_id=cid,
            user_message_id=uuid4(),
            assistant_message_id=uuid4(),
            provider="groq",
            model="openai/gpt-oss-120b",
            task_type="reasoning",
            complexity="high",
            classifier_reason="Complex architecture decisions.",
            routing_reason="Reasoning tasks routed to most capable model.",
            confidence=0.98,
            input_tokens=150,
            output_tokens=80,
            total_tokens=230,
            estimated_cost=0.0125,
            latency_ms=1234.5,
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.conversation_id == cid
        assert log.input_tokens == 150
        assert log.output_tokens == 80
        assert log.total_tokens == 230
        assert log.estimated_cost == 0.0125
        assert log.latency_ms == 1234.5

    def test_log_persisted_can_be_queried(self, db_session: Session, test_user_id: UUID):
        cid = uuid4()
        log = LLMUsageLog(
            user_id=test_user_id,
            conversation_id=cid,
            user_message_id=uuid4(),
            assistant_message_id=uuid4(),
            provider="groq",
            model="llama-3.1-8b-instant",
            task_type="summarization",
            complexity="low",
            classifier_reason="Summarization.",
            routing_reason="Simple tasks.",
            confidence=0.9,
        )
        db_session.add(log)
        db_session.commit()

        fetched = db_session.exec(
            select(LLMUsageLog).where(LLMUsageLog.conversation_id == cid)
        ).first()
        assert fetched is not None
        assert fetched.task_type == "summarization"


class TestUsageLogger:
    def test_log_usage_creates_record(self, db_session: Session, test_user_id: UUID):
        route = make_route()
        logger = UsageLogger()

        cid = uuid4()
        result = logger.log_usage(
            session=db_session,
            user_id=test_user_id,
            conversation_id=cid,
            user_message_id=uuid4(),
            assistant_message_id=uuid4(),
            route=route,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=0.005,
            latency_ms=500.0,
        )

        assert isinstance(result, LLMUsageLog)
        assert result.id is not None
        assert result.conversation_id == cid
        assert result.provider == "groq"
        assert result.model == "qwen/qwen3-32b"
        assert result.task_type == "coding"
        assert result.complexity == "medium"
        assert result.classifier_reason == "Requires code generation."
        assert result.routing_reason == "Coding tasks routed to medium model."
        assert result.confidence == 0.85
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.total_tokens == 150
        assert result.estimated_cost == 0.005
        assert result.latency_ms == 500.0

    def test_log_usage_with_none_tokens(self, db_session: Session, test_user_id: UUID):
        route = make_route()
        logger = UsageLogger()

        result = logger.log_usage(
            session=db_session,
            user_id=test_user_id,
            conversation_id=uuid4(),
            user_message_id=uuid4(),
            assistant_message_id=uuid4(),
            route=route,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            estimated_cost=0.0,
            latency_ms=None,
        )

        assert result.input_tokens is None
        assert result.output_tokens is None
        assert result.total_tokens is None
        assert result.latency_ms is None

    def test_log_usage_multiple_records(self, db_session: Session, test_user_id: UUID):
        route = make_route()
        logger = UsageLogger()

        cid = uuid4()
        for _ in range(3):
            logger.log_usage(
                session=db_session,
                user_id=test_user_id,
                conversation_id=cid,
                user_message_id=uuid4(),
                assistant_message_id=uuid4(),
                route=route,
                input_tokens=10,
                output_tokens=5,
                total_tokens=15,
                estimated_cost=0.001,
                latency_ms=100.0,
            )

        records = db_session.exec(
            select(LLMUsageLog).where(LLMUsageLog.conversation_id == cid)
        ).all()
        assert len(records) == 3

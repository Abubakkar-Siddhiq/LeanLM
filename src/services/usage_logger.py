import logging
from uuid import UUID
from sqlmodel import Session
from db.usage import LLMUsageLog
from schemas.routing import RouteDecision

logger = logging.getLogger(__name__)


class UsageLogger:
    def log_usage(
        self,
        session: Session,
        conversation_id: UUID,
        user_message_id: UUID,
        assistant_message_id: UUID,
        route: RouteDecision,
        input_tokens: int | None,
        output_tokens: int | None,
        total_tokens: int | None,
        estimated_cost: float,
        latency_ms: float | None,
    ) -> LLMUsageLog:
        log = LLMUsageLog(
            conversation_id=conversation_id,
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            provider=route.provider,
            model=route.model,
            task_type=route.task_type,
            complexity=route.complexity,
            classifier_reason=route.classifier_reason,
            routing_reason=route.routing_reason,
            confidence=route.confidence,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            latency_ms=latency_ms,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log

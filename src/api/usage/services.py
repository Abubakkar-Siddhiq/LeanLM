from uuid import UUID

from sqlmodel import Session, select, func
from db.usage import LLMUsageLog
from api.usage.schemas import (
    UsageSummaryResponse,
    UsageByModelItem,
    UsageByTaskTypeItem,
    RecentUsageItem,
)


class UsageAnalytics:
    def get_summary(self, session: Session, user_id: UUID) -> UsageSummaryResponse:
        row = session.exec(
            select(
                func.count(LLMUsageLog.id).label("total_requests"),
                func.coalesce(func.sum(LLMUsageLog.input_tokens), 0).label("total_input_tokens"),
                func.coalesce(func.sum(LLMUsageLog.output_tokens), 0).label("total_output_tokens"),
                func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(LLMUsageLog.estimated_cost), 0.0).label("total_estimated_cost"),
                func.avg(LLMUsageLog.latency_ms).label("average_latency_ms"),
            )
            .where(LLMUsageLog.user_id == user_id)
        ).one()

        return UsageSummaryResponse(
            total_requests=row.total_requests or 0,
            total_input_tokens=row.total_input_tokens or 0,
            total_output_tokens=row.total_output_tokens or 0,
            total_tokens=row.total_tokens or 0,
            total_estimated_cost=float(row.total_estimated_cost or 0.0),
            average_latency_ms=(
                round(float(row.average_latency_ms), 2)
                if row.average_latency_ms is not None
                else None
            ),
        )

    def get_usage_by_model(self, session: Session, user_id: UUID) -> list[UsageByModelItem]:
        rows = session.exec(
            select(
                LLMUsageLog.provider,
                LLMUsageLog.model,
                func.count(LLMUsageLog.id).label("request_count"),
                func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(LLMUsageLog.estimated_cost), 0.0).label("total_estimated_cost"),
                func.avg(LLMUsageLog.latency_ms).label("average_latency_ms"),
            )
            .where(LLMUsageLog.user_id == user_id)
            .group_by(LLMUsageLog.provider, LLMUsageLog.model)
            .order_by(func.count(LLMUsageLog.id).desc())
        ).all()

        return [
            UsageByModelItem(
                provider=row.provider,
                model=row.model,
                request_count=row.request_count,
                total_tokens=row.total_tokens,
                total_estimated_cost=float(row.total_estimated_cost),
                average_latency_ms=(
                    round(float(row.average_latency_ms), 2)
                    if row.average_latency_ms is not None
                    else None
                ),
            )
            for row in rows
        ]

    def get_usage_by_task_type(self, session: Session, user_id: UUID) -> list[UsageByTaskTypeItem]:
        rows = session.exec(
            select(
                LLMUsageLog.task_type,
                func.count(LLMUsageLog.id).label("request_count"),
                func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(LLMUsageLog.estimated_cost), 0.0).label("total_estimated_cost"),
                func.avg(LLMUsageLog.latency_ms).label("average_latency_ms"),
            )
            .where(LLMUsageLog.user_id == user_id)
            .group_by(LLMUsageLog.task_type)
            .order_by(func.count(LLMUsageLog.id).desc())
        ).all()

        return [
            UsageByTaskTypeItem(
                task_type=row.task_type,
                request_count=row.request_count,
                total_tokens=row.total_tokens,
                total_estimated_cost=float(row.total_estimated_cost),
                average_latency_ms=(
                    round(float(row.average_latency_ms), 2)
                    if row.average_latency_ms is not None
                    else None
                ),
            )
            for row in rows
        ]

    def get_recent_usage(
        self, session: Session, user_id: UUID, limit: int = 20
    ) -> list[RecentUsageItem]:
        rows = session.exec(
            select(LLMUsageLog)
            .where(LLMUsageLog.user_id == user_id)
            .order_by(LLMUsageLog.created_at.desc())
            .limit(limit)
        ).all()

        return [
            RecentUsageItem(
                id=row.id,
                conversation_id=row.conversation_id,
                provider=row.provider,
                model=row.model,
                task_type=row.task_type,
                complexity=row.complexity,
                classifier_reason=row.classifier_reason,
                routing_reason=row.routing_reason,
                confidence=row.confidence,
                input_tokens=row.input_tokens,
                output_tokens=row.output_tokens,
                total_tokens=row.total_tokens,
                estimated_cost=row.estimated_cost,
                latency_ms=row.latency_ms,
                created_at=row.created_at,
            )
            for row in rows
        ]

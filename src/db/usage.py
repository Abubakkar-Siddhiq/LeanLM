from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class LLMUsageLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID
    user_message_id: UUID
    assistant_message_id: UUID
    provider: str
    model: str
    task_type: str
    complexity: str
    classifier_reason: str
    routing_reason: str
    confidence: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: float = Field(default=0.0)
    latency_ms: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

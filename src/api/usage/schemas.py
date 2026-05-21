from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class UsageSummaryResponse(BaseModel):
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_estimated_cost: float = 0.0
    average_latency_ms: Optional[float] = None


class UsageByModelItem(BaseModel):
    provider: str
    model: str
    request_count: int = 0
    total_tokens: int = 0
    total_estimated_cost: float = 0.0
    average_latency_ms: Optional[float] = None


class UsageByTaskTypeItem(BaseModel):
    task_type: str
    request_count: int = 0
    total_tokens: int = 0
    total_estimated_cost: float = 0.0
    average_latency_ms: Optional[float] = None


class RecentUsageItem(BaseModel):
    id: UUID
    conversation_id: UUID
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
    estimated_cost: float = 0.0
    latency_ms: Optional[float] = None
    created_at: datetime

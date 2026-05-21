from pydantic import BaseModel, Field

class RouteDecision(BaseModel):
    provider: str = "groq"
    model: str
    task_type: str
    complexity: str
    classifier_reason: str
    routing_reason: str
    confidence: float
    fallback_models: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    fallback_model: str | None = None
    fallback_error: str | None = None
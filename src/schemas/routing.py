from pydantic import BaseModel

class RouteDecision(BaseModel):
    provider: str = "groq"
    model: str
    task_type: str
    complexity: str
    classifier_reason: str
    routing_reason: str
    confidence: float
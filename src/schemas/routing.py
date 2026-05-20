from pydantic import BaseModel

class RouteDecision(BaseModel):
    provider: str = "groq"
    model: str
    complexity: str
    task_type: str
    reason: str
    confidence: float
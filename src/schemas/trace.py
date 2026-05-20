from pydantic import BaseModel
from typing import Optional

class RequestTrace(BaseModel):
    provider: str = "groq"
    model: str
    complexity: str
    reason: str
    confidence: float
    prompt_tokens_estimate: Optional[int] = None
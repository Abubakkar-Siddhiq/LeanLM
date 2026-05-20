from pydantic import BaseModel, Field
from typing import Literal

class ClassificationResult(BaseModel):
    complexity: Literal["low", "medium", "high"] = "medium"
    reason: str = "fallback_default"
    confidence: float = Field(default=0, ge=0, le=1)
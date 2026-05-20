from pydantic import BaseModel
from typing import Optional, Any

class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    raw: Optional[dict[str, Any]] = None

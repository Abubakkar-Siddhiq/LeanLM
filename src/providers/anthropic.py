import os
import time
from schemas.llm import LLMResponse


class AnthropicProvider:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self._client = None
        if api_key:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=api_key)

    async def generate(self, model: str, messages: list) -> LLMResponse:
        if not self._client:
            raise ValueError("ANTHROPIC_API_KEY not set")
        start = time.monotonic()
        response = await self._client.messages.create(
            model=model,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
        )
        latency_ms = (time.monotonic() - start) * 1000

        content = "".join(block.text for block in response.content if block.type == "text")
        usage = response.usage
        raw = None
        try:
            raw = response.model_dump()
        except Exception:
            pass

        return LLMResponse(
            content=content,
            provider="anthropic",
            model=model,
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
            total_tokens=(usage.input_tokens + usage.output_tokens) if usage else None,
            latency_ms=latency_ms,
            raw=raw,
        )

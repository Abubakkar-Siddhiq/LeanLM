import os
import time
from schemas.llm import LLMResponse


class AnthropicProvider:
    async def generate(self, model: str, messages: list, api_key: str | None = None) -> LLMResponse:
        from config.settings import settings
        resolved_key = api_key
        if settings.ALLOW_ENV_PROVIDER_FALLBACK:
            resolved_key = resolved_key or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=resolved_key)
        start = time.monotonic()
        response = await client.messages.create(
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

import os
import time
from schemas.llm import LLMResponse


class GroqProvider:
    async def generate(self, model: str, messages: list, api_key: str | None = None) -> LLMResponse:
        from config.settings import settings
        resolved_key = api_key
        if settings.ALLOW_ENV_PROVIDER_FALLBACK:
            resolved_key = resolved_key or os.getenv("GROQ_API_KEY")
        if not resolved_key:
            raise ValueError("GROQ_API_KEY not set")
        from groq import Groq
        client = Groq(api_key=resolved_key)
        start = time.monotonic()
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        latency_ms = (time.monotonic() - start) * 1000

        content = completion.choices[0].message.content
        usage = completion.usage

        raw = None
        try:
            raw = completion.model_dump()
        except Exception:
            pass

        return LLMResponse(
            content=content,
            provider="groq",
            model=model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_ms=latency_ms,
            raw=raw,
        )

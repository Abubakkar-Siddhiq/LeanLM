import os
import time
from schemas.llm import LLMResponse


class OpenAIProvider:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self._client = None
        if api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=api_key)

    async def generate(self, model: str, messages: list) -> LLMResponse:
        if not self._client:
            raise ValueError("OPENAI_API_KEY not set")
        start = time.monotonic()
        completion = await self._client.chat.completions.create(
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
            provider="openai",
            model=model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_ms=latency_ms,
            raw=raw,
        )

import os
import time
import asyncio
from schemas.llm import LLMResponse


class GoogleProvider:
    async def generate(self, model: str, messages: list, api_key: str | None = None) -> LLMResponse:
        from config.settings import settings
        resolved_key = api_key
        if settings.ALLOW_ENV_PROVIDER_FALLBACK:
            resolved_key = resolved_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError("GEMINI_API_KEY not set")
        import google.generativeai as genai
        genai.configure(api_key=resolved_key)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_generate, model, messages)

    def _sync_generate(self, model_name: str, messages: list) -> LLMResponse:
        import google.generativeai as genai

        model = genai.GenerativeModel(model_name)

        combined = "\n".join(f"{m['role']}: {m['content']}" for m in messages)

        start = time.monotonic()
        response = model.generate_content(combined)
        latency_ms = (time.monotonic() - start) * 1000

        content = response.text
        usage = response.usage_metadata
        raw = None
        try:
            raw = type(response).to_dict(response)
        except Exception:
            pass

        return LLMResponse(
            content=content,
            provider="google",
            model=model_name,
            input_tokens=usage.prompt_token_count if usage else None,
            output_tokens=usage.candidates_token_count if usage else None,
            total_tokens=usage.total_token_count if usage else None,
            latency_ms=latency_ms,
            raw=raw,
        )

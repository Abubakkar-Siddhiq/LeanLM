import os
import time
import asyncio
from schemas.llm import LLMResponse


class GoogleProvider:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self._configured = False
        if api_key:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._configured = True

    async def generate(self, model: str, messages: list) -> LLMResponse:
        if not self._configured:
            raise ValueError("GEMINI_API_KEY not set")
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

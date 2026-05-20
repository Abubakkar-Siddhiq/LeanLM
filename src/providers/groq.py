import os
import time
from dotenv import load_dotenv
from groq import Groq
from schemas.llm import LLMResponse

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")

client = Groq(api_key=api_key)

class GroqProvider:
    def __init__(self):
        pass

    async def generate(self, model: str, messages: list) -> LLMResponse:
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
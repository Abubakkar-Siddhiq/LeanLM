from config.prompts import Prompts
from providers.groq import GroqProvider
import json


class IntentRouter:
    MODEL_MAP = {
        "low": "llama-3.1-8b-instant",
        "medium": "qwen/qwen3-32b",
        "high": "openai/gpt-oss-120b",
    }

    def __init__(self, llm_provider: GroqProvider, classify_model: str):
        self.llm_provider = llm_provider
        self.classify_model = classify_model

    async def classify(self, prompt: str) -> dict:
        user_prompt = prompt.lower()

        response = await self.llm_provider.generate(
            model=self.classify_model,
            messages=[{"role": "user", "content": Prompts.intent_detection(user_prompt)}]
        )
        print("Intent classification response:", response)
        return json.loads(response)

    def select_model(self, complexity: str) -> str:
        return self.MODEL_MAP[complexity]

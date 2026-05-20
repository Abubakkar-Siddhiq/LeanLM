from config.prompts import Prompts
from providers.groq import GroqProvider
import json
from schemas.classification import ClassificationResult
from config.models import MODEL_MAP, MEDIUM_MODEL
from schemas.routing import RouteDecision


class IntentClassifier:
    def __init__(self, llm_provider: GroqProvider, classify_model: str):
        self.llm_provider = llm_provider
        self.classify_model = classify_model

    async def classify(self, prompt: str) -> ClassificationResult:
        try:
            user_prompt = prompt.lower()

            response = await self.llm_provider.generate(
                model=self.classify_model,
                messages=[{"role": "user", "content": Prompts.intent_detection(user_prompt)}]
            )
            print("Intent classification response:", response)
            return ClassificationResult(**json.loads(response))
        except Exception as e:
            print(f"Error in classification: {e}")
            return ClassificationResult(
                complexity="medium",
                reason="classification_failed_fallback",
                confidence=0.0
            ) 

class ModelSelector:
    def select_model(self, intent: ClassificationResult) -> RouteDecision:
        model = MODEL_MAP.get(intent.complexity, MEDIUM_MODEL)

        return RouteDecision(
            provider="groq",
            model=model,
            complexity=intent.complexity,
            task_type=intent.task_type,
            reason=intent.reason,
            confidence=intent.confidence,
        )


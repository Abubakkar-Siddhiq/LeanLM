import json
from config.prompts import Prompts
from providers.groq import GroqProvider
from schemas.routing import RouteDecision
from schemas.classification import ClassificationResult
from config.routing import ROUTING_RULES, DEFAULT_MODEL_BY_COMPLEXITY, FALLBACK_MODEL_BY_COMPLEXITY


class IntentClassifier:
    def __init__(self, llm_provider: GroqProvider, classify_model: str):
        self.llm_provider = llm_provider
        self.classify_model = classify_model

    async def classify(self, prompt: str) -> ClassificationResult:
        try:
            user_prompt = prompt.lower()

            llm_response = await self.llm_provider.generate(
                model=self.classify_model,
                messages=[{"role": "user", "content": Prompts.intent_detection(user_prompt)}]
            )
            response = llm_response.content
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
    def select(self, intent: ClassificationResult) -> RouteDecision:
        model, routing_reason = self._select_model(intent)
        fallback_models = self._get_fallback_models(intent.complexity, model)

        return RouteDecision(
                provider="groq",
                model=model,
                task_type=intent.task_type,
                complexity=intent.complexity,
                classifier_reason=intent.reason,
                routing_reason=routing_reason,
                confidence=intent.confidence,
                fallback_models=fallback_models,
            )

    def _get_fallback_models(self, complexity: str, primary_model: str) -> list[str]:
        fallbacks = FALLBACK_MODEL_BY_COMPLEXITY.get(complexity, [])
        return [m for m in fallbacks if m != primary_model]

    def _select_model(self, intent: ClassificationResult) -> tuple[str, str]:
        for rule in ROUTING_RULES:
            if (
                intent.task_type in rule["task_types"]
                and intent.complexity in rule["complexities"]
            ):
                return rule["model"], rule["reason"]

        return (
            DEFAULT_MODEL_BY_COMPLEXITY.get(intent.complexity, DEFAULT_MODEL_BY_COMPLEXITY["medium"]),
            "Fallback model selected by complexity."
        )


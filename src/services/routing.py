import json
from config.prompts import Prompts
from providers.groq import GroqProvider
from schemas.routing import RouteDecision
from schemas.classification import ClassificationResult
from config.routing import (
    ROUTING_RULES,
    DEFAULT_MODEL_BY_COMPLEXITY,
    FALLBACK_MODEL_BY_COMPLEXITY,
    MODEL_TO_PROVIDER,
)


class IntentClassifier:
    def __init__(self, llm_provider: GroqProvider, classify_model: str):
        self.llm_provider = llm_provider
        self.classify_model = classify_model

    async def classify(self, prompt: str, api_key: str | None = None) -> ClassificationResult:
        try:
            user_prompt = prompt.lower()

            llm_response = await self.llm_provider.generate(
                model=self.classify_model,
                messages=[{"role": "user", "content": Prompts.intent_detection(user_prompt)}],
                api_key=api_key,
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
    def select(self, intent: ClassificationResult, available_providers: list[str] | None = None) -> RouteDecision:
        provider, model, routing_reason = self._select_model(intent, available_providers)
        fallback_models = self._get_fallback_models(intent.complexity, model, provider, available_providers)

        return RouteDecision(
                provider=provider,
                model=model,
                task_type=intent.task_type,
                complexity=intent.complexity,
                classifier_reason=intent.reason,
                routing_reason=routing_reason,
                confidence=intent.confidence,
                fallback_models=fallback_models,
            )

    def _get_fallback_models(self, complexity: str, primary_model: str, primary_provider: str, available_providers: list[str] | None = None) -> list[str]:
        avail = available_providers or []
        fallbacks = FALLBACK_MODEL_BY_COMPLEXITY.get(complexity, [])
        return [
            m for m in fallbacks
            if m != primary_model
            and MODEL_TO_PROVIDER.get(m) == primary_provider
            and (not avail or MODEL_TO_PROVIDER.get(m) in avail)
        ]

    def _select_model(self, intent: ClassificationResult, available_providers: list[str] | None = None) -> tuple[str, str, str]:
        avail = available_providers or []

        for rule in ROUTING_RULES:
            if (
                intent.task_type in rule["task_types"]
                and intent.complexity in rule["complexities"]
                and (not avail or rule["provider"] in avail)
            ):
                return rule["provider"], rule["model"], rule["reason"]

        model = DEFAULT_MODEL_BY_COMPLEXITY.get(intent.complexity, DEFAULT_MODEL_BY_COMPLEXITY["medium"])
        provider = MODEL_TO_PROVIDER.get(model, "groq")

        if avail and provider not in avail:
            model = self._find_available_default(intent.complexity, avail)
            provider = MODEL_TO_PROVIDER.get(model, "groq")

        return provider, model, "Fallback model selected by complexity."

    def _find_available_default(self, complexity: str, available_providers: list[str]) -> str:
        for model in FALLBACK_MODEL_BY_COMPLEXITY.get(complexity, []):
            if MODEL_TO_PROVIDER.get(model) in available_providers:
                return model
        raise ValueError(
            f"No available model for complexity {complexity} with providers {available_providers}"
        )


from providers.groq import GroqProvider
import json

class ChatService:    
    MODEL_MAP = {
        "low": "llama-3.1-8b-instant",
        "medium": "qwen/qwen3-32b",
        "high": "openai/gpt-oss-120b",
    }

    def __init__(self):
        self.llm_provider = GroqProvider()

    async def find_intent(self, prompt: str) -> dict:
        user_prompt = prompt.lower()

        response = await self.llm_provider.generate(
            model="llama-3.1-8b-instant",
            prompt=f"""You are an intent classifier for an AI routing system called Routiq.
                Your only job is to classify the complexity of a user's prompt
                so it can be routed to the most cost-efficient LLM.

                Classify into exactly one of three tiers:

                - low    → Simple, factual, conversational. No reasoning required.
                        Examples: greetings, yes/no questions, definitions,
                        unit conversions, "what is X", single-line completions.

                - medium → Moderate effort. Some reasoning or generation required.
                        Examples: summarization, code explanation, short essays,
                        data extraction, rewriting text, step-by-step how-tos.

                - high   → Complex, multi-step, or expert-level.
                        Examples: system design, debugging complex code,
                        long-form generation, multi-constraint reasoning,
                        architecture decisions, research synthesis.

                Rules:
                1. When uncertain between two tiers, pick the lower one.
                2. Ignore politeness or filler words — classify the core task only.
                3. If the prompt contains code or technical context, weight toward medium or high.
                4. A long prompt is not automatically high — classify by task complexity, not length.
                5. Requests involving architecture, debugging, optimization, implementation from scratch, or deep reasoning should usually be classified as high.
                6. Coding tasks are not automatically high. Small fixes or explanations are usually medium.
                Respond with a single JSON object and nothing else.
                No explanation. No markdown. No preamble.
                Return valid parsable JSON only.
                Do not wrap in markdown fences.

                Format:
                    {{
                        "complexity": "low" | "medium" | "high",
                        "confidence": "high" | "medium" | "low",
                        "reason": "one sentence max"
                    }}

                User prompt: {user_prompt}
            """
        )
        print("Intent classification response:", response)
        return response


    
    def select_model(self, complexity: str):
        return self.MODEL_MAP[complexity]
    
    async def chat(self, prompt: str):
        intent_response = await self.find_intent(prompt)
        intent = json.loads(intent_response)

        model = self.select_model(intent["complexity"])
        response = await self.llm_provider.generate(model=model, prompt=prompt)
        
        return {
            "intent": intent["complexity"],
            "reason": intent["reason"],
            "confidence": intent["confidence"],
            "model": model,
            "response": response,
        }
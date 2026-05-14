from providers.groq import GroqProvider

class ChatService:    
    MODEL_MAP = {
        "low": "llama-3.1-8b-instant",
        "medium": "qwen/qwen3-32b",
        "high": "openai/gpt-oss-120b",
    }

    def __init__(self):
        self.llm_provider = GroqProvider()

    def find_intent(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()

        coding_keywords = [
            "code",
            "bug",
            "fix",
            "function",
            "class",
            "api",
            "fastapi",
            "react",
            "python",
            "javascript",
            "write",
        ]

        reasoning_keywords = [
            "design",
            "architecture",
            "strategy",
            "optimize",
            "compare",
            "analyze",
            "brainstorm",
        ]

        coding = any(word in prompt_lower for word in coding_keywords)
        reasoning = any(word in prompt_lower for word in reasoning_keywords)

        word_count = len(prompt.split())

        if reasoning or word_count > 120:
            complexity = "high"
        elif coding or word_count > 40:
            complexity = "medium"
        else:
            complexity = "low"

        return {
            "complexity": complexity,
            "coding": coding,
            "reasoning": reasoning,
        }
    
    def select_model(self, complexity: str):
        return self.MODEL_MAP[complexity]
    
    async def chat(self, prompt: str):
        intent = self.find_intent(prompt)
        model = self.select_model(intent["complexity"])
        response = await self.llm_provider.generate(model=model, prompt=prompt)
        return {
            "intent": intent,
            "model": model,
            "response": response,
        }
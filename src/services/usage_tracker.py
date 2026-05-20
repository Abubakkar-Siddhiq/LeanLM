class UsageTracker:
    def estimate_tokens(self, messages: list[dict[str, str]]) -> int:
        return sum(len(m["content"].split()) for m in messages)

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int = 0) -> float:
        # temporary placeholder until real provider usage metadata
        return 0.0
import tiktoken


class ContextBuilder:
    def __init__(self, max_tokens=6000):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = max_tokens

    def count(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def score_message(self, msg: dict) -> int:
        content = msg["content"].lower()

        score = 0

        # 1. user messages slightly more important
        if msg["role"] == "user":
            score += 3

        # 2. code / technical content
        if "```" in content or "code" in content:
            score += 5

        # 3. questions are important
        if "?" in content:
            score += 2

        # 4. long messages usually carry context
        if len(content) > 200:
            score += 2

        # 5. keywords for memory / decisions
        keywords = ["remember", "important", "note", "decide", "plan"]
        if any(k in content for k in keywords):
            score += 5

        return score

    def build(self, system_prompt, summary, messages):
        context = []
        selected = []
        used = 0
        reserved_tokens = 1000 # For res. and user input.
        limit = self.max_tokens - reserved_tokens

        # system
        context.append({"role": "system", "content": system_prompt})
        used += self.count(system_prompt)

        # summary
        if summary:
            summary_text = f"Summary:\n{summary}"
            context.append({"role": "system", "content": summary_text})
            used += self.count(summary_text)

        # scoring
        scored_messages = [(self.score_message(msg), msg) for msg in messages]
        scored_messages.sort(key=lambda x: x[0], reverse=True)

        for _, msg in scored_messages:
            tokens = self.count(msg["content"])

            if used + tokens > limit:
                continue

            selected.append(msg)
            used += tokens

        # restore order
        selected.sort(key=lambda m: messages.index(m))

        context.extend(selected)
        return context
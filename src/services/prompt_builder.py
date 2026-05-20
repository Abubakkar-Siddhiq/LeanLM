from db.models import Message

class ChatPromptBuilder:
    def build(
        self,
        system_prompt: str,
        summary: str,
        messages: list[dict],
        relevant_messages: list[Message],
    ) -> list[dict[str, str]]:
        
        context = []

        context.append({
            "role": "system",
            "content": system_prompt
        })

        if summary:
            context.append({
                "role": "system",
                "content": f"Conversation summary:\n{summary}"
            })

        if relevant_messages:
            relevant_context = "\n".join([
                f"{m.role}: {m.content}"
                for m in relevant_messages
            ])

            context.append({
                "role": "system",
                "content": f"Relevant past conversation context:\n{relevant_context}"
            })

        context.extend(messages)

        return context

class Summarizer:
    async def summarize(self, provider, model, messages):
        text = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in messages
        )

        prompt = f"""
                    Summarize the conversation.

                    Keep:
                    - user facts
                    - preferences
                    - ongoing tasks

                    Conversation:
                    {text}
                """

        return await provider.generate(
            model=model,
            prompt=prompt
        )
    
    def should_summarize(
        self,
        conversation,
        messages,
        context_tokens: int
    ):

        # how many NEW messages since last summary
        new_messages_since_summary = (
            conversation.message_count
            - conversation.last_summarized_at_count
        )

        # not enough new information yet
        if new_messages_since_summary < 15:
            return False

        # context pressure still low
        if context_tokens < 4500:
            return False

        # not enough history to summarize meaningfully
        if len(messages) < 20:
            return False

        return True
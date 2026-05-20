from db.models import Conversation, Message
from sqlmodel import select

class Summarizer:
    async def summarize(self, provider, model, messages):
        text = "\n".join(
            f"{m.role}: {m.content}"
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

        result = await provider.generate(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return result.content

    async def run_summarization(self, conversation_id, session, llm_provider, local_model):
        try:
            conversation = session.get(
                Conversation,
                conversation_id
            )

            messages = session.exec(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            ).all()

            # keep latest 10 messages
            old_messages = messages[:-10]

            if not old_messages:
                return

            summary = await self.summarize(
                llm_provider,
                local_model,
                old_messages
            )

            conversation.summary = (
                (conversation.summary or "")
                + "\n"
                + summary
            )

            conversation.last_summarized_at_count = (
                conversation.message_count
            )

            session.add(conversation)

            # delete compressed messages
            for msg in old_messages:
                session.delete(msg)

            session.commit()

        except Exception as e:
            print(f"Summarization failed for conversation {conversation_id}: {e}")
        finally:
            session.close()

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
        # if context_tokens < 4500:
        #     return False

        # not enough history to summarize meaningfully
        if len(messages) < 20:
            return False

        return True

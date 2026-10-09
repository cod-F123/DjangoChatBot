from django.conf import settings
from django.db import transaction
from asgiref.sync import sync_to_async
from chatbot.models import ConversationSummary, Message, Conversation


RECENT_MESSAGES_TO_KEEP = settings.AI_CONFIG.get("RECENT_MESSAGES_TO_KEEP")
SUMMARIZER_LLM_MODEL = "openai/gpt-oss-20b"

SUMMARY_PROMPT = """
Create an updated summary of the conversation.

Preserve important information such as:
- user preferences
- important facts
- decisions
- goals
- unresolved questions
- technical details
- important context

Do not invent information.
Do not include unnecessary conversational filler.

Return only the updated summary.
"""


class Summarizer:

    def __init__(self, conversation: Conversation, llm):

        self.conversation = conversation
        self.llm = llm

    @sync_to_async
    def get_messages_to_summarize(self):

        last_summary = (
            self.conversation.summaries
            .order_by("-created_at")
            .first()
        )

        summarised_util_id = (
            last_summary.summarized_until_message.id
            if last_summary else 0
        )

        messages = list(
            self.conversation.messages.filter(
                id__gt=summarised_util_id,
                message_role__in=["user", "assistant"]
            )
        )

        if len(messages) <= 10:
            return []

        return messages[:-10]

    @sync_to_async
    def get_latest_summary(self):
        return (
            self.conversation.summaries
            .order_by("-created_at")
            .first()
        )

    @sync_to_async
    def save_summary(self, summary, summarized_until_message):

        return ConversationSummary.objects.create(
            conversation=self.conversation,
            summary=summary,
            summarized_until_message=summarized_until_message,
        )

    def build_prompt(self, latest_summary, messages):

        parts = []

        if latest_summary:
            parts.append(f"Previous conversation summary:\n"
                         f"{latest_summary.summary}")

        parts.append("New conversation messages:")

        for message in messages:

            parts.append(
                f"{message.message_role} : {message.content}"
            )

        parts.append(SUMMARY_PROMPT)

        return "\n\n".join(parts)

    async def generate_summary(self, prompt):

        response = await self.llm.chat.completions.create(
            model=SUMMARIZER_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a conversation summarization system."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            stream=False,
        )

        return response.choices[0].message.content

    async def summarize(self):

        latest_summary = await self.get_latest_summary()

        messages = await self.get_messages_to_summarize()

        if not messages:
            return None

        prompt = self.build_prompt(
            latest_summary,
            messages,
        )

        summary = await self.generate_summary(prompt)

        await self.save_summary(
            summary=summary,
            summarized_until_message=messages[-1],
        )

        return summary

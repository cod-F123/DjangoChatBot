from django.conf import settings
from asgiref.sync import sync_to_async
from chatbot.models import ConversationSummary, Conversation
from chatbot.services.attachment_service import AttachmentService


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
        self.attachment_service = AttachmentService()

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
            self.conversation.messages.prefetch_related("attachments").filter(
                id__gt=summarised_util_id,
                message_role__in=["user", "assistant"]
            ).order_by("id")
        )

        if len(messages) <= RECENT_MESSAGES_TO_KEEP:
            return []

        return messages[:-RECENT_MESSAGES_TO_KEEP]

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

            content = message.content

            # Add attachment text in content
            for attachment in message.attachments.all():

                extracted_text = self.attachment_service.extract_text(
                    attachment)

                if extracted_text:

                    content += (
                        "\n\n"
                        f"[محتوای فایل: {attachment.original_name}]\n"
                        f"{extracted_text}"
                    )

            parts.append(
                f"{message.message_role} : {content}"
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

        if not summary or not summary.strip():
            return None

        await self.save_summary(
            summary=summary.strip(),
            summarized_until_message=messages[-1],
        )

        return summary.strip()

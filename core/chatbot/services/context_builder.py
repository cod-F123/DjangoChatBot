from chatbot.models import Message, Conversation, ConversationSummary
from chatbot.services.attachment_service import AttachmentService


class ContextBuilder:

    def __init__(self, conversation: Conversation):

        self.conversation = conversation

    def build(self):
        context = []

        latest_summary: ConversationSummary | None = (
            self.conversation.summaries
            .order_by("-created_at")
            .first()
        )

        messages = self.conversation.messages.all()

        if latest_summary:
            context.append({
                "role": "system",
                "content": latest_summary.summary,
            })

            messages = messages.filter(
                id__gt=latest_summary.summarized_until_message.id
            )

        messages = (
            messages
            .prefetch_related("attachments")
            .order_by("id")
        )

        for message in messages:

            content = message.content

            for attachment in message.attachments.all():
                extracted_text = AttachmentService.extract_text(
                    attachment
                )

                if extracted_text:
                    content += (
                        "\n\n"
                        f"[محتوای فایل: {attachment.original_name}]\n"
                        f"{extracted_text}"
                    )

            context.append({
                "role": message.message_role,
                "content": content,
            })

        return context

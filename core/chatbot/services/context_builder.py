from chatbot.models import Message, Conversation, ConversationSummary


class ContextBuilder:

    def __init__(self, conversation: Conversation):

        self.conversation = conversation

    def build(self):

        context = []

        conversation_context: ConversationSummary = self.conversation.summaries.all(
        ).order_by("-created_at").first()

        if conversation_context:

            context.append({
                "role": "system",
                "content": conversation_context.summary
            })

            conversation_messages: list[Message] = self.conversation.messages.filter(
                id__gt=conversation_context.summarized_until_message.id
            ).order_by("created_at")

        else:

            conversation_messages: list[Message] = self.conversation.messages.all(
            ).order_by("created_at")

        context.extend({"role": m.message_role, "content": m.content}
                       for m in conversation_messages)

        return context

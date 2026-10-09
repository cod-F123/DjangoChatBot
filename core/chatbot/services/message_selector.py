from dataclasses import dataclass

from chatbot.models import Message
from chatbot.services.token_counter import TokenCounter


@dataclass
class MessageSelection:

    messages_to_summarize: list[Message]
    recent_messages: list[Message]


class MessageSelector:

    def __init__(self, token_counter: TokenCounter, summary_target_tokens: int, recent_messages_tokens: int):

        self.token_counter = token_counter
        self.summary_target_tokens = summary_target_tokens
        self.recent_messages_tokens = recent_messages_tokens

    def select(self, messages: list[Message]) -> MessageSelection:

        if not messages:
            return MessageSelection(
                messages_to_summarize=[],
                recent_messages=[]
            )

        messages_to_summarize = []
        recent_messages = []

        current_recent_tokens = 0

        for message in reversed(messages):

            message_tokens = self.token_counter.count_text(message.content)

            if current_recent_tokens + message_tokens <= self.recent_messages_tokens:

                recent_messages.append(
                    message
                )

                current_recent_tokens += message_tokens

            else:
                break

        recent_ids = {
            message.id for message in recent_messages
        }

        summary_tokens = 0

        for message in messages:

            if message.id in recent_ids:
                break

            tokens = self.token_counter.count_text(message.content)

            if summary_tokens + tokens > self.summary_target_tokens:
                break

            messages_to_summarize.append(message)
            summary_tokens += tokens

        # Reversed to before
        recent_messages.reverse()

        return MessageSelection(
            messages_to_summarize=messages_to_summarize,
            recent_messages=recent_messages
        )

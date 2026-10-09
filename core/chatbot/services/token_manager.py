import logging

from django.conf import settings

from chatbot.services.token_counter import TokenCounter


logger = logging.getLogger(__name__)

AI_CONFIG = settings.AI_CONFIG
CHATBOT_MAX_CONTEXT_TOKENS = AI_CONFIG.get("CHATBOT_MAX_CONTEXT_TOKENS")
CHATBOT_SUMMARY_TRIGGER_RATIO = AI_CONFIG.get("CHATBOT_SUMMARY_TRIGGER_RATIO")


class TokenManager:

    def __init__(self):

        self.counter = TokenCounter()

        self.max_tokens = CHATBOT_MAX_CONTEXT_TOKENS

        self.trigger_tokens = int(
            self.max_tokens
            * CHATBOT_SUMMARY_TRIGGER_RATIO
        )

    def count(self, messages):
        return self.counter.count_messages(messages)

    def needs_summary(self, messages):

        token_count = self.count(messages)

        return token_count >= self.trigger_tokens

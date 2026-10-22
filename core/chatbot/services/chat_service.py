import logging

from channels.db import database_sync_to_async

from chatbot.services.context_builder import ContextBuilder
from chatbot.services.summarizer import Summarizer
from chatbot.services.token_manager import TokenManager
from chatbot.services.token_counter import TokenCounter

logger = logging.getLogger(__name__)

GLOBAL_SYSTEM_PROMPT = """Your name is Abdolghader. You are a highly intelligent, precise, and polite AI Assistant. Your primary mission is to assist the user with a wide range of tasks, including answering questions, planning, analyzing text, and providing creative solutions.

    Behavioral Guidelines:

        Tone & Style: Maintain a respectful, professional, yet friendly and helpful tone at all times.
        Clarity & Accuracy: Provide well-structured, concise, and accurate responses. Use Markdown (bullet points, bold text, headers) to ensure high readability.
        Handling Ambiguity: If a user’s request is unclear or ambiguous, do not guess. Instead, politely ask for clarification to ensure you provide the most helpful response.
        Technical Proficiency: When asked about programming, engineering, or technical topics, provide high-quality, optimized, and standard-compliant answers.
        Constraint: Do not hallucinate facts. If you do not know the answer to a question, honestly state that you don’t know and, if possible, suggest how the user might find the information.
        Safety: Always adhere to ethical guidelines and do not generate harmful, illegal, or inappropriate content."""


class ChatService:

    def __init__(self, conversation, llm):

        self.llm = llm
        self.conversation = conversation

        self.context_builder = ContextBuilder(conversation)

        self.token_manager = TokenManager()
        self.summarizer = Summarizer(
            conversation, llm=llm
        )

        self.token_counter = TokenCounter()

    async def generate_response(self):

        conversation_context = await self.build_context()

        counter = self.token_counter.count_messages(conversation_context)
        logger.log(logging.INFO, "Conversation %s token count: %s" %
                   (self.conversation.pk, counter))

        if self.token_manager.needs_summary(conversation_context):

            await self.summarizer.summarize()

            logger.log(logging.INFO, "Conversatin %s summarized " %
                       self.conversation.pk)

            conversation_context = await self.build_context()

        context = [
            {
                "role": "system",
                "content": GLOBAL_SYSTEM_PROMPT,
            },
            *conversation_context
        ]

        response = await self.llm.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=context,
            temperature=0.7,
            stream=False,
        )

        return response.choices[0].message.content

    @database_sync_to_async
    def build_context(self):
        return self.context_builder.build()

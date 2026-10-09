from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from chatbot.models import Conversation, Message

from openai import AsyncOpenAI

from chatbot.services.chat_service import ChatService

from asgiref.sync import AsyncToSync


import logging

logger = logging.getLogger(__name__)


AI_CONFIG = settings.AI_CONFIG

API_KEY = AI_CONFIG.get("API_KEY")
API_BASE_URL = AI_CONFIG.get("API_BASE_URL")
CHATBOT_MAX_CONTEXT_TOKENS = AI_CONFIG.get("CHATBOT_MAX_CONTEXT_TOKENS")

GLOBAL_SYSTEM_PROMPT = """Your name is Abdolghader. You are a highly intelligent, precise, and polite AI Assistant. Your primary mission is to assist the user with a wide range of tasks, including answering questions, planning, analyzing text, and providing creative solutions.

    Behavioral Guidelines:

        Tone & Style: Maintain a respectful, professional, yet friendly and helpful tone at all times.
        Clarity & Accuracy: Provide well-structured, concise, and accurate responses. Use Markdown (bullet points, bold text, headers) to ensure high readability.
        Handling Ambiguity: If a user’s request is unclear or ambiguous, do not guess. Instead, politely ask for clarification to ensure you provide the most helpful response.
        Technical Proficiency: When asked about programming, engineering, or technical topics, provide high-quality, optimized, and standard-compliant answers.
        Constraint: Do not hallucinate facts. If you do not know the answer to a question, honestly state that you don’t know and, if possible, suggest how the user might find the information.
        Safety: Always adhere to ethical guidelines and do not generate harmful, illegal, or inappropriate content."""


class ChatBotConsumer(AsyncConsumer):

    async def websocket_connect(self, event):

        self.c_id = self.scope["url_route"]["kwargs"].get("c_id")
        self.user = self.scope["user"]

        self.conversation = await self.get_conversation()

        if self.conversation:

            # Connect to LLM With OpenAI SDK

            self.llm = AsyncOpenAI(
                api_key=API_KEY,
                base_url=API_BASE_URL
            )

            self.chat_service = ChatService(self.conversation,  llm=self.llm)

            await self.send({
                "type": "websocket.accept",
            })

    async def websocket_disconnect(self, event):

        raise StopConsumer()

    async def websocket_receive(self, event):

        text_message = event.get("text")

        user_message = await self.create_message(text_message, "user")

        ai_answer = await self.chat_service.generate_response()

        if ai_answer:

            ai_message = await self.create_message(ai_answer, "assistant")

            await self.send({
                "type": "websocket.send",
                "text": ai_message.content
            })

    @database_sync_to_async
    def get_conversation(self):

        return Conversation.objects.filter(converstation_id=self.c_id, user=self.user).first()

    @database_sync_to_async
    def create_message(self, content, role):
        return Message.objects.create(Conversation=self.conversation, content=content, message_role=role)

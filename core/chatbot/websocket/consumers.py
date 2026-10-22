from channels.consumer import AsyncConsumer
from channels.exceptions import StopConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from django.db import transaction
from chatbot.models import Conversation, Message, MessageAttachment

from openai import AsyncOpenAI

from chatbot.services.chat_service import ChatService

from asgiref.sync import AsyncToSync
import json


import logging
import uuid

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

        else:

            await self.send({
                "type": "websocket.close"
            })

    async def websocket_disconnect(self, event):

        raise StopConsumer()

    async def websocket_receive(self, event):

        try:
            data = json.loads(event.get("text", "{}"))

            if not isinstance(data, dict):
                raise ValueError("Invalid message format.")

            content = data.get("text", "")
            attachment_ids = data.get("attachments", [])

            if not isinstance(content, str):
                raise ValueError("Message text must be a string.")

            if not isinstance(attachment_ids, list):
                raise ValueError("Attachments must be a list.")

            if not content.strip() and not attachment_ids:
                raise ValueError("Message cannot be empty.")

            user_message = await self.create_message_with_attachments(
                content=content,
                role="user",
                attachment_ids=attachment_ids,
            )

        except (json.JSONDecodeError, ValueError) as exc:
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({
                    "type": "error",
                    "message": str(exc),
                }),
            })
            return

        try:
            ai_answer = await self.chat_service.generate_response()

            if ai_answer:
                ai_message = await self.create_message_with_attachments(
                    content=ai_answer,
                    role="assistant",
                    attachment_ids=[],
                )

                await self.send({
                    "type": "websocket.send",
                    "text": json.dumps({
                        "type": "message",
                        "message": ai_message.content,
                    }),
                })

        except Exception:
            logger.exception("Error generating AI response")

            await self.send({
                "type": "websocket.send",
                "text": json.dumps({
                    "type": "error",
                    "message": "خطا در ارتباط با مدل زبانی",
                }),
            })

    @database_sync_to_async
    def get_conversation(self):

        return Conversation.objects.prefetch_related("messages").prefetch_related("summaries").filter(converstation_id=self.c_id, user=self.user).first()

    @database_sync_to_async
    def create_message_with_attachments(self, content, role, attachment_ids):
        if not isinstance(attachment_ids, list):
            raise ValueError("Attachments must be a list.")

        if len(attachment_ids) > 10:
            raise ValueError("Too many attachments.")

        # Validate UUIDs and remove duplicates.
        try:
            attachment_ids = list(
                dict.fromkeys(uuid.UUID(str(item)) for item in attachment_ids)
            )
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Invalid attachment ID.")

        with transaction.atomic():
            message = Message.objects.create(
                Conversation=self.conversation,
                content=content,
                message_role=role,
            )

            if attachment_ids:
                attachments = list(
                    MessageAttachment.objects.select_for_update().filter(
                        id__in=attachment_ids,
                        conversation=self.conversation,
                        source=role,
                        uploaded_by=self.user,
                        message__isnull=True,
                    )
                )

                if len(attachments) != len(attachment_ids):
                    raise ValueError(
                        "Some attachments are invalid or unavailable."
                    )

                MessageAttachment.objects.filter(
                    id__in=[attachment.id for attachment in attachments]
                ).update(message=message)

        return message

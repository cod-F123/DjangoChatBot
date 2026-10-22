from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

# Create your models here.


class Conversation(models.Model):

    converstation_id = models.CharField(
        max_length=121, unique=True,  blank=True, null=True)
    title = models.CharField(max_length=121, default="New Conversation")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversations")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):

        if not self.converstation_id:
            self.converstation_id = "C-" + \
                str(uuid.uuid4()).replace("-", "")[:13]

        super().save(*args, **kwargs)


class Message(models.Model):

    MESSAGE_ROLES = (
        ("user", "user"),
        ("system", "system"),
        ("assistant", "assistant")
    )

    Conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages")

    message_role = models.CharField(
        max_length=13, choices=MESSAGE_ROLES, default="user")

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ConversationSummary(models.Model):

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="summaries"
    )

    summary = models.TextField()

    summarized_until_message = models.ForeignKey(
        Message, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)


class MessageAttachment(models.Model):

    class Source(models.TextChoices):
        USER = "user", "user"
        ASSISTANT = "assistant", "assistant"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="attachments"
    )

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments", blank=True, null=True
    )

    source = models.CharField(
        max_length=10,
        choices=Source.choices,
    )

    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="chat_attachments"
    )

    file = models.FileField(
        upload_to="chat_attachments/%Y/%m/",
    )

    # content = models.TextField(blank=True, null=True)

    original_name = models.CharField(max_length=255)

    mime_type = models.CharField(max_length=100)

    size = models.PositiveBigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name

from rest_framework import serializers
from pathlib import Path
from chatbot.models import Conversation, Message, MessageAttachment


MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/plain",
    "application/pdf",
}


class MessageAttachmentSerializer(serializers.ModelSerializer):

    def validate(self, attrs):

        validated_data = super().validate(attrs)

        user = self.context.get("request").user

        if validated_data.get("conversation").user.id != user.id:
            raise serializers.ValidationError(
                "You do not have access to this conversation.", code="conversation")

        return validated_data

    def validate_file(self, uploaded_file):
        if uploaded_file.size > MAX_ATTACHMENT_SIZE:
            raise serializers.ValidationError(
                "Maximum file size is 10 MB."
            )

        extension = Path(uploaded_file.name).suffix.lower()

        # The browser-supplied MIME type is not trustworthy by itself.
        # Validate the actual file content before production use.
        if uploaded_file.content_type not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                "This file type is not supported."
            )

        return uploaded_file

    def create(self, validated_data):
        uploaded_file = validated_data["file"]

        validated_data["uploaded_by"] = self.context["request"].user
        validated_data["source"] = MessageAttachment.Source.USER
        validated_data["original_name"] = uploaded_file.name
        validated_data["mime_type"] = uploaded_file.content_type
        validated_data["size"] = uploaded_file.size

        return super().create(validated_data)

    class Meta:
        model = MessageAttachment
        fields = ["id", "conversation", "message", "source", "uploaded_by",
                  "file", "original_name", "mime_type", "size", "created_at"]

        read_only_fields = ["id", "source",
                            "message", "created_at", "uploaded_by"]


class MessageSerializer(serializers.ModelSerializer):

    attachments = MessageAttachmentSerializer(read_only=True, many=True)

    class Meta:

        model = Message
        fields = ["id", "message_role", "content",
                  "attachments", "created_at", "updated_at"]


class CoversationSerializer(serializers.ModelSerializer):

    messages = MessageSerializer(read_only=True, many=True)
    message = serializers.CharField(required=False)

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        request = self.context.get("request")

        if not request.parser_context.get("kwargs").get("c_id"):

            rep.pop("messages")

        return rep

    def validate(self, attrs):
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data["user"] = self.context.get("request").user

        message = validated_data.get("message")

        if not message:

            c = super().create(validated_data)
            return c

        validated_data.pop("message")

        c = super().create(validated_data)

        Message.objects.create(message_role="user",
                               content=message, Conversation=c)

        return c

    class Meta:

        model = Conversation
        fields = ["id", "converstation_id", "title",
                  "messages", "created_at", "updated_at", "message"]

        read_only_fields = ["id", "converstation_id",
                            "created_at", "updated_at"]

from rest_framework import serializers
from chatbot.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):

    class Meta:

        model = Message
        fields = ["id", "message_role", "content", "created_at", "updated_at"]


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

        print(validated_data)

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
        fields = ["converstation_id", "title",
                  "messages", "created_at", "updated_at", "message"]

        read_only_fields = ["converstation_id", "created_at", "updated_at"]

from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from chatbot.models import Conversation, MessageAttachment
from .serializers import CoversationSerializer, MessageAttachmentSerializer


class ConversationViewSet(ModelViewSet):

    permission_classes = [IsAuthenticated,]

    serializer_class = CoversationSerializer

    lookup_url_kwarg = "c_id"
    lookup_field = "converstation_id"

    def get_queryset(self):
        return Conversation.objects.prefetch_related("messages").filter(user=self.request.user)


class MessageAttachmentsApiView(CreateAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = MessageAttachmentSerializer
    queryset = MessageAttachment.objects.all()

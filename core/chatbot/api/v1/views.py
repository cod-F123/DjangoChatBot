from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from chatbot.models import Conversation
from .serializers import CoversationSerializer


class ConversationViewSet(ModelViewSet):

    permission_classes = [IsAuthenticated,]

    serializer_class = CoversationSerializer

    queryset = Conversation.objects.prefetch_related("messages").all()

    lookup_url_kwarg = "c_id"
    lookup_field = "converstation_id"

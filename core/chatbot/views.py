from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Conversation

# Create your views here.


# def chat_view(request):
#     return render(request, "chatbot/chatbot.html", {})


# def chat_detail_view(request, c_id):

#     c = get_object_or_404(Conversation, converstation_id=c_id)
#     return render(request, "chatbot/chat_detail.html", {})


class ChatView(LoginRequiredMixin, TemplateView):
    template_name = "chatbot/chatbot.html"


class ChatDetailView(LoginRequiredMixin, DetailView):

    template_name = "chatbot/chat_detail.html"
    slug_url_kwarg = "c_id"
    slug_field = "converstation_id"
    context_object_name = "c"

    def get_queryset(self):
        return Conversation.objects.prefetch_related("messages").filter(user=self.request.user)

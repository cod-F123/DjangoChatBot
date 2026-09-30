from django.urls import path, include
from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.ChatView.as_view(), name="chat-bot"),
    path("<str:c_id>/", views.ChatDetailView.as_view(), name="chat-detail"),

    path("api/v1/", include("chatbot.api.v1.urls"), name="chatbot-api-v1")
]

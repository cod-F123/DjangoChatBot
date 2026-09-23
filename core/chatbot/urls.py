from django.urls import path
from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chat_view, name="chat-bot"),
    path("<str:chat_id>/", views.chat_detail_view, name="chat-detail")
]

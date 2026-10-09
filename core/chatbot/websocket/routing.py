from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:c_id>/', consumers.ChatBotConsumer.as_asgi()),
]

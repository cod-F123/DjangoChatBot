from django.shortcuts import render
from django.contrib.auth.views import LoginView

# Create your views here.


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    success_url = "chatbot:chat-bot"

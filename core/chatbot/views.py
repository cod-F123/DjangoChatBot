from django.shortcuts import render

# Create your views here.


def chat_view(request):
    return render(request, "chatbot/chatbot.html", {})


def chat_detail_view(request):
    return render(request, "chatbot/chat_detail.html", {})

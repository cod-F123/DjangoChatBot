from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = "api-v1"


router = DefaultRouter()
router.register("conversation", views.ConversationViewSet, "conversation")

urlpatterns = [
    path("files/", views.MessageAttachmentsApiView.as_view(), name="attachemtns-api"),
]

urlpatterns += router.urls

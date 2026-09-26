from django.contrib import admin
from .models import Conversation, Message, ConversationSummary

# Register your models here.


class MessageAdminInline(admin.StackedInline):
    model = Message
    extra = 1

    show_change_link = True


class CoverstationSummaryAdminInline(admin.StackedInline):
    model = ConversationSummary
    extra = 0

    show_change_link = True


@admin.register(Conversation)
class ConverstationAdmin(admin.ModelAdmin):

    list_display = ["converstation_id", "user__email", "title", "created_at"]

    search_fields = ["converstation_id", "user__email", "title"]

    readonly_fields = ["converstation_id", "created_at", "updated_at"]

    inlines = [MessageAdminInline, CoverstationSummaryAdminInline]

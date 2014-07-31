from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import *
from .models import Sms
from .utils import VumiSmsApi


class PageAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description"]})
    ]


class PostAdmin(SummernoteModelAdmin):
    list_display = ("name", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "course", "publishdate"]}),
        ("Content",
            {"fields": ["big_image", "small_image", "moderated", "content"]})
    ]


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("author", "content", "publishdate")
    ordering = ("publishdate",)

    def has_add_permission(self, request):
        return False


class ChatGroupAdmin(SummernoteModelAdmin):
    list_display = ("name", "course", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description", "course"]})
    ]
    inlines = (ChatMessageInline, )


class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("course", "module", "question", "author", "publishdate",
                    "content", "moderated")
    list_filter = ("course", "module", "question", "moderated")
    search_fields = ("author", "content")
    fieldsets = [
        (None,
            {"fields": ["name", "description"]}),
        ("Content",
            {"fields": ["content", "author", "publishdate", "moderated"]}),
        ("Discussion Group",
            {"fields": ["course", "module", "question", "response"]})
    ]


class MessageAdmin(SummernoteModelAdmin):
    list_display = ("name", "course", "author", "direction", "publishdate")
    list_filter = ("course", "direction")
    search_fields = ("name", "author")
    fieldsets = [
        (None,
            {"fields": ["name", "course", "author", "direction",
                        "publishdate"]}),
        ("Content",
            {"fields": ["content"]})
    ]


class SmsAdmin(SummernoteModelAdmin):
    list_display = ("msisdn", "date_sent", "message")


# Communication
admin.site.register(Sms, SmsAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ChatGroup, ChatGroupAdmin)
admin.site.register(Discussion, DiscussionAdmin)

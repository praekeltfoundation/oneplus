from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import *
from core.models import Participant
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
    list_display = ("name", "get_content", "get_class", "course",
                    "author", "direction", "publishdate", 'get_response')
    list_filter = ("course", "direction", "responded")
    search_fields = ("name", )
    fieldsets = [
        (None,
            {"fields": ["name", "course", "author", "direction",
                        "publishdate"]}),
        ("Content",
            {"fields": ["content"]})
    ]

    def get_content(self, obj):
        return '<a href="">' + obj.content + '<a>'

    get_content.short_description = 'Message Content'
    get_content.allow_tags = True

    def get_class(self, obj):
        p = Participant.objects.select_related().filter(learner=obj.author)
        return ', '.join([obj.classs.name for obj in p.all()])

    get_class.short_description = 'Class'

    def get_response(self, obj):
        if obj.responded:
            return obj.responddate
        else:
            return '<a href="">Respond</a>'

    get_response.short_description = 'Response Sent'
    get_response.allow_tags = True


class SmsAdmin(SummernoteModelAdmin):
    list_display = ("msisdn", "date_sent", "message")


# Communication
admin.site.register(Sms, SmsAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ChatGroup, ChatGroupAdmin)
admin.site.register(Discussion, DiscussionAdmin)

from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from models import *

class PageAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description"]})
    ]


class PostAdmin(SummernoteModelAdmin):
    list_display = ("name", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "course", "publishdate"]}),
        ("Content",             {"fields": ["content"]})
    ]


class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description"]})
    ]


# Communication
admin.site.register(Page, PageAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Discussion, DiscussionAdmin)
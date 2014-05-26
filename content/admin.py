from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from models import *


class TestingQuestionInline(admin.TabularInline):
    model = TestingQuestion
    extra = 1
    fields = ("order", "name", "description", "difficulty", "points")
    ordering = ("order", "name")


class TestingQuestionOptionInline(admin.TabularInline):
    model = TestingQuestionOption
    extra = 1
    fields = ("order", "name", "correct")
    ordering = ("order", "name")


class LearningChapterAdmin(SummernoteModelAdmin):
    list_display = ("module", "order", "name", "description")
    list_filter = ("module", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "module", "order"]}),
        ("Content",
            {"fields": ["content"]})
    ]
    ordering = ("module", "order", "name", )


class TestingBankAdmin(SummernoteModelAdmin):
    list_display = ("module", "order", "name", "description")
    list_filter = ("module", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "module", "order"]}),
        ("Content",
            {"fields": ["question_order", ]})
    ]
    inlines = (TestingQuestionInline, )
    ordering = ("module", "order", "name", )


class TestingQuestionAdmin(SummernoteModelAdmin):
    list_display = ("bank", "order", "name", "description")
    list_filter = ("bank", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "bank", "order"]}),
        ("Content",
            {"fields": ["question_content", "answer_content",
                        "difficulty", "points"]})
    ]
    inlines = (TestingQuestionOptionInline,)
    ordering = ("bank", "order", "name", )


class TestingQuestionOptionAdmin(SummernoteModelAdmin):
    list_display = ("question", "order", "name")
    list_filter = ("question", )
    search_fields = ("name",)
    fieldsets = [
        (None,                  {"fields": ["name", "question", "order"]}),
        ("Content",             {"fields": ["content", "correct"]})
    ]
    ordering = ("question", "order", "name", )


# Content
admin.site.register(LearningChapter, LearningChapterAdmin)
admin.site.register(TestingBank, TestingBankAdmin)
admin.site.register(TestingQuestion, TestingQuestionAdmin)

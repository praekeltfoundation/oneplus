from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import TestingBank, TestingQuestion, TestingQuestionOption, LearningChapter
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from core.models import ParticipantQuestionAnswer


class TestingQuestionInline(admin.TabularInline):
    model = TestingQuestion
    extra = 1
    fields = ("order", "name", "description", "difficulty", "points")
    ordering = ("order", "name")


class TestingQuestionOptionInline(admin.TabularInline):
    model = TestingQuestionOption
    extra = 1
    fields = ("order", "name", "admin_thumbnail", "correct", "link")
    readonly_fields = ('link', "admin_thumbnail")
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


class TestingQuestionResource(resources.ModelResource):

    class Meta:
        model = TestingQuestion
        fields = (
            'id',
            'name',
            'description',
            'bank',
            'percentage_correct',
            'correct',
            'incorrect'
        )
        export_order = (
            'id',
            'name',
            'description',
            'bank',
            'percentage_correct',
            'correct',
            'incorrect'
        )

    correct = fields.Field(column_name=u'correct')
    incorrect = fields.Field(column_name=u'incorrect')
    percentage_correct = fields.Field(column_name=u'percentage_correct')

    def dehydrate_correct(self, question):
        return ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()

    def dehydrate_incorrect(self, question):
        return ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=False
        ).count()

    def dehydrate_percentage_correct(self, question):
        correct = ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()
        total = ParticipantQuestionAnswer.objects.filter(
            question=question
        ).count()

        if total > 0:
            return 100 * correct / total
        else:
            return 0


class TestingQuestionAdmin(SummernoteModelAdmin, ImportExportModelAdmin):
    list_display = ("bank", "order", "name", "description",
                    "correct", "incorrect", "percentage_correct")
    list_filter = ("bank", )
    search_fields = ("name", "description")

    def correct(self, question):
        return ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()
    correct.allow_tags = True
    correct.short_description = "Correct"

    def incorrect(self, question):
        return ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=False
        ).count()
    incorrect.allow_tags = True
    incorrect.short_description = "Incorrect"

    def percentage_correct(self, question):
        correct = ParticipantQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()
        total = ParticipantQuestionAnswer.objects.filter(
            question=question
        ).count()
        if total > 0:
            return 100 * correct / total
        else:
            return 0
    percentage_correct.allow_tags = True
    percentage_correct.short_description = "Percentage Correct"

    fieldsets = [
        (None,
            {"fields": ["name", "description", "bank", "order"]}),
        ("Content",
            {"fields": ["question_content", "answer_content", "textbook_link",
                        "difficulty", "points"]})
    ]
    inlines = (TestingQuestionOptionInline,)
    resource_class = TestingQuestionResource


class TestingQuestionOptionAdmin(SummernoteModelAdmin):
    list_display = ("question", "order", "name")
    list_filter = ("question", )
    search_fields = ("name",)
    fieldsets = [
        (None, {"fields": ["name", "question", "order"]}),
        ("Content", {"fields": ["content", "correct"]})
    ]
    ordering = ("question", "order", "name", )


# Content
admin.site.register(LearningChapter, LearningChapterAdmin)
admin.site.register(TestingBank, TestingBankAdmin)
admin.site.register(TestingQuestion, TestingQuestionAdmin)
admin.site.register(TestingQuestionOption, TestingQuestionOptionAdmin)

from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import TestingQuestion, TestingQuestionOption, LearningChapter, Mathml, GoldenEgg
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from core.models import ParticipantQuestionAnswer, Class
from .forms import TestingQuestionCreateForm, TestingQuestionFormSet, TestingQuestionOptionCreateForm, GoldenEggCreateForm
from organisation.models import Course, CourseModuleRel

class TestingQuestionInline(admin.TabularInline):
    model = TestingQuestion
    extra = 1
    fields = ("order", "name", "description", "difficulty", "points")
    ordering = ("order", "name")


class TestingQuestionOptionInline(admin.TabularInline):
    model = TestingQuestionOption
    extra = 2
    fields = ("order", "name", "admin_thumbnail", "correct", "link")
    readonly_fields = ('link', "admin_thumbnail")
    ordering = ("order", "name")
    formset = TestingQuestionFormSet


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


class TestingQuestionResource(resources.ModelResource):

    class Meta:
        model = TestingQuestion
        fields = (
            'id',
            'name',
            'description',
            'percentage_correct',
            'correct',
            'incorrect'
        )
        export_order = (
            'id',
            'name',
            'description',
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
    list_display = ("name", "order", "module", "get_course", "description",
                    "correct", "incorrect", "percentage_correct", "preview_link", "state")
    list_filter = ("module", "state")
    search_fields = ("name", "description")

    form = TestingQuestionCreateForm

    def get_course(self, question):
        courses = Course.objects.filter(coursemodulerel__module=question.module)

        course_list = ""

        for c in courses:
            course_list += c.name + "\n"

        return course_list
    get_course.short_description = "Courses"

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

    def preview_link(self, question):
        return u'<a href="/preview/%s">Preview</a>' % question.id
    preview_link.allow_tags = True
    preview_link.short_description = "Preview"

    def make_incomplete(modeladmin, request, queryset):
        queryset.update(state='1')
    make_incomplete.short_description = "Change state to Incomplete"

    def make_ready(modeladmin, request, queryset):
        queryset.update(state='2')
    make_ready.short_description = "Change state to Ready for Review"

    def make_published(modeladmin, request, queryset):
        queryset.update(state='3')
    make_published.short_description = "Change state to Published"

    actions = [make_incomplete, make_ready, make_published]

    fieldsets = [
        (None,
            {"fields": ["name", "description", "module", "order"]}),
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
    form = TestingQuestionOptionCreateForm
    fieldsets = [
        (None, {"fields": ["name", "question", "order"]}),
        ("Content", {"fields": ["content", "correct"]})
    ]
    ordering = ("question", "order", "name", )


class MathmlAdmin(SummernoteModelAdmin):
    list_display = ("filename", "rendered")
    list_filter = ("rendered", "source", "source_id")

class GoldenEggAdmin(SummernoteModelAdmin):
    list_display = ("classs", "course", "get_reward", "get_reward_value", "active")
    list_filter = ("course", "classs", "active", "badge")
    fieldsets = [
        (None, {"fields": ["classs", "course", "active"]}),
        ("Reward", {"fields": ["point_value", "airtime", "badge"]})
    ]
    form = GoldenEggCreateForm

    def get_reward(self, golden_egg):
        if golden_egg.point_value:
            return "Points"
        if golden_egg.airtime:
            return "Airtime"
        if golden_egg.badge:
            return "Badge"
    get_reward.short_description = "Reward"

    def get_reward_value(self, golden_egg):
        if golden_egg.point_value:
            return golden_egg.point_value
        if golden_egg.airtime:
            return "R%d" % golden_egg.airtime
        if golden_egg.badge:
            return golden_egg.badge.name
    get_reward_value.short_description = "Reward Value"

# Content
admin.site.register(LearningChapter, LearningChapterAdmin)
admin.site.register(TestingQuestion, TestingQuestionAdmin)
admin.site.register(TestingQuestionOption, TestingQuestionOptionAdmin)
admin.site.register(Mathml, MathmlAdmin)
admin.site.register(GoldenEgg, GoldenEggAdmin)
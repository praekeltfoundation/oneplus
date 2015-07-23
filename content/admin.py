from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin, SummernoteInlineModelAdmin
from .models import TestingQuestion, TestingQuestionOption, LearningChapter, Mathml, GoldenEgg, EventSplashPage, \
    EventStartPage, EventEndPage, EventQuestionAnswer, Event, EventQuestionRel, SUMit, SUMitEndPage, SUMitLevel, \
    Definition
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from core.models import ParticipantQuestionAnswer, Participant, ParticipantRedoQuestionAnswer
from .forms import TestingQuestionCreateForm, TestingQuestionFormSet, TestingQuestionOptionCreateForm, \
    GoldenEggCreateForm, EventSplashPageInlineFormSet, EventStartPageInlineFormSet, EventEndPageInlineFormSet, \
    EventQuestionRelInline, EventForm, SUMitEndPageInlineFormSet, SUMitLevelForm
from organisation.models import Course
from django.db.models import Count
from datetime import datetime


class TestingQuestionInline(admin.TabularInline):
    model = TestingQuestion
    extra = 1
    fields = ("order", "name", "description", "difficulty", "points")
    readonly_fields = ("name", "order")
    ordering = ("order", "name")


class TestingQuestionOptionInline(admin.StackedInline, SummernoteInlineModelAdmin):
    model = TestingQuestionOption
    extra = 3
    fields = ("order", "name", "content", "correct", "link")
    readonly_fields = ('link', "order", "name")
    ordering = ("order", "name")
    formset = TestingQuestionFormSet


class LearningChapterAdmin(SummernoteModelAdmin):
    list_display = ("module", "order", "name", "description")
    list_filter = ("module",)
    search_fields = ("name", "description")
    fieldsets = [
        (None,
         {"fields": ["name", "description", "module", "order"]}),
        ("Content",
         {"fields": ["content"]})
    ]
    ordering = ("module", "order", "name",)


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
                    "correct", "incorrect", "percentage_correct", "redo_correct", "redo_incorrect",
                    "redo_percentage_correct", "preview_link", "state")
    list_filter = ("module", "state")
    readonly_fields = ("name", "order")
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

    def redo_correct(self, question):
        return ParticipantRedoQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()
    redo_correct.allow_tags = True
    redo_correct.short_description = "Redo Correct"

    def redo_incorrect(self, question):
        return ParticipantRedoQuestionAnswer.objects.filter(
            question=question,
            correct=False
        ).count()
    redo_incorrect.allow_tags = True
    redo_incorrect.short_description = "Redo Incorrect"

    def redo_percentage_correct(self, question):
        correct = ParticipantRedoQuestionAnswer.objects.filter(
            question=question,
            correct=True
        ).count()
        total = ParticipantRedoQuestionAnswer.objects.filter(
            question=question
        ).count()
        if total > 0:
            return 100 * correct / total
        else:
            return 0
    redo_percentage_correct.allow_tags = True
    redo_percentage_correct.short_description = "Redo Percentage Correct"

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
         {"fields": ["question_content", "answer_content", "notes", "textbook_link",
                     "difficulty", "points"]})
    ]
    inlines = (TestingQuestionOptionInline,)
    resource_class = TestingQuestionResource


class TestingQuestionOptionAdmin(SummernoteModelAdmin):
    list_display = ("question", "order", "name")
    list_filter = ("question",)
    readonly_fields = ("name", "order")
    search_fields = ("name",)
    form = TestingQuestionOptionCreateForm
    fieldsets = [
        (None, {"fields": ["name", "question", "order"]}),
        ("Content", {"fields": ["content", "correct"]})
    ]
    ordering = ("question", "order", "name",)


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


class EventSplashPageInline(admin.TabularInline):
    model = EventSplashPage
    extra = 1
    max_num = 3
    fields = ("order_number", "header", "paragraph")
    ordering = ("order_number",)
    verbose_name = "Splash Page"
    verbose_name_plural = "Splash Page"
    formset = EventSplashPageInlineFormSet


class EventStartPageInline(admin.TabularInline):
    model = EventStartPage
    extra = 1
    max_num = 1
    fields = ("header", "paragraph")
    verbose_name = "Start Page"
    verbose_name_plural = "Start Page"
    formset = EventStartPageInlineFormSet


class EventEndPageInline(admin.TabularInline):
    model = EventEndPage
    extra = 1
    max_num = 1
    fields = ("header", "paragraph")
    verbose_name = "End Page"
    verbose_name_plural = "End Page"
    formset = EventEndPageInlineFormSet


class EventQuestionRelInline(admin.TabularInline):
    model = EventQuestionRel
    extra = 1
    fields = ("order", "question",)
    verbose_name = "Event Questions"
    verbose_name_plural = "Event Questions"
    ordering = ("order",)
    formset = EventQuestionRelInline


class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "activation_date", "deactivation_date", "get_total_users",
                    "get_total_questions_answered", "get_percent_complete_all",
                    "get_percent_correct", "get_participant", "get_is_active")
    list_filter = ()
    fieldsets = [
        (None, {"fields": ["name", "course", "activation_date", "deactivation_date", "number_sittings", "event_points",
                           "airtime", "event_badge", "type"]})]
    inlines = (EventSplashPageInline, EventStartPageInline, EventEndPageInline, EventQuestionRelInline)
    form = EventForm
    add_form = EventForm

    def queryset(self, request):
        return Event.objects.all().exclude(type=0)

    def get_total_users(self, obj):
        return Participant.objects.filter(classs__course=obj.course).aggregate(Count('id'))['id__count']

    get_total_users.short_description = "Total Users"

    def get_total_questions_answered(self, obj):
        return EventQuestionAnswer.objects.filter(event=obj).aggregate(Count('id'))['id__count']

    get_total_questions_answered.short_description = "Total Questions Answered"

    def get_percent_complete_all(self, obj):
        # total_participants = Participant.objects.filter(classs__course=obj.course, is_active=True)\
        #     .aggregate(Count('id'))['id__count']
        # total_event_questions = EventQuestionRel.objects.filter(event=obj) \
        #     .aggregate(Count('question'))['question__count']
        # completed = EventQuestionAnswer.objects.values('participant')\
        #     .annotate(answered=Count('question_option'))\
        #     .filter(event=obj, answered=total_event_questions).aggregate(Count('answered'))
        #
        # return (completed / total_participants) * 100
        return 0

    get_percent_complete_all.short_description = "% Complete All Questions"

    def get_percent_correct(self, obj):
        answered = self.get_total_questions_answered(obj)
        correct = EventQuestionAnswer.objects.filter(event=obj, correct=True) \
            .aggregate(Count('correct'))['correct__count']
        if answered > 0:
            return (correct / answered) * 100
        else:
            return 0

    get_percent_correct.short_description = "% Correct"

    def get_participant(self, obj):
        participant_string = ""
        all_participants = Participant.objects.filter(classs__course=obj.course)
        for p in all_participants:
            participant_string += "%s %s, " % (p.learner.first_name, p.learner.last_name)
        return participant_string[:-2]

    get_participant.short_description = "Participants"

    def get_is_active(self, obj):
        if obj.activation_date < datetime.now() < obj.deactivation_date:
            return "<img alt='True' src='/static/admin/img/icon-yes.gif'>"
        else:
            return "<img alt='True' src='/static/admin/img/icon-no.gif'>"

    get_is_active.short_description = "Active"
    get_is_active.allow_tags = True


class SUMitEndPageInline(admin.TabularInline):
    model = SUMitEndPage
    extra = 3
    max_num = 3
    fields = ("type", "header", "paragraph")
    verbose_name = "End Page"
    verbose_name_plural = "End Page"
    formset = SUMitEndPageInlineFormSet

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "type":
            kwargs["initial"] = 1
        return super(EventSplashPageInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SUMitAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "activation_date", "deactivation_date", "get_total_users",
                    "get_total_questions_answered", "get_percent_complete_all", "get_easy_questions_answered",
                    "get_percent_correct_easy", "get_normal_questions_answered", "get_percent_correct_normal",
                    "get_advanced_questions_answered", "get_percent_correct_advanced", "get_winners", "get_is_active")
    list_filter = ()
    fieldsets = [
        (None, {"fields": ["name", "course", "activation_date", "deactivation_date", "event_points",
                           "airtime", "event_badge"]})]
    inlines = (EventSplashPageInline, EventStartPageInline, SUMitEndPageInline)
    form = EventForm
    add_form = EventForm

    def get_total_users(self, obj):
        return Participant.objects.filter(classs__course=obj.course).aggregate(Count('id'))['id__count']
    get_total_users.short_description = "Total Users"

    def get_total_questions_answered(self, obj):
        return EventQuestionAnswer.objects.filter(event=obj).aggregate(Count('id'))['id__count']
    get_total_questions_answered.short_description = "Total Questions Answered"

    def get_easy_questions_answered(self, obj):
        return EventQuestionAnswer.objects.filter(event=obj, question__difficulty=2).aggregate(Count('id'))['id__count']
    get_easy_questions_answered.short_description = "Total Easy Questions Answered"

    def get_normal_questions_answered(self, obj):
        return EventQuestionAnswer.objects.filter(event=obj, question__difficulty=3).aggregate(Count('id'))['id__count']
    get_normal_questions_answered.short_description = "Total Normal Questions Answered"

    def get_advanced_questions_answered(self, obj):
        return EventQuestionAnswer.objects.filter(event=obj, question__difficulty=4).aggregate(Count('id'))['id__count']
    get_advanced_questions_answered.short_description = "Total Advanced Questions Answered"

    def get_percent_complete_all(self, obj):
        total_participants = Participant.objects.filter(classs__course=obj.course).aggregate(Count('id'))['id__count']
        completed = len(EventQuestionAnswer.objects.values('participant').filter(correct=True).
                        annotate(answered=Count('question_option')).values('participant').filter(answered=15))
        if total_participants == 0:
            return 0
        else:
            return round((float(completed) / total_participants) * 100)
    get_percent_complete_all.short_description = "% Complete All Questions"

    def get_percent_correct_easy(self, obj):
        answered = self.get_easy_questions_answered(obj)
        correct = EventQuestionAnswer.objects.filter(event=obj, question__difficulty=2, correct=True) \
            .aggregate(Count('correct'))['correct__count']
        if answered > 0:
            return round((float(correct) / answered) * 100)
        else:
            return 0
    get_percent_correct_easy.short_description = "% Correct Easy Questions Answered"

    def get_percent_correct_normal(self, obj):
        answered = self.get_normal_questions_answered(obj)
        correct = EventQuestionAnswer.objects.filter(event=obj, question__difficulty=2, correct=True) \
            .aggregate(Count('correct'))['correct__count']
        if answered > 0:
            return round((float(correct) / answered) * 100)
        else:
            return 0
    get_percent_correct_normal.short_description = "% Correct Normal Questions Answered"

    def get_percent_correct_advanced(self, obj):
        answered = self.get_advanced_questions_answered(obj)
        correct = EventQuestionAnswer.objects.filter(event=obj, question__difficulty=2, correct=True) \
            .aggregate(Count('correct'))['correct__count']
        if answered > 0:
            return round((float(correct) / answered) * 100)
        else:
            return 0
    get_percent_correct_advanced.short_description = "% Correct Advanced Questions Answered"

    def get_winners(self, obj):
        participant_string = ""
        winner_ids = EventQuestionAnswer.objects.values('participant').filter(event=obj, correct=True).\
            annotate(correct=Count('question_option')).values('participant').filter(correct=15)
        all_participants = Participant.objects.filter(id__in=winner_ids)
        for p in all_participants:
            participant_string += "%s %s, " % (p.learner.first_name, p.learner.last_name)
        return participant_string[:-2]
    get_winners.short_description = "SUMit!s"

    def get_is_active(self, obj):
        if obj.activation_date < datetime.now() < obj.deactivation_date:
            return "<img alt='True' src='/static/admin/img/icon-yes.gif'>"
        else:
            return "<img alt='True' src='/static/admin/img/icon-no.gif'>"
    get_is_active.short_description = "Active"
    get_is_active.allow_tags = True


class SUMitLevelAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "question_1", "question_2", "question_3", "image_")
    fieldsets = [(None, {"fields": ["order", "name", "question_1", "question_2", "question_3", "image"]})]
    ordering = ["order"]
    readonly_fields = ["order"]

    form = SUMitLevelForm

    def has_add_permission(self, request):
        return False

# Content
admin.site.register(LearningChapter, LearningChapterAdmin)
admin.site.register(TestingQuestion, TestingQuestionAdmin)
admin.site.register(TestingQuestionOption, TestingQuestionOptionAdmin)
admin.site.register(Mathml, MathmlAdmin)
admin.site.register(Definition)
admin.site.register(GoldenEgg, GoldenEggAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(SUMit, SUMitAdmin)
admin.site.register(SUMitLevel, SUMitLevelAdmin)
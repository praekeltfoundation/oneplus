from django.shortcuts import render_to_response, redirect
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.conf import settings
from import_export.admin import ImportExportModelAdmin
from communication.utils import VumiSmsApi
from auth.forms import SendSmsForm, SendMessageForm
from communication.tasks import bulk_send_all
from django import template
from auth.models import SystemAdministrator, SchoolManager, CourseManager, CourseMentor, Teacher, Learner
from .forms import SystemAdministratorChangeForm, \
    SystemAdministratorCreationForm, SchoolManagerChangeForm,\
    SchoolManagerCreationForm, CourseManagerChangeForm, \
    CourseManagerCreationForm, CourseMentorChangeForm, \
    CourseMentorCreationForm, LearnerChangeForm, LearnerCreationForm, \
    TeacherCreationForm, TeacherChangeForm
from core.models import ParticipantQuestionAnswer
from auth.resources import LearnerResource, TeacherResource
from auth.filters import AirtimeFilter, ClassFilter, CourseFilter
from core.models import TeacherClass, ParticipantBadgeTemplateRel, Participant
from gamification.models import GamificationScenario
from communication.models import Message
from datetime import datetime


class SystemAdministratorAdmin(UserAdmin):
    # The forms to add and change user instances
    form = SystemAdministratorChangeForm
    add_form = SystemAdministratorCreationForm

    list_display = ("username", "last_name", "first_name", "country", "area")
    list_filter = ("country", "area")
    search_fields = ("last_name", "first_name", "username")
    ordering = ("country", "area", "last_name")
    filter_horizontal = ()

    fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name", "email",
                                      "mobile")}),
        ("Access", {"fields": ("username", "password", "is_active")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Access", {"fields": ("username", "password1",
                               "password2")}),
        ("Region", {"fields": ("country",)})
    )


class SchoolManagerAdmin(UserAdmin):
    # The forms to add and change user instances
    form = SchoolManagerChangeForm
    add_form = SchoolManagerCreationForm

    list_display = ("username", "last_name", "first_name", "country", "area")
    list_filter = ("country", "area")
    search_fields = ("last_name", "first_name", "username")
    ordering = ("country", "area", "last_name")
    filter_horizontal = ()

    fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name",
                                      "email", "mobile")}),
        ("Access", {"fields": ("username", "password",
                               "is_active")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups")}),
        ("Region", {"fields": ("country", "area", "city",
                               "school")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Access", {"fields": ("username", "password1",
                               "password2")}),
        ("Region", {"fields": ("country", "area", "school")})
    )


class CourseManagerAdmin(UserAdmin):
    # The forms to add and change user instances
    form = CourseManagerChangeForm
    add_form = CourseManagerCreationForm

    list_display = ("username", "last_name", "first_name", "country", "area")
    list_filter = ("country", "area")
    search_fields = ("last_name", "first_name", "username")
    ordering = ("country", "area", "last_name")
    filter_horizontal = ()

    fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name",
                                      "email", "mobile")}),
        ("Access", {"fields": ("username", "password",
                               "is_active")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups")}),
        ("Region", {"fields": ("country", "area", "city",
                               "course")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Access", {"fields": ("username", "password1",
                               "password2")}),
        ("Region", {"fields": ("country", "area", "course")})
    )


class CourseMentorAdmin(UserAdmin):
    # The forms to add and change user instances
    form = CourseMentorChangeForm
    add_form = CourseMentorCreationForm

    list_display = ("username", "last_name", "first_name", "country", "area")
    list_filter = ("country", "area")
    search_fields = ("last_name", "first_name", "username")
    ordering = ("country", "area", "last_name")
    filter_horizontal = ()

    fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name",
                                      "email", "mobile")}),
        ("Access", {"fields": ("username", "password",
                               "is_active")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups")}),
        ("Region", {"fields": ("country", "area", "city",
                               "course")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Access", {"fields": ("username", "password1",
                               "password2")}),
        ("Region", {"fields": ("country", "area", "course")})
    )


def send_sms(modeladmin, request, queryset):
    form = None
    if 'apply' in request.POST:
        form = SendSmsForm(request.POST)

        if form.is_valid():
            vumi = VumiSmsApi()
            message = form.cleaned_data["message"]

            if queryset.count() <= settings.MIN_VUMI_CELERY_SEND:
                successful, fail = vumi.send_all(queryset, message)
                async = False
            else:
                #Use celery task
                bulk_send_all.delay(queryset, message)
                successful = 0
                fail = []
                async = True

            return render_to_response(
                'admin/auth/sms_result.html',
                {
                    'redirect': request.get_full_path(),
                    'success_num': successful,
                    'fail': fail,
                    'async': async
                },
            )

    if not form:
        form = SendSmsForm(
            initial={
                '_selected_action': request.POST.getlist(
                    admin.ACTION_CHECKBOX_NAME,
                ),
            }
        )
    return render_to_response(
        'admin/auth/send_sms.html',
        {
            'sms_form': form,
            'learners': queryset
        },
        context_instance=template.RequestContext(request)
    )
send_sms.short_description = "Send SMS to selected learners"


def send_message(modeladmin, request, queryset):
    form = None

    if 'apply' in request.POST:
        form = SendMessageForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["name"]
            date = datetime.strptime(request.POST['publishdate_0'], '%Y-%m-%d')
            t = datetime.strptime(request.POST['publishdate_1'], "%H:%M")
            publish_date = datetime.combine(date, t.time())
            message = form.cleaned_data["message"]

            for learner in queryset:
                part = Participant.objects.filter(learner=learner, is_active=True).first()
                if part and part.classs:
                    Message.objects.create(name=name, publishdate=publish_date, content=message, to_user=learner,
                                           author=request.user, to_class=part.classs, course=part.classs.course)

            successful = len(queryset)

            return render_to_response(
                'admin/auth/message_result.html',
                {
                    'redirect': request.get_full_path(),
                    'success_num': successful,
                },
            )
    if not form:
        form = SendMessageForm(
            initial={
                '_selected_action': request.POST.getlist(
                    admin.ACTION_CHECKBOX_NAME,
                ),
            }
        )

    return render_to_response(
        'admin/auth/send_message.html',
        {
            'message_form': form,
            'learners': queryset
        },
        context_instance=template.RequestContext(request)
    )
send_message.short_description = "Send Message to selected learners"


class LearnerAdmin(UserAdmin, ImportExportModelAdmin):
    # The forms to add and change user instances
    form = LearnerChangeForm
    add_form = LearnerCreationForm
    resource_class = LearnerResource
    list_max_show_all = 1000
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("username", "first_name", "last_name", "school",
                    "area", "welcome_message_sent", "class_list")
    list_filter = ("first_name", "last_name", "mobile", 'school', "country", "area",
                   "welcome_message_sent", ClassFilter, CourseFilter, AirtimeFilter)
    search_fields = ("last_name", "first_name", "username")
    ordering = ("country", "area", "last_name", "first_name", "last_login")
    filter_horizontal = ()
    readonly_fields = ("mobile",)

    fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name",
                                      "email", "mobile")}),
        ("Access", {"fields": ("username", "password",
                               "is_active", "unique_token")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups")}),
        ("Region", {"fields": ("country", "area", "city",
                               "school", "classs")}),
        ("Opt-In Communications", {"fields": ("optin_sms", "optin_email")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Access", {"fields": ("username", "password1",
                               "password2")}),
        ("Region", {"fields": ("country", "area", "school")})
    )

    actions = [send_sms, send_message]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        all_scenarios = GamificationScenario.objects.all()
        all_participant_badges = ParticipantBadgeTemplateRel.objects.filter(participant__learner__id=object_id,
                                                                            participant__is_active=True)

        badges_list = list()
        count = 0
        row = list()
        for s in all_scenarios:
            item = dict()
            item['scenario'] = s
            item['scenario_count'] = 0
            for a in all_participant_badges:
                if s == a.scenario:
                    item['scenario_count'] = a.awardcount
                    break
            row.append(item)
            count += 1

            if count % 5 == 0:
                badges_list.append(row)
                row = []

        if len(row) > 0:
            badges_list.append(row)

        extra_context = extra_context or {}
        extra_context['scenario_list'] = badges_list
        return super(LearnerAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def class_list(self, obj):
        return obj.get_class(active_only=True)


class TeacherClassInline(admin.TabularInline):
    model = TeacherClass
    extra = 1
    fields = ("classs", )
    ordering = ("classs", )


class TeacherAdmin(UserAdmin, ImportExportModelAdmin):
    form = TeacherChangeForm
    add_form = TeacherCreationForm
    resource_class = TeacherResource
    list_display = ("username", "first_name", "last_name", "school",
                    "students_completed_questions", "students_percentage_correct",
                    "welcome_message_sent")
    list_filter = ("first_name", "last_name", "mobile", 'school', "country",
                   "area", "welcome_message_sent")
    search_fields = ("last_name", "first_name", "username")
    ordering = ("country", "area", "last_name", "first_name", "last_login")
    filter_horizontal = ()
    readonly_fields = ("mobile",)

    fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name",
                                      "email", "mobile")}),
        ("Access", {"fields": ("username", "password",
                               "is_active", "unique_token")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups")}),
        ("Region", {"fields": ("country", "area", "city",
                               "school")}),
        ("Opt-In Communications", {"fields": ("optin_sms", "optin_email")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Access", {"fields": ("username", "password1",
                               "password2")}),
        ("Region", {"fields": ("country", "area", "school")})
    )

    add_fieldsets2 = (
        ("Personal info", {"fields": ("first_name", "last_name", "email", "mobile")}),
        ("Access", {"fields": ("username", "password", 'is_active', "unique_token")}),
        ("Permissions", {"fields": ('is_staff', 'is_superuser', 'groups')}),
        ("Region", {"fields": ("country", "area", "city", "school")}),
        ("Opt-In Communications", {"fields": ("optin_sms", "optin_email")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )

    inlines = [TeacherClassInline, ]

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return self.add_fieldsets2

    def students_completed_questions(self, teacher):
        classes = TeacherClass.objects.filter(teacher=teacher).values("classs")
        return ParticipantQuestionAnswer.objects.filter(
            participant__classs__in=classes
        ).count()
    students_completed_questions.short_description = "Student Completed Questions"
    students_completed_questions.allow_tags = True

    def students_percentage_correct(self, teacher):
        complete = self.students_completed_questions(teacher)
        classes = TeacherClass.objects.filter(teacher=teacher).values("classs")
        if complete > 0:
            return ParticipantQuestionAnswer.objects.filter(
                participant__classs__in=classes,
                correct=True
            ).count() * 100 / complete
        else:
            return 0
    students_percentage_correct.short_description = "Student Percentage Correct"
    students_percentage_correct.allow_tags = True

# Auth
admin.site.register(SystemAdministrator, SystemAdministratorAdmin)
admin.site.register(SchoolManager, SchoolManagerAdmin)
admin.site.register(CourseManager, CourseManagerAdmin)
admin.site.register(CourseMentor, CourseMentorAdmin)
admin.site.register(Learner, LearnerAdmin)
admin.site.register(Teacher, TeacherAdmin)
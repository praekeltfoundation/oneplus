from datetime import datetime
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import fields
from communication.utils import VumiSmsApi
from random import randint
from auth.forms import SendWelcomeSmsForm
from django import template
from communication.utils import get_autologin_link
from auth.models import Learner, SystemAdministrator, SchoolManager,\
    CourseManager, CourseMentor
from organisation.models import School
from forms import SystemAdministratorChangeForm, \
    SystemAdministratorCreationForm, SchoolManagerChangeForm,\
    SchoolManagerCreationForm, CourseManagerChangeForm, \
    CourseManagerCreationForm, CourseMentorChangeForm, \
    CourseMentorCreationForm, LearnerChangeForm, LearnerCreationForm
import koremutake
from django.contrib.auth.hashers import make_password
from django.utils.translation import ugettext_lazy as _
from organisation.models import Course
from core.models import ParticipantQuestionAnswer
from django.core.exceptions import ObjectDoesNotExist
from core.models import Participant, Class


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
        ("Personal info",   {"fields": ("first_name", "last_name", "email",
                                        "mobile")}),
        ("Access",          {"fields": ("username", "password", "is_active")}),
        ("Permissions",     {"fields": ("is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info",           {"fields": ("first_name", "last_name")}),
        ("Access",                  {"fields": ("username", "password1",
                                                "password2")}),
        ("Region",                  {"fields": ("country",)})
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
        ("Personal info",           {"fields": ("first_name", "last_name",
                                                "email", "mobile")}),
        ("Access",                  {"fields": ("username", "password",
                                                "is_active")}),
        ("Region",                  {"fields": ("country", "area", "city",
                                                "school")}),
        ("Important dates",         {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info",           {"fields": ("first_name", "last_name")}),
        ("Access",                  {"fields": ("username", "password1",
                                                "password2")}),
        ("Region",                  {"fields": ("country", "area", "school")})
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
        ("Personal info",           {"fields": ("first_name", "last_name",
                                                "email", "mobile")}),
        ("Access",                  {"fields": ("username", "password",
                                                "is_active")}),
        ("Region",                  {"fields": ("country", "area", "city",
                                                "course")}),
        ("Important dates",         {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info",           {"fields": ("first_name", "last_name")}),
        ("Access",                  {"fields": ("username", "password1",
                                                "password2")}),
        ("Region",                  {"fields": ("country", "area", "course")})
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
        ("Personal info",           {"fields": ("first_name", "last_name",
                                                "email", "mobile")}),
        ("Access",                  {"fields": ("username", "password",
                                                "is_active")}),
        ("Region",                  {"fields": ("country", "area", "city",
                                                "course")}),
        ("Important dates",         {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info",           {"fields": ("first_name", "last_name")}),
        ("Access",                  {"fields": ("username", "password1",
                                                "password2")}),
        ("Region",                  {"fields": ("country", "area", "course")})
    )


class LearnerResource(resources.ModelResource):
    course = fields.Field(column_name=u'course')
    completed_questions = fields.Field(column_name=u'completed_questions')
    percentage_correct = fields.Field(column_name=u'percentage_correct')

    class Meta:
        model = Learner
        exclude = (
            'customuser_ptr', 'password', 'last_login', 'is_superuser',
            'groups', 'user_permissions', 'is_staff', 'is_active',
            'date_joined', 'unique_token', 'unique_token_expiry'
            'welcome_message_sent', 'welcome_message'
        )
        export_order = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'mobile',
            'school',
            'country',
            'area',
            'city',
            'optin_sms',
            'optin_email',
            'completed_questions',
            'percentage_correct',
            'course',
        )

    def dehydrate_school(self, learner):
        if learner.school is not None:
            return learner.school.name
        else:
            return ""

    def dehydrate_completed_questions(self, learner):
        return ParticipantQuestionAnswer.objects.filter(
            participant__learner=learner
        ).count()

    def dehydrate_percentage_correct(self, learner):
        complete = self.dehydrate_completed_questions(learner)
        if complete > 0:
            return ParticipantQuestionAnswer.objects.filter(
                participant__learner=learner,
                correct=True
            ).count()*100/complete
        else:
            return 0

    def get_or_init_instance(self, instance_loader, row):
        row[u'is_staff'] = False
        row[u'is_superuser'] = False
        row[u'is_active'] = True
        row[u'date_joined'] = datetime.now()
        row[u'welcome_message_sent'] = None
        row[u'welcome_message'] = None

        return super(resources.ModelResource, self) \
            .get_or_init_instance(instance_loader, row)

    def import_obj(self, obj, data, dry_run):
        school, created = School.objects.get_or_create(name=data[u'school'])
        data[u'school'] = school.id
        return super(resources.ModelResource, self)\
            .import_obj(obj, data, dry_run)

    def save_m2m(self, obj, data, dry_run):
        course = Course.objects.filter(name=data[u'course']).first()

        # If the course and respective class exist, create participant
        if course:
            classs = Class.objects.get(course=course)
            if classs and not dry_run:
                Participant.objects.create(
                    learner=obj,
                    classs=classs,
                    datejoined=datetime.now(),

                )
        return super(resources.ModelResource, self)\
            .save_m2m(obj, data, dry_run)


class CourseFilter(admin.SimpleListFilter):
    title = _('Course')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Course.objects.all().values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__classs__course_id=self.value())


class LearnerAdmin(UserAdmin, ImportExportModelAdmin):
    # The forms to add and change user instances
    form = LearnerChangeForm
    add_form = LearnerCreationForm
    resource_class = LearnerResource

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("username", "last_name", "first_name", "school",
                    "area", "completed_questions", "percentage_correct")
    list_filter = ("country", "area", CourseFilter)
    search_fields = ("last_name", "first_name", "username")
    ordering = ("country", "area", "last_name")
    filter_horizontal = ()
    readonly_fields = ("mobile",)

    fieldsets = (
        ("Personal info",           {"fields": ("first_name", "last_name",
                                                "email", "mobile")}),
        ("Access",                  {"fields": ("username", "password",
                                                "is_active", "unique_token")}),
        ("Region",                  {"fields": ("country", "area", "city",
                                                "school")}),
        ("Opt-In Communications",   {"fields": ("optin_sms", "optin_email")}),
        ("Important dates",         {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        ("Personal info",           {"fields": ("first_name", "last_name")}),
        ("Access",                  {"fields": ("username", "password1",
                                                "password2")}),
        ("Region",                  {"fields": ("country", "area", "school")})
    )

    def send_sms(self, request, queryset):
        form = None
        if 'apply' in request.POST:
            form = SendWelcomeSmsForm(request.POST)

            if form.is_valid():
                vumi = VumiSmsApi()
                message = form.cleaned_data["message"]

                #Check if a password or autologin message
                is_welcome_message = False
                is_autologin_message = False
                if "|password|" in message:
                    is_welcome_message = True
                    queryset = queryset.filter(
                        welcome_message_sent=False
                    )
                if "|autologin|" in message:
                    is_autologin_message = True

                for learner in queryset:
                    password = None
                    if is_welcome_message:
                        #Generate password
                        password = koremutake.encode(randint(10000, 100000))
                        learner.password = make_password(password)
                    if is_autologin_message:
                        #Generate autologin link
                        learner.generate_unique_token()
                    learner.save()

                    #Send sms
                    sms, sent = vumi.send(
                        learner.username,
                        message=message,
                        password=password,
                        autologin=get_autologin_link(learner.unique_token)
                    )

                    #Save welcome message details
                    if is_welcome_message:
                        learner.welcome_message = sms
                        learner.welcome_message_sent = True

                    learner.save()

                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = SendWelcomeSmsForm(
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
    send_sms.short_description = "Send sms to learners"
    actions = ['send_sms']

    def completed_questions(self, learner):
        return ParticipantQuestionAnswer.objects.filter(
            participant__learner=learner
        ).count()
    completed_questions.short_description = "Completed Questions"
    completed_questions.allow_tags = True

    def percentage_correct(self, learner):
        complete = self.completed_questions(learner)
        if complete > 0:
            return ParticipantQuestionAnswer.objects.filter(
                participant__learner=learner,
                correct=True
            ).count()*100/complete
        else:
            return 0
    percentage_correct.short_description = "Percentage correct"
    percentage_correct.allow_tags = True

# Auth
admin.site.register(SystemAdministrator, SystemAdministratorAdmin)
admin.site.register(SchoolManager, SchoolManagerAdmin)
admin.site.register(CourseManager, CourseManagerAdmin)
admin.site.register(CourseMentor, CourseMentorAdmin)
admin.site.register(Learner, LearnerAdmin)

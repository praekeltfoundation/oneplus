from datetime import datetime

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from auth.models import Learner, SystemAdministrator, SchoolManager,\
    CourseManager, CourseMentor
from organisation.models import School
from forms import SystemAdministratorChangeForm, \
    SystemAdministratorCreationForm, SchoolManagerChangeForm,\
    SchoolManagerCreationForm, CourseManagerChangeForm, \
    CourseManagerCreationForm, CourseMentorChangeForm, \
    CourseMentorCreationForm, LearnerChangeForm, LearnerCreationForm


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

    class Meta:
        model = Learner
        exclude = (
            'customuser_ptr', 'password', 'last_login', 'is_superuser',
            'groups', 'user_permissions', 'is_staff', 'is_active',
            'date_joined', 'unique_token', 'unique_token_expiry'
            'welcome_message_sent', 'welcome_message'
        )

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


#send_sms.short_description = "Send sms to learners"


class LearnerAdmin(UserAdmin, ImportExportModelAdmin):
    # The forms to add and change user instances
    form = LearnerChangeForm
    add_form = LearnerCreationForm
    resource_class = LearnerResource
    actions = ['send_sms']


    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("username", "last_name", "first_name", "country", "area",
                    "unique_token")
    list_filter = ("country", "area")
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


# Auth
admin.site.unregister(Group)
admin.site.register(SystemAdministrator, SystemAdministratorAdmin)
admin.site.register(SchoolManager, SchoolManagerAdmin)
admin.site.register(CourseManager, CourseManagerAdmin)
admin.site.register(CourseMentor, CourseMentorAdmin)
admin.site.register(Learner, LearnerAdmin)

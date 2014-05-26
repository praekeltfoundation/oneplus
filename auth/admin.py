from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from forms import *


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


class LearnerAdmin(UserAdmin):
    # The forms to add and change user instances
    form = LearnerChangeForm
    add_form = LearnerCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("username", "last_name", "first_name", "country", "area")
    list_filter = ("country", "area")
    search_fields = ("last_name", "first_name", "username")
    ordering = ("country", "area", "last_name")
    filter_horizontal = ()
    readonly_fields = ("mobile",)

    fieldsets = (
        ("Personal info",           {"fields": ("first_name", "last_name",
                                                "email", "mobile")}),
        ("Access",                  {"fields": ("username", "password",
                                                "is_active")}),
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

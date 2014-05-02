from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from forms import *



"""
class LearnerCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Learner
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(LearnerCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
"""



"""
class LearnerCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = ProxyLearner
        fields = ("username", "email")

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class LearnerChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = ProxyLearner

class LearnerAdmin(UserAdmin):
    form = LearnerChangeForm
    add_form = LearnerCreationForm

    fieldsets = (
        ("Personal info",   {"fields": ("first_name", "last_name", "email", "mobile")}),
        ("Access",          {"fields": ("username", "password", "is_active")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
"""








class SystemAdministratorAdmin(UserAdmin):
    # The forms to add and change user instances
    form = SystemAdministratorChangeForm
    add_form = SystemAdministratorCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', )
    #list_filter = ('is_admin',)
    fieldsets = (
        ("Personal info",   {"fields": ("first_name", "last_name", "email", "mobile")}),
        ("Access",          {"fields": ("username", "password", "is_active")}),
        ("Permissions",     {"fields": ("is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class SchoolManagerAdmin(UserAdmin):
    # The forms to add and change user instances
    form = SchoolManagerChangeForm
    add_form = SchoolManagerCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', )
    #list_filter = ('is_admin',)
    fieldsets = (
        ("Personal info",   {"fields": ("first_name", "last_name", "email", "mobile")}),
        ("Access",          {"fields": ("username", "password", "is_active")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class CourseManagerAdmin(UserAdmin):
    # The forms to add and change user instances
    form = CourseManagerChangeForm
    add_form = CourseManagerCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', )
    #list_filter = ('is_admin',)
    fieldsets = (
        ("Personal info",   {"fields": ("first_name", "last_name", "email", "mobile")}),
        ("Access",          {"fields": ("username", "password", "is_active")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class CourseMentorAdmin(UserAdmin):
    # The forms to add and change user instances
    form = CourseMentorChangeForm
    add_form = CourseMentorCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', )
    #list_filter = ('is_admin',)
    fieldsets = (
        ("Personal info",   {"fields": ("first_name", "last_name", "email", "mobile")}),
        ("Access",          {"fields": ("username", "password", "is_active")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class LearnerAdmin(UserAdmin):
    # The forms to add and change user instances
    form = LearnerChangeForm
    add_form = LearnerCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', )
    #list_filter = ('is_admin',)
    fieldsets = (
        ("Personal info",   {"fields": ("first_name", "last_name", "email", "mobile")}),
        ("Access",          {"fields": ("username", "password", "is_active")}),
        ("Important dates", {"fields": ("last_login", "date_joined")})
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


# Auth
admin.site.unregister(Group)
admin.site.register(SystemAdministrator, SystemAdministratorAdmin)
admin.site.register(SchoolManager, SchoolManagerAdmin)
admin.site.register(CourseManager, CourseManagerAdmin)
admin.site.register(CourseMentor, CourseMentorAdmin)
admin.site.register(Learner, LearnerAdmin)
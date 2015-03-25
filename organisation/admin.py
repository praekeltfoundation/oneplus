from django.contrib import admin
from .models import *
from gamification.models import GamificationScenario


class SchoolInline(admin.TabularInline):
    model = School
    extra = 1
    fields = ("name", "description")
    ordering = ("name", )


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ("name", "description", "order")
    ordering = ("order", )


class CourseModuleInline(admin.TabularInline):
    model = CourseModuleRel
    extra = 1


class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description"]}),
        ("Contact Information", {"fields": ["website", "email"]}),
    ]
    inlines = (SchoolInline,)
    ordering = ("name", )


class SchoolAdmin(admin.ModelAdmin):
    list_display = ("organisation", "name", "description")
    list_filter = ("organisation", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,
            {"fields": ["name", "description", "organisation"]}),
        ("Contact Information", {"fields": ["website", "email"]}),
    ]
    ordering = ("organisation", "name")


class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description", "slug"]})
    ]
    inlines = (CourseModuleInline, )
    ordering = ("name", )


class ModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "order", "get_scenarios", "get_courses", "is_active")
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description", "order", "is_active"]})
    ]
    ordering = ("name", "order")

    def get_courses(self, obj):
        return ", ".join([m.name for m in obj.courses.all()])

    get_courses.short_description = 'Courses'

    def get_scenarios(self, obj):
        return ", ".join([s.module.name for s in GamificationScenario.objects.filter(module=obj)])

    get_scenarios.short_description = 'Scenarios'

# Organisation
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Module, ModuleAdmin)
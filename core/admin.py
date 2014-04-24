from django.contrib import admin
from core.models import *
from django_summernote.admin import *


class SchoolInline(admin.TabularInline):
    model = School
    extra = 1
    fields = ("name", "description")
    ordering = ("name", )


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ("name", "description")
    ordering = ("name", )


class PageInline(admin.TabularInline):
    model = Page
    extra = 1
    fields = ("name", "description")
    ordering = ("name", )


class PostInline(admin.TabularInline):
    model = Post
    extra = 1
    fields = ("name", "description")
    ordering = ("name", )


class LearningChapterInline(admin.TabularInline):
    model = LearningChapter
    extra = 1
    fields = ("order", "name", "description")
    ordering = ("order", "name")


class TestingBankInline(admin.TabularInline):
    model = TestingBank
    extra = 1
    fields = ("order", "name", "description", "question_order")
    ordering = ("order", "name")

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


class GamificationScenarioInline(admin.TabularInline):
    model = GamificationScenario
    extra = 1
    fields = ("name", "description", "event", "point", "badge")
    ordering = ("name", )


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1
    #fields = ("learner", "classs", "datejoined", "points", "pointbonus", "badgetemplate")
    fieldsets = [
        (None,                  {"fields": ["learner", "classs", "datejoined"]}),
        ("Achievements",        {"fields": ["points", "pointbonus", "badgetemplate"]}),
    ]
    filter_vertical = ("pointbonus", "badgetemplate")


class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description"]}),
        ("Contact Information", {"fields": ["website", "email"]}),
    ]
    inlines = (SchoolInline,)
    ordering = ("name", )


class SchoolAdmin(admin.ModelAdmin):
    list_display = ("organisation", "name", "description")
    list_filter = ("organisation", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "organisation"]}),
        ("Contact Information", {"fields": ["website", "email"]}),
    ]
    ordering = ("organisation", "name")


class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "slug"]})
    ]
    inlines = (ModuleInline, PageInline, PostInline)
    ordering = ("name", )


class ModuleAdmin(admin.ModelAdmin):
    list_display = ("course", "name", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "course"]})
    ]
    inlines = (LearningChapterInline, TestingBankInline, GamificationScenarioInline)
    ordering = ("course", "name", )

class LearningChapterAdmin(SummernoteModelAdmin):
    list_display = ("module", "order", "name", "description")
    list_filter = ("module", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "module", "order"]}),
        ("Content",             {"fields": ["content"]})
    ]
    ordering = ("module", "order", "name", )


class TestingBankAdmin(SummernoteModelAdmin):
    list_display = ("module", "order", "name", "description")
    list_filter = ("module", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "module", "order"]}),
        ("Content",             {"fields": ["question_order", ]})
    ]
    inlines = (TestingQuestionInline, )
    ordering = ("module", "order", "name", )


class TestingQuestionAdmin(SummernoteModelAdmin):
    list_display = ("bank", "order", "name", "description")
    list_filter = ("bank", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "bank", "order"]}),
        ("Content",             {"fields": ["question_content", "answer_content", "difficulty", "points"]})
    ]
    inlines = (TestingQuestionOptionInline,)
    ordering = ("bank", "order", "name", )


class TestingQuestionOptionAdmin(SummernoteModelAdmin):
    list_display = ("question", "order", "name")
    list_filter = ("question", )
    search_fields = ("name")
    fieldsets = [
        (None,                  {"fields": ["name", "question", "order"]}),
        ("Content",             {"fields": ["content", "correct"]})
    ]
    ordering = ("question", "order", "name", )


class PageAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description"]})
    ]


class PostAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description"]})
    ]


class ClassAdmin(admin.ModelAdmin):
    list_display = ("course", "name", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "course"]}),
        ("Classification",      {"fields": ["type", "startdate", "enddate"]})
    ]
    inlines = (ParticipantInline,)


class LearnerAdmin(admin.ModelAdmin):
    list_display = ("school", "firstname", "lastname")
    list_filter = ("school", )
    search_fields = ("firstname", "lastname")
    fieldsets = [
        (None,                  {"fields": ["firstname", "lastname", "school"]}),
        ("Access",              {"fields": ["username", "password"]})
    ]
    inlines = (ParticipantInline,)


class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description"]})
    ]


class GamificationPointBonusAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "image", "value"]})
    ]


class GamificationBadgeTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "image"]})
    ]


# Structures
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(School, SchoolAdmin)

admin.site.register(Course, CourseAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Learner, LearnerAdmin)

# Content
admin.site.register(LearningChapter, LearningChapterAdmin)
admin.site.register(TestingQuestion, TestingQuestionAdmin)

#Gamification
admin.site.register(GamificationPointBonus, GamificationPointBonusAdmin)
admin.site.register(GamificationBadgeTemplate, GamificationBadgeTemplateAdmin)

# Communication
admin.site.register(Page, PageAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Discussion, DiscussionAdmin)
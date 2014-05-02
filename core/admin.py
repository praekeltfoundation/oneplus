from django.contrib import admin
from core.models import *

"""
class PageInline(admin.TabularInline):
    model = Page
    extra = 1
    fields = ("name", "description")
    ordering = ("name", )


class PostInline(admin.TabularInline):
    model = Post
    extra = 1
    fields = ("name", "description", "publishdate")
    ordering = ("publishdate", "name")


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


class GamificationScenarioInline(admin.TabularInline):
    model = GamificationScenario
    extra = 1
    fields = ("name", "description", "event", "point", "badge")
    ordering = ("name", )



"""


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1
    #fields = ("learner", "classs", "datejoined", "points", "pointbonus", "badgetemplate")
    fieldsets = [
        (None,                  {"fields": ["learner", "classs", "datejoined"]}),
        ("Achievements",        {"fields": ["points", "pointbonus", "badgetemplate"]}),
    ]
    filter_vertical = ("pointbonus", "badgetemplate")


class ClassAdmin(admin.ModelAdmin):
    list_display = ("course", "name", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None,                  {"fields": ["name", "description", "course"]}),
        ("Classification",      {"fields": ["type", "startdate", "enddate"]})
    ]
    inlines = (ParticipantInline,)


# Organisation
admin.site.register(Class, ClassAdmin)






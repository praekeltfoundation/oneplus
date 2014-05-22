from django.contrib import admin
from core.models import *


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1
    #fields = ("learner", "classs", "datejoined", "points", "pointbonus", "badgetemplate")
    fieldsets = [
        (None,                  {"fields": ["learner", "classs", "datejoined"]}),
        #("Achievements",        {"fields": ["points", "pointbonus", "badgetemplate"]}),
    ]
    #filter_vertical = ("pointbonus", "badgetemplate")


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






from django.contrib import admin
from core.models import *


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1
    fieldsets = [
        (None,
            {"fields": ["learner", "classs", "datejoined"]}),
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


class ParticipantQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ("participant", "question", "option_selected","correct")
    list_filter = ("participant", "question")
    search_fields = ("participant",)
    inline = (ParticipantInline,)


# Organisation
admin.site.register(Class, ClassAdmin)
admin.site.register(ParticipantQuestionAnswer,ParticipantQuestionAnswerAdmin)
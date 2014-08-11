from django.contrib import admin
from core.models import *

from core.filters import FirstNameFilter, LastNameFilter, MobileFilter, \
    ParticipantFirstNameFilter, ParticipantLastNameFilter, \
    ParticipantMobileFilter


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1
    raw_id_fields = ('learner',)
    readonly_fields = ('get_firstname', 'get_lastname', 'get_mobile')
    exclude = ('points',)


    def get_firstname(self, obj):
        return obj.learner.first_name
    get_firstname.short_description = 'First Name'
    get_firstname.admin_order_field = 'learner__first_name'


    def get_lastname(self, obj):
        return obj.learner.last_name
    get_lastname.short_description = 'Last Name'
    get_lastname.admin_order_field = 'learner__last_name'

    def get_mobile(self, obj):
        return obj.learner.mobile
    get_mobile.short_description = 'Mobile'
    get_mobile.admin_order_field = 'learner__mobile'


class ClassAdmin(admin.ModelAdmin):
    list_display = ("course", "name", "description")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description", "course"]}),
        ("Classification", {"fields": ["type", "startdate", "enddate"]})
    ]
    inlines = (ParticipantInline,)


class ParticipantQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "participant",
        "get_firstname",
        "get_lastname",
        "get_mobile",
        "question",
        "answerdate",
        "option_selected",
        "correct")
    list_filter = (
        "participant",
        "question",
        FirstNameFilter,
        LastNameFilter,
        MobileFilter)
    search_fields = ('participant__learner__first_name',
                     'participant__learner__last_name',
                     'participant__learner__mobile')
    inline = (ParticipantInline,)

    def get_firstname(self, obj):
        return obj.participant.learner.first_name
    get_firstname.short_description = 'First Name'
    get_firstname.admin_order_field = 'participant__learner__first_name'

    def get_lastname(self, obj):
        return obj.participant.learner.last_name
    get_lastname.short_description = 'Last Name'
    get_lastname.admin_order_field = 'participant__learner__last_name'

    def get_mobile(self, obj):
        return obj.participant.learner.mobile
    get_mobile.short_description = 'Mobile'
    get_mobile.admin_order_field = 'participant__learner__mobile'


class ParticipantPointInline(admin.TabularInline):
    model = Participant.pointbonus.through
    list_display = ("pointbonus", "scenario")


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("learner","get_firstname",
        "get_lastname", "classs" '')
    list_filter = (
        "learner",
        "classs",
        ParticipantFirstNameFilter,
        ParticipantLastNameFilter,
        ParticipantMobileFilter)
    search_fields = ("learner",)
    inlines = [ParticipantPointInline, ]

    def get_firstname(self, obj):
        return obj.learner.first_name
    get_firstname.short_description = 'First Name'
    get_firstname.admin_order_field = 'learner__first_name'

    def get_lastname(self, obj):
        return obj.learner.last_name
    get_lastname.short_description = 'Last Name'
    get_lastname.admin_order_field = 'learner__last_name'


# Organisation
admin.site.register(Class, ClassAdmin)
admin.site.register(ParticipantQuestionAnswer, ParticipantQuestionAnswerAdmin)
admin.site.register(Participant, ParticipantAdmin)

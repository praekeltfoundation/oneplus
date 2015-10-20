from django.contrib import admin
from core.models import *
from core.forms import ParticipantCreationForm, MoveParticipantsForm
from core.filters import FirstNameFilter, LastNameFilter, MobileFilter, \
    ParticipantFirstNameFilter, ParticipantLastNameFilter, \
    ParticipantMobileFilter, ParticipantFilter, LearnerFilter
from django import template
from django.shortcuts import render_to_response


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
    list_display = ("course", "name", "description", "is_active")
    list_filter = ("course", )
    search_fields = ("name", "description")
    fieldsets = [
        (None, {"fields": ["name", "description", "course", "province"]}),
        ("Classification", {"fields": ["type", "startdate", "enddate"]})
    ]
    inlines = (ParticipantInline,)

    def deactivate_class(self, request, queryset):
        for q in queryset:
            class_id = q.id
            Participant.objects.filter(classs__id=class_id).update(is_active=False)
        queryset.update(is_active=False)
    deactivate_class.short_description = "Deactivate Class"

    def activate_class(self, request, queryset):
        for q in queryset:
            class_id = q.id
            class_participants = Participant.objects.filter(classs__id=class_id)
            for cp in class_participants:
                if not Participant.objects.filter(learner=cp.learner, is_active=True):
                    cp.is_active = True
                    cp.save()
        queryset.update(is_active=True)
    activate_class.short_description = "Activate Class"

    actions = [activate_class, deactivate_class]


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
        ParticipantFilter,
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


def change_class(modeladmin, request, queryset):
    form = None

    if 'apply' in request.POST:
        form = MoveParticipantsForm(request.POST)

        if form.is_valid():
            classs_id = form.cleaned_date["classs"]

            try:
                classs = Class.objects.get(id=classs_id)
            except Class.DoesNotExist:
                return render_to_response(
                    'admin/core/move_participants.html',
                    {
                        'move_participants_form': form,
                        'participants': queryset
                    },
                    context_instance=template.RequestContext(request)
                )

            queryset.update(classs=classs)

            return render_to_response(
                'admin/core/move_participants_result',
                {
                    'redirect': request.get_full_path(),
                },
            )

    if not form:
        form = MoveParticipantsForm(
            initial={
                '_selected_action': request.POST.getlist(
                    admin.ACTION_CHECKBOX_NAME,
                ),
            }
        )
    return render_to_response(
        'admin/core/move_participants.html',
        {
            'move_participants_form': form,
            'participants': queryset
        },
        context_instance=template.RequestContext(request)
    )
change_class.short_description = "Move selected participants to a different class"


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("learner", "get_firstname", "get_lastname", "classs", "is_active")
    list_filter = (
        LearnerFilter,
        "classs",
        ParticipantFirstNameFilter,
        ParticipantLastNameFilter,
        ParticipantMobileFilter)
    search_fields = ("learner__first_name", "learner__last_name")
    inlines = [ParticipantPointInline, ]
    form = ParticipantCreationForm
    add_form = ParticipantCreationForm

    def get_firstname(self, obj):
        return obj.learner.first_name
    get_firstname.short_description = 'First Name'
    get_firstname.admin_order_field = 'learner__first_name'

    def get_lastname(self, obj):
        return obj.learner.last_name
    get_lastname.short_description = 'Last Name'
    get_lastname.admin_order_field = 'learner__last_name'

    actions = [change_class]


class SettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value")

# Organisation
admin.site.register(Class, ClassAdmin)
admin.site.register(ParticipantQuestionAnswer, ParticipantQuestionAnswerAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Setting, SettingAdmin)

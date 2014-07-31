from datetime import datetime, timedelta
from django.db.models import Count
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from auth.models import Learner


class FirstNameFilter(admin.SimpleListFilter):
    title = _('First Name')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'first_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__learner__id=self.value())


class LastNameFilter(admin.SimpleListFilter):
    title = _('Last Name')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'last_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__learner__id=self.value())


class MobileFilter(admin.SimpleListFilter):
    title = _('Mobile')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'mobile')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__learner__id=self.value())


class ParticipantFirstNameFilter(admin.SimpleListFilter):
    title = _('First Name')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'first_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(learner__id=self.value())


class ParticipantLastNameFilter(admin.SimpleListFilter):
    title = _('Last Name')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'last_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(learner__id=self.value())


class ParticipantMobileFilter(admin.SimpleListFilter):
    title = _('Mobile')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'mobile')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(learner__id=self.value())

from datetime import datetime, timedelta
from django.db.models import Count
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
import operator

from auth.models import Learner


class ParticipantFilter(admin.SimpleListFilter):
    title = _('Participant')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        result = set([c.learner for c in Learner.objects.all()])
        return [(c.id, c.first_name + ' ' + c.last_name)
                for c in sorted(result,key=operator.attrgetter('first_name'))]


    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__learner__id=self.value())


class FirstNameFilter(admin.SimpleListFilter):
    title = _('First Name')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'first_name').order_by('first_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__learner__id=self.value())


class LastNameFilter(admin.SimpleListFilter):
    title = _('Last Name')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'last_name').order_by('last_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__learner__id=self.value())


class MobileFilter(admin.SimpleListFilter):
    title = _('Mobile')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'mobile').order_by('mobile')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__learner__id=self.value())


class LearnerFilter(admin.SimpleListFilter):
    title = _('Learner')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        result = set([c.learner for c in Learner.objects.all()])
        return [(c.id, c.first_name + ' ' + c.last_name)
                for c in sorted(result,key=operator.attrgetter('first_name'))]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(learner__id=self.value())

class ParticipantFirstNameFilter(admin.SimpleListFilter):
    title = _('First Name')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'first_name').order_by('first_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(learner__id=self.value())


class ParticipantLastNameFilter(admin.SimpleListFilter):
    title = _('Last Name')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'last_name').order_by('last_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(learner__id=self.value())


class ParticipantMobileFilter(admin.SimpleListFilter):
    title = _('Mobile')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Learner.objects.all().values_list('id', 'mobile').order_by('mobile')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(learner__id=self.value())

from datetime import datetime, timedelta
from django.db.models import Count
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from organisation.models import Course
from core.models import Participant, ParticipantQuestionAnswer


class CourseFilter(admin.SimpleListFilter):
    title = _('Course')
    parameter_name = 'id'

    def lookups(self, request, model_admin):
        return Course.objects.all().values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(participant__classs__course_id=self.value())


class AirtimeFilter(admin.SimpleListFilter):
    title = _('Airtime')
    parameter_name = 'name'

    def get_date_range(self):
        today = datetime.today()
        start = today - timedelta(days=today.weekday(), weeks=1)
        end = start + timedelta(days=7)
        return [start, end]

    def get_learner_ids(self):
        participants = ParticipantQuestionAnswer.objects.filter(
            answerdate__range=self.get_date_range(),
            correct=True
        ).values('participant').annotate(Count('participant'))

        filtered_participants = participants.filter(
            participant__count__gte=9
        ).values('participant')

        return Participant.objects.filter(
            id__in=filtered_participants
        ).values_list('learner', flat=True)

    def lookups(self, request, model_admin):
        return [('airtime_award', _('9 to 15 questions correct'))]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            if self.value() == 'airtime_award':
                learners = self.get_learner_ids()
                return queryset.filter(id__in=learners)
            else:
                return queryset

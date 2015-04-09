from core.models import Participant, ParticipantQuestionAnswer
from datetime import datetime, timedelta
from django.db.models import Count


def participants_registered_last_x_hours(hours):
    dt = datetime.now() - timedelta(hours=hours)
    return Participant.objects.filter(datejoined__gte=dt)\
        .aggregate(Count('id'))['id__count']


def questions_answered_in_last_x_hours(hours):
    dt = datetime.now() - timedelta(hours=hours)
    return ParticipantQuestionAnswer.objects.filter(answerdate__gte=dt)\
        .aggregate(Count('id'))['id__count']


def percentage_questions_answered_correctly_in_last_x_hours(hours):
    dt = datetime.now() - timedelta(hours=hours)
    total = questions_answered_in_last_x_hours(hours=hours)
    correct = ParticipantQuestionAnswer.objects\
        .filter(answerdate__gte=dt, correct=True)\
        .aggregate(Count('id'))['id__count']

    if total > 0:
        return int(correct / float(total) * 100)
    else:
        return 0
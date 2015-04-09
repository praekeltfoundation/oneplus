from datetime import datetime, timedelta
from django.db.models import Count
from .models import Learner


def learners_active_in_last_x_hours(hours):
    dt = datetime.now() - timedelta(hours=hours)
    return Learner.objects.filter(last_active_date__gte=dt)\
        .aggregate(Count('id'))['id__count']


def total_active_learners():
    return Learner.objects.filter(is_active=True)\
        .aggregate(Count('id'))['id__count']


def percentage_learner_sms_opt_ins():
    total = total_active_learners()
    cnt = Learner.objects.filter(is_active=True, optin_sms=True)\
        .aggregate(Count('id'))['id__count']
    if total > 0:
        return int(cnt / float(total) * 100)
    else:
        return 0


def percentage_learner_email_opt_ins():
    total = total_active_learners()
    cnt = Learner.objects.filter(is_active=True, optin_email=True)\
        .aggregate(Count('id'))['id__count']
    if total > 0:
        return int(cnt / float(total) * 100)
    else:
        return 0

from __future__ import absolute_import

from mobileu.celery import app
from go_http import HttpApiSender
from oneplusmvp import settings
from auth.models import Learner
from core.models import ParticipantQuestionAnswer


@app.task
def update_learner_metric():
    update_metric(
        "total.learners",
        Learner.objects.count(),
        "last"
    )


@app.task
def update_active_learner_metric():
    update_metric(
        "active.learners",
        Learner.objects.filter(active=True).count(),
        "last"
    )

@app.task
def update_num_question_metric():
    update_metric(
        "answered.questions",
        ParticipantQuestionAnswer.objects.count(),
        "last"
    )

@app.task
def update_perc_correct_answers():
    total = ParticipantQuestionAnswer.objects.count()
    if total > 0:
        value = ParticipantQuestionAnswer.objects.filter(
            correct=True
        ).count()/total
    else:
        value = 0
    update_metric(
        "percentage.correct",
        value,
        "last"
    )

@app.task
def update_metric(name, value, metric_type):
    sender = HttpApiSender(
        account_key=settings.VUMI_GO_ACCOUNT_KEY,
        conversation_key=settings.VUMI_GO_CONVERSATION_KEY,
        conversation_token=settings.VUMI_GO_ACCOUNT_TOKEN
    )
    sender.fire_metric(name, value, agg=metric_type)
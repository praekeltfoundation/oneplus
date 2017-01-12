import logging

from datetime import datetime, timedelta

from auth.models import Learner

from content.models import SUMit

from core.models import Class, Participant

from django.core.mail import mail_managers

from django.core.management import call_command

from djcelery import celery

from teacher_report import send_teacher_reports_body

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@celery.task
def send_sms(x, y):
    return x + y


@celery.task
def send_teacher_reports():
    send_teacher_reports_body()


@celery.task
def send_sumit_counts():
    send_sumit_counts_body()


def send_sumit_counts_body():
    today = datetime.now()
    sumits = SUMit.objects.filter(activation_date__gt=today,
                                  activation_date__lt=today + timedelta(hours=48))
    is_insufficient = False
    message = 'SUMits with insufficient questions:\n'
    for s in sumits:
        counts = s.get_question_counts()
        if counts['easy'] < 15 or counts['normal'] < 11 or counts['advanced'] < 5:
            is_insufficient = True
            message += s.name + ': activating ' + s.activation_date.strftime('%Y-%m-%d %H:%M') + '\n'
    if is_insufficient:
        try:
            mail_managers(subject='DIG-IT: SUMits with too few questions', message=message, fail_silently=False)
        except Exception as ex:
            logger.error("Error while sending email:\nmsg: %s\nError: %s" % (message, ex))


@celery.task
def run_haystack_update():
    run_haystack_update_body()


def run_haystack_update_body():
    call_command('update_index')


@celery.task
def run_haystack_rebuild():
    run_haystack_update_body()


def run_haystack_rebuild_body():
    call_command('rebuild_index', '--noinput')


@celery.task
def grade_up():
    grade_up_body()


def grade_up_body():
    valid_grades = ['Grade 10', 'Grade 11', 'Grade 12', 'Graduate']

    # set i to 2nd last index
    i = (len(valid_grades) - 1) - 1
    while i >= 0:
        grade = valid_grades[i]
        old_participants = Participant.objects.filter(learner__grade=grade, is_active=True)
        old_participants.update(is_active=False)
        learners = Learner.objects.filter(grade=grade, is_active=True)
        learners.update(grade=valid_grades[i+1])
        i -= 1

    for grade in valid_grades[:-1]:
        learners = Learner.objects.filter(grade=grade, is_active=True)
        for learner in learners:
            Class.get_or_create_class(grade, learner.school).create_participant(learner)

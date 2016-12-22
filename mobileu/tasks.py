import logging

from datetime import datetime, timedelta

from content.models import SUMit

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
    call_command('update_index', '--remove')
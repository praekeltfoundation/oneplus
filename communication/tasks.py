from __future__ import absolute_import

from mobileu.celery import app
from go_http import HttpApiSender
from django.conf import settings
from datetime import datetime
from django.core.mail import mail_managers
from .models import SmsQueue
from communication.utils import JunebugApi, SmsSender


@app.task
def update_metric(name, value, metric_type):
    sender = HttpApiSender(
        username=settings.JUNEBUG_USERNAME,
        password=settings.JUNEBUG_PASSWORD,
        api_url=settings.JUNEBUG_BASE_URL+settings.JUNEBUG_CHANNEL_ID+settings.JUNEBUG_ACCOUNT_NUMBER)
    sender.fire_metric(name, value, agg=metric_type)


@app.task
def send_sms(msisdn, message):
    sms_sender = SmsSender()
    sms_sender.send(msisdn, settings.JUNEBUG_FAKE, message)


@app.task(default_retry_delay=300, max_retries=5)
def bulk_send_all(queryset, message):
    junebug_api = JunebugApi()
    successful, fail = junebug_api.send_all(queryset, message)
    subject = 'Junebug SMS Send'
    message = "\n".join([
        "Message: " + message,
        "Time: " + str(datetime.now()),
        "Successful sends: " + str(successful),
        "Failures: " + ", ".join(fail)
    ])

    mail_managers(
        subject=subject,
        message=message,
        fail_silently=False
    )

    return successful, fail


@app.task
def process_sms_queue():
    dt = datetime.now()
    smses = SmsQueue.objects.filter(sent=False, send_date__lt=dt)
    junebug_api = JunebugApi()

    for sms in smses:
        dt = datetime.now()
        obj, sent = junebug_api.send(sms.msisdn, sms.message, None, None)

        if sent:
            sms.sent = True
            sms.sent_date = dt
            sms.save()

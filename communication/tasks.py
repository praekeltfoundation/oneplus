from __future__ import absolute_import

from mobileu.celery import app
from go_http import HttpApiSender
from django.conf import settings
from communication.utils import VumiSmsApi
from datetime import datetime
from django.core.mail import mail_managers

@app.task
def update_metric(name, value, metric_type):
    sender = HttpApiSender(
        account_key=settings.VUMI_GO_ACCOUNT_KEY,
        conversation_key=settings.VUMI_GO_CONVERSATION_KEY,
        conversation_token=settings.VUMI_GO_ACCOUNT_TOKEN
    )
    sender.fire_metric(name, value, agg=metric_type)


@app.task
def send_sms(msisdn, message, password, autologin):
    vumi_api = VumiSmsApi()
    sms, sent = vumi_api.send(msisdn, message, password, autologin)


@app.task(default_retry_delay=300, max_retries=5)
def bulk_send_all(queryset, message):
    vumi_api = VumiSmsApi()
    successful, fail = vumi_api.send_all(queryset, message)
    subject = 'Vumi SMS Send'
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
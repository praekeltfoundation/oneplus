from go_http import HttpApiSender, LoggingSender
from django.conf import settings
from datetime import datetime
from celery import task
import requests


def update_metric(name, value, metric_type):
    try:
        if hasattr(settings, 'JUNEBUG_FAKE') and settings.JUNEBUG_FAKE:
            sender = LoggingSender('DEBUG')
            sender.fire_metric(name, value, agg=metric_type.lower())
        else:
            async_sender.delay(name, value, metric_type)
    except requests.exceptions.RequestException as e:
        pass


@task()
def async_sender(name, value, metric_type):
    try:
        if hasattr(settings, 'VUMI_METRICS_ON') and settings.VUMI_METRICS_ON:
            sender = HttpApiSender(
                account_key=settings.VUMI_GO_ACCOUNT_KEY,
                conversation_key=settings.VUMI_GO_CONVERSATION_KEY,
                conversation_token=settings.VUMI_GO_ACCOUNT_TOKEN
            )
            sender.fire_metric(name, value, agg=metric_type)
    except requests.exceptions.RequestException as e:
        pass


def get_today():
    return datetime.today()

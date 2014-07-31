from go_http import HttpApiSender
import oneplusmvp.settings as settings
from datetime import datetime
import requests


def update_metric(name, value, metric_type):
    try:
        sender = HttpApiSender(
            account_key=settings.VUMI_GO_ACCOUNT_KEY,
            conversation_key=settings.VUMI_GO_CONVERSATION_KEY,
            conversation_token=settings.VUMI_GO_ACCOUNT_TOKEN
        )
        sender.fire_metric(name, value, agg=metric_type)
    except requests.exceptions.RequestException as e:
        pass

# So can be overridden in tests.


def get_today():
    return datetime.today()

from go_http import HttpApiSender
import oneplusmvp.settings as settings

def update_metric(name, value, metric_type):
    sender = HttpApiSender(
        account_key=settings.VUMI_GO_ACCOUNT_KEY,
        conversation_key=settings.VUMI_GO_CONVERSATION_KEY,
        conversation_token=settings.VUMI_GO_ACCOUNT_TOKEN
    )
    sender.fire_metric(name, value, agg=metric_type)

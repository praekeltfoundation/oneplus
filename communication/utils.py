from django.conf import settings
import json
from communication.models import Sms
import requests
from django.contrib.sites.models import Site
from go_http import HttpApiSender

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_autologin_link(unique_token):
    if unique_token is not None:
        return 'http://%s/%s/%s' % (
            Site.objects.get_current().domain,
            'a',
            unique_token
        )
    else:
        return None

class VumiSmsApi:
    """Sends vumi http api requests"""
    def __init__(self):
        self.conversation_key = settings.VUMI_GO_CONVERSATION_KEY
        self.account_key = settings.VUMI_GO_ACCOUNT_KEY
        self.account_token = settings.VUMI_GO_ACCOUNT_TOKEN

        self.sender = HttpApiSender(
            account_key=settings.VUMI_GO_ACCOUNT_KEY,
            conversation_key=settings.VUMI_GO_CONVERSATION_KEY,
            conversation_token=settings.VUMI_GO_ACCOUNT_TOKEN
        )

    def templatize(self, message, password, autologin):
        if password is not None:
            message = message.replace("|password|", password)
        if autologin is not None:
            message = message.replace("|autologin|", autologin)
        return message

    def save_sms_log(self, uuid, message, timestamp, msisdn):
        # Create sms object
        sms = Sms.objects.create(
            uuid=uuid,
            message=message,
            date_sent=timestamp,
            msisdn=msisdn
        )
        sms.save()
        return sms

    def send(self, msisdn, message, password, autologin):
        #Send the url
        message = self.templatize(message, password, autologin)

        try:
            response = self.sender.send_text(to_addr=msisdn, content=message)
        except requests.exceptions.RequestException as e:
            sent = False
            logger.error(e)
            return None, sent

        if u'success' in response.keys() and response[u'success'] is False:
            sms = self.save_sms_log(response[u'success'], message,
                                    None, msisdn)
            sent = False
        else:
            sms = self.save_sms_log(response[u'message_id'], message,
                                    response[u'timestamp'], msisdn)
            sent = True

        return sms, sent



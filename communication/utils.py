from django.conf import settings
import json
import base64
from communication.models import Sms
import requests


class VumiSmsApi:
    """Sends vumi http api requests"""
    def __init__(self):
        self.conversation_key = settings.VUMI_GO_CONVERSATION_KEY
        self.account_key = settings.VUMI_GO_ACCOUNT_KEY
        self.account_token = settings.VUMI_GO_ACCOUNT_TOKEN

    def templatize(self, message, password, autologin):
        if password is not None:
            message.replace("|password|", password)
        if autologin is not None:
            message.replace("|autologin|", autologin)
        return message

    def get_sms_url(self):
        return "/".join((
            settings.VUMI_GO_BASE_URL,
            self.account_key,
            'messages.json'
        ))

    def get_auth_string(self):
        auth = base64.encodestring(
            '%s:%s' % (self.conversation_key, self.account_token)
        ).replace('\n', '')
        return "Basic %s" % auth

    def send(self, msisdn, message, password, autologin):
        #Send the url
        url = self.get_request_url()
        message = self.templatize(message, password, autologin)

        #Headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        #create request data
        data = json.dumps({
            "in_reply_to": None,
            "session_event": None,
            "to_addr": msisdn,
            "content": message,
            "transport_type": "sms",
            "transport_metadata": {},
            "helper_metadata": {}
        })

        #Create request
        response = requests.put(
            url,
            data=data,
            headers=headers,
            auth=(self.conversation_key, self.account_token)
        ).json()

        if response.success is True:
            # Create sms object
            sms = Sms.objects.create(
                identifier=response.message_id,
                message=message,
                date_sent=response.timestamp,
                status='sent'
            )
            sms.save()
        else:
            # Create sms object
            sms = Sms.objects.create(
                identifier="",
                message=message,
                status=response.reason
            )
            sms.save()



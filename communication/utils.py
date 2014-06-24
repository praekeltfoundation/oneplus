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
            message = message.replace("|password|", password)
        if autologin is not None:
            message = message.replace("|autologin|", autologin)
        return message

    def get_sms_url(self):
        return "/".join((
            settings.VUMI_GO_BASE_URL,
            self.conversation_key,
            'messages.json'
        ))


    def send(self, msisdn, message, password, autologin):
        #Send the url
        url = self.get_sms_url()
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
            auth=(self.account_key, self.account_token)
        )

        response = response.json()

        if u'success' in response.keys() and response[u'success'] is not False:
            # Create sms object
            sms = Sms.objects.create(
                identifier="",
                message=message,
                status=response.reason
            )
            sms.save()
        else:
            # Create sms object
            sms = Sms.objects.create(
                identifier=response[u'message_id'],
                message=message,
                date_sent=response[u'timestamp'],
                status='sent'
            )
            sms.save()



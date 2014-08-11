from django.conf import settings
from communication.models import Sms
import requests
from django.contrib.sites.models import Site
from go_http import HttpApiSender, LoggingSender
import koremutake
from django.contrib.auth.hashers import make_password
from random import randint
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

        if hasattr(settings, 'VUMI_GO_FAKE') and settings.VUMI_GO_FAKE:
            self.sender = LoggingSender(
                'DEBUG'
            )
        else:
            self.sender = HttpApiSender(
                account_key=settings.VUMI_GO_ACCOUNT_KEY,
                conversation_key=settings.VUMI_GO_CONVERSATION_KEY,
                conversation_token=settings.VUMI_GO_ACCOUNT_TOKEN
            )

    def prepare_msisdn(self, msisdn):
        if msisdn.startswith('+'):
            return msisdn
        else:
            if msisdn.startswith('27'):
                return '+' + msisdn
            elif msisdn.startswith('0'):
                return '+27' + msisdn[1:]


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
        # Send the url
        message = self.templatize(message, password, autologin)
        msisdn = self.prepare_msisdn(msisdn)
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

    def send_all(self, queryset, message):
        # Check if a password or autologin message
        is_welcome_message = False
        is_autologin_message = False
        if "|password|" in message:
            is_welcome_message = True
        if "|autologin|" in message:
            is_autologin_message = True

        successful = 0
        fail = []
        for learner in queryset:
            password = None
            if is_welcome_message:
                # Generate password
                password = koremutake.encode(randint(10000, 100000))
                learner.password = make_password(password)
            if is_autologin_message:
                # Generate autologin link
                learner.generate_unique_token()
            learner.save()

            # Send sms
            try:
                sms, sent = self.send(
                    learner.username,
                    message=message,
                    password=password,
                    autologin=get_autologin_link(learner.unique_token)
                )
            except:
                sent = False
                pass

            if sent:
                successful += 1
            else:
                fail.append(learner.username)

            # Save welcome message details
            if is_welcome_message and sent:
                learner.welcome_message = sms
                learner.welcome_message_sent = True

            learner.save()

        return successful, fail

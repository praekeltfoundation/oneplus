from django.conf import settings
import requests
from django.contrib.sites.models import Site
from go_http import HttpApiSender, LoggingSender
import koremutake
from django.contrib.auth.hashers import make_password
from random import randint
import logging
from datetime import datetime, timedelta
from .models import Sms, Ban, Profanity, ChatMessage, PostComment, Discussion

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
            sms = self.save_sms_log(False, message, datetime.now(), msisdn)
            sent = False
        else:
            if u"message_id" in response.keys():
                msg_id = response[u"message_id"]
            else:
                msg_id = u"Not in response"

            if u"timestamp" in response.keys():
                ts = response[u"timestamp"]
            else:
                ts = datetime.now()

            sms = self.save_sms_log(msg_id, message, ts, msisdn)
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


def get_user_bans(user):
    today = datetime.now()
    today_start = datetime(today.year, today.month, today.day)

    return Ban.objects.filter(banned_user=user, till_when__gte=today_start)


def moderate(comm):
    comm.moderated = True
    comm.unmoderated_date = None
    comm.unmoderated_by = None
    comm.save()


def unmoderate(comm, user):
    comm.moderated = False
    comm.unmoderated_by = user
    comm.unmoderated_date = datetime.now()
    comm.original_content = comm.content
    comm.content = get_replacement_content(admin_ban=True, num_days=3)
    comm.save()


def contains_profanity(content):
    qs = Profanity.objects.all()

    for prof in qs:
        lprof = prof.word.lower()
        lcontent = content.lower()
        if lprof in lcontent:
            return True

    return False


def get_ban_source_info(obj):
    if isinstance(obj, PostComment):
        return (1, obj.id)
    elif isinstance(obj, Discussion):
        return (2, obj.id)
    elif isinstance(obj, ChatMessage):
        return (3, obj.id)
    else:
        return (None, None)


def ban_user(banned_user, banning_user, obj, num_days):
    today = datetime.now()
    till_when = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)
    (source_type, source_pk) = get_ban_source_info(obj)
    duration = num_days - 1
    till_when = till_when + timedelta(days=duration)

    # don't create duplicate bans
    if not Ban.objects.filter(banned_user=banned_user, till_when=till_when).exists():
        Ban.objects.create(
            banned_user=banned_user,
            banning_user=banning_user,
            till_when=till_when,
            source_type=source_type,
            source_pk=source_pk,
            when=today
        )


def get_replacement_content(admin_ban=False, num_days=1):
    plural = ''

    if num_days > 1:
        plural = 's'

    if admin_ban:
        msg = 'This comment has been reported by a moderator and the user has ' \
              'been banned from commenting for %d day%s.' % (num_days, plural)
    else:
        msg = 'This comment has been reported by the community and the user has ' \
              'been banned from commenting for %d day%s.' % (num_days, plural)

    return msg


def report_user_post(obj, banning_user, num_days):
    obj.unmoderated_by = banning_user
    obj.unmoderated_date = datetime.now()
    obj.original_content = obj.content
    obj.content = get_replacement_content(admin_ban=False, num_days=num_days)
    obj.save()

    ban_user(
        banned_user=obj.author,
        banning_user=banning_user,
        obj=obj,
        num_days=num_days
    )
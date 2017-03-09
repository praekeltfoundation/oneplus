from import_export import resources
from communication.models import SmsQueue


class SmsQueueResource(resources.ModelResource):

    class Meta:
        model = SmsQueue
        fields = (
            'message',
            'msisdn',
            'sent',
            'sent_date',
        )
        export_order = (
            'msisdn',
            'sent',
            'sent_date',
            'message',
        )

    def dehydrate_sent_date(self, sms):
        if sms.sent_date:
            return str(sms.sent_date)
        return ''


class SmsResource(resources.ModelResource):

    class Meta:
        model = SmsQueue
        fields = (
            'message',
            'msisdn',
            'respond_date',
            'responded',
            'response',
            'sent',
            'date_sent',
            'uuid',
        )
        export_order = (
            'msisdn',
            'uuid',
            'sent',
            'date_sent',
            'message',
            'responded',
            'respond_date',
            'response',
        )

    def dehydrate_date_sent(self, sms):
        if sms.sent_date:
            return str(sms.date_sent)
        return ''

    def dehydrate_respond_date(self, sms):
        if sms.respond_date:
            return str(sms.respond_date)
        return ''

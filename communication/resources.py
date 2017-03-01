from import_export import resources
from communication.models import SmsQueue


class SmsQueueResource(resources.ModelResource):

    class Meta:
        model = SmsQueue
        fields = (
            'message',
            'sent_date',
            'msisdn',
            'sent',
            'sent_date',
        )
        export_order = (
            'message',
            'sent_date',
            'msisdn',
            'sent',
            'sent_date',
        )

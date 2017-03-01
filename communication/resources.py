from import_export import resources
from communication.models import SmsQueue


class SmsQueueResource(resources.ModelResource):

    class Meta:
        model = SmsQueue
        fields = (
            'message',
            'sent_id',
            'msisdn',
            'sent',
            'sent_date',
        )
        export_order = (
            'sent_id',
            'message',
            'msisdn',
            'sent',
            'sent_date',
        )

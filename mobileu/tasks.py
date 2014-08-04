from djcelery import celery

@celery.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@celery.task
def send_sms(x, y):
    return x + y
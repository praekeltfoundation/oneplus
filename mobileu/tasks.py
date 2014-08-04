from mobileu.celery import app


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task
def send_sms(x, y):
    return x + y
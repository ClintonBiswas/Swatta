from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rongdhonu.settings')

app = Celery('rongdhonu')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.timezone = 'Asia/Dhaka'
app.conf.enable_utc = False
app.conf.beat_schedule = {
    'check-scheduled-messages-every-minute': {
        'task': 'product.tasks.process_scheduled_messages',
        'schedule': crontab(minute='*'), 
    },
}
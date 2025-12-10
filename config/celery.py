import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-scheduled-alerts-every-minute': {
        'task': 'alerts.tasks.check_scheduled_alerts',
        'schedule': crontab(minute='*'),
    },
}

app.conf.timezone = 'America/Sao_Paulo'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
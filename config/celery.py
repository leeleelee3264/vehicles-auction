"""
Celery configuration for vehicle auction project.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('vehicle_auction')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# Scheduled tasks (Celery Beat)
app.conf.beat_schedule = {
    # 1분마다 경매 종료 체크
    'check-expired-auctions': {
        'task': 'apps.auctions.tasks.check_expired_auctions',
        'schedule': crontab(minute='*/1'),  # 1분마다 실행
    }
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
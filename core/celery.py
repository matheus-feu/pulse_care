import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('pulse_care')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f'Celery debug task invoked {self.request}')

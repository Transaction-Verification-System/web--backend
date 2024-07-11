from celery import Celery
import os
from kombu import Queue


os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_site.settings')

app = Celery('my_site')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.task_queues = {
    Queue('queue_1','routing_key'),
    Queue('queue_2','routing_key'),

}
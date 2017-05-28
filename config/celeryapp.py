from __future__ import absolute_import

from celery import Celery

app = Celery('bordercore')

# Celery settings will be retrieved from Django's settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Look for tasks.py in every app listed in INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

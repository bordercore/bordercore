"""Production settings and globals."""

from __future__ import absolute_import

from .base import *

# Elasticsearch config
ELASTICSEARCH_ENDPOINT = "http://ec2-18-209-231-14.compute-1.amazonaws.com:9200"

LOGGING['handlers']['bordercore'] = {
    'level': 'DEBUG',
    'class': 'logging.handlers.RotatingFileHandler',
    'maxBytes': 1024 * 1024 * 10,  # 10MB
    'backupCount': 5,
    'formatter': 'standard',
    'filename': '/var/log/django/bordercore.log'
}

LOGGING['loggers']['django.request'] = {
    'handlers': ['file', 'mail_admins'],
    'level': 'ERROR',
    'propagate': False,
}

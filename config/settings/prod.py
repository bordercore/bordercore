"""Production settings and globals."""

from __future__ import absolute_import

from .base import *


# Elasticsearch config
ELASTICSEARCH_ENDPOINT = "http://ec2-3-220-164-234.compute-1.amazonaws.com:9200"

LOGGING['handlers']['bordercore'] = {
    'level': 'DEBUG',
    'class': 'logging.FileHandler',
    'formatter': 'standard',
    'filename': '/var/log/django/bordercore.log'
}

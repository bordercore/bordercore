"""Production settings and globals."""

from __future__ import absolute_import

from .base import *

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filename='/var/log/django/django.log',)


# Elasticsearch config
ELASTICSEARCH_ENDPOINT = "http://ec2-3-220-164-234.compute-1.amazonaws.com:9200"

"""Production settings and globals."""

from __future__ import absolute_import

from .base import *

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filename='/var/log/django/django.log',)

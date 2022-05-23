"""Production settings and globals."""
from __future__ import absolute_import

import os

from .base import *

LOGGING["handlers"]["bordercore"] = {
    "level": "DEBUG",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": 1024 * 1024 * 10,  # 10MB
    "backupCount": 5,
    "formatter": "standard",
    "filename": "/var/log/django/bordercore.log"
}

LOGGING["handlers"]["disallowed_host"] = {
    "level": "ERROR",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": 1024 * 1024 * 10,  # 10MB
    "backupCount": 5,
    "formatter": "standard",
    "filename": "/var/log/django/disallowed_host.log",
}

LOGGING["loggers"]["django.request"] = {
    "handlers": ["file", "mail_admins"],
    "level": "ERROR",
    "propagate": False,
}

LOGGING["loggers"]["django.security.DisallowedHost"] = {
    "handlers": ["disallowed_host"],
    "level": "ERROR",
    "propagate": False,
}

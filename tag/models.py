from django.db import models

from datetime import datetime


class TimeStampedActivate(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Tag(models.Model):
    name = models.TextField(unique=True)
    created = models.DateTimeField(default=datetime.now())

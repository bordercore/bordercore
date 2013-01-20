import datetime

from django.db import models
from django.contrib.auth.models import User
from datetime import *

class TimeStampedActivate(models.Model):
    created = models.DateTimeField(default=datetime.now)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True

class Feed(TimeStampedActivate):
    name = models.TextField()
    url = models.TextField()
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)
    homepage = models.TextField(null=True)

class FeedItem(models.Model):
    feed = models.ForeignKey(Feed)
    title = models.TextField()
    link = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

from tag.models import Tag


# Should probably put this in a general-purpose file, since it's
#  used in several Bordercore apps
class TimeStampedActivate(models.Model):
    created = models.DateTimeField(default=datetime.now)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Bookmark(TimeStampedActivate):
    url = models.TextField()
    title = models.TextField()
    user = models.ForeignKey(User)
    note = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)

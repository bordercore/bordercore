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


class Todo(TimeStampedActivate):
    task = models.TextField()
    note = models.TextField(null=True)
    url = models.TextField(null=True)
    user = models.ForeignKey(User)
    due_date = models.DateTimeField(null=True)
    tags = models.ManyToManyField(Tag)
    is_urgent = models.BooleanField(default=False)

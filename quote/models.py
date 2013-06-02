from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

# Should probably put this in a general-purpose file, since it's
#  used in several Bordercore apps
class TimeStampedActivate(models.Model):
    created = models.DateTimeField(default=datetime.now)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Quote(TimeStampedActivate):
    quote = models.TextField()
    source = models.TextField()
    user = models.ForeignKey(User)

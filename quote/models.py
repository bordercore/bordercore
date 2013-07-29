from django.contrib.auth.models import User
from django.db import models

from lib.mixins import TimeStampedModel


class Quote(TimeStampedModel):
    quote = models.TextField()
    source = models.TextField()
    user = models.ForeignKey(User)

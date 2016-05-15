from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models

from lib.mixins import TimeStampedModel


class Bookshelf(TimeStampedModel):
    """
    A collection of blobs organized around a common theme or project
    """

    name = models.CharField(max_length=200)
    user = models.ForeignKey(User)
    blob_list = JSONField(blank=True, null=True)

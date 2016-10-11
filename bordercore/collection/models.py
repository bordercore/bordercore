from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Collection(TimeStampedModel):
    """
    A collection of blobs organized around a common theme or project
    """

    name = models.CharField(max_length=200)
    user = models.ForeignKey(User)
    blob_list = JSONField(blank=True, null=True)
    tags = models.ManyToManyField(Tag)
    description = models.TextField(null=True)

    def get_created(self):
        return self.created.strftime('%b %d, %Y')

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

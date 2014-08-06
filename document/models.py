from django.contrib.auth.models import User
from django.db import models

from lib.mixins import TimeStampedModel
from tag.models import Tag

import dbarray

class Document(TimeStampedModel):
    content = models.TextField()
    title = models.TextField(null=True)
    author = dbarray.TextArrayField(blank=True)
    url = models.TextField(null=True)
    user = models.ForeignKey(User)
    note = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])


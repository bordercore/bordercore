from django.contrib.auth.models import User
from django.db import models

import dbarray
from lib.mixins import TimeStampedModel
from tag.models import Tag


class Bookmark(TimeStampedModel):
    url = models.TextField()
    title = models.TextField()
    user = models.ForeignKey(User)
    note = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])


class BookmarkTagUser(models.Model):
    tag = models.ForeignKey(Tag)
    user = models.ForeignKey(User)
    bookmark_list = dbarray.IntegerArrayField()


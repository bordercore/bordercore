from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

import dbarray
from tag.models import Tag

# Should probably put this in a general-purpose file, since it's
#  used in several Bordercore apps
class TimeStampedActivate(models.Model):
    created = models.DateTimeField(auto_now_add=True)
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

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])


class BookmarkTagUser(models.Model):
    tag = models.ForeignKey(Tag)
    user = models.ForeignKey(User)
    bookmark_list = dbarray.IntegerArrayField()


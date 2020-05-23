from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.http import JsonResponse
from django.utils import timezone

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Collection(TimeStampedModel):
    """
    A collection of blobs organized around a common theme or project
    """

    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    blob_list = JSONField(blank=True, null=True)
    tags = models.ManyToManyField(Tag)
    description = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False)

    def get_created(self):
        to_tz = timezone.get_default_timezone()
        return self.created.astimezone(to_tz).strftime("%b %d, %Y")

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def sort(self, blob_id, new_position):

        # First remove the blob from the existing list
        saved_blob = []
        new_blob_list = []

        for blob in self.blob_list:
            if blob['id'] == blob_id:
                saved_blob = blob
            else:
                new_blob_list.append(blob)

        # Then re-insert it in its new position
        new_blob_list.insert(new_position - 1, saved_blob)
        self.blob_list = new_blob_list

        self.save()

    def get_blob(self, position):

        # import here to avoid circular dependency
        from blob.models import Blob

        if (position >= len(self.blob_list) or position < 0):
            return {}

        blob = Blob.objects.get(pk=self.blob_list[position]["id"])

        return {
            "blob_id": blob.id,
            "cover_info": Blob.get_cover_info(
                user=self.user,
                sha1sum=blob.sha1sum
            )
        }

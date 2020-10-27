import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from blob.models import Blob
from bookmark.models import Bookmark
from lib.mixins import SortOrderMixin


class Node(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    # TODO: Should this be a 1 to many relationship?
    note = models.TextField(blank=True, null=True)

    bookmarks = models.ManyToManyField(Bookmark, through="SortOrderNodeBookmark")
    blobs = models.ManyToManyField(Blob, through="SortOrderNodeBlob")


class SortOrderNodeBookmark(SortOrderMixin):

    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    bookmark = models.ForeignKey(Bookmark, on_delete=models.CASCADE)

    field_name = "node"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("node", "bookmark")
        )


@receiver(pre_delete, sender=SortOrderNodeBookmark)
def remove_bookmark(sender, instance, **kwargs):
    instance.handle_delete()


class SortOrderNodeBlob(SortOrderMixin):

    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    blob = models.ForeignKey(Blob, on_delete=models.CASCADE)

    field_name = "node"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("node", "blob")
        )


@receiver(pre_delete, sender=SortOrderNodeBlob)
def remove_blob(sender, instance, **kwargs):
    instance.handle_delete()

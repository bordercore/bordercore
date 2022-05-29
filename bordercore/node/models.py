import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from blob.models import Blob
from bookmark.models import Bookmark
from collection.models import Collection
from lib.mixins import SortOrderMixin, TimeStampedModel
from todo.models import Todo


def default_layout():
    """
    Django JSONField default must be a callable
    """
    return [[{"type": "bookmark"}, {"type": "blob"}], [{"type": "todo"}], [{"type": "note"}]]


class Node(TimeStampedModel):
    """
    A collection of blobs, bookmarks, and notes around a certain topic.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(blank=True, null=True)
    bookmarks = models.ManyToManyField(Bookmark, through="SortOrderNodeBookmark")
    blobs = models.ManyToManyField(Blob, through="SortOrderNodeBlob")
    todos = models.ManyToManyField(Todo, through="SortOrderNodeTodo")
    layout = JSONField(default=default_layout, null=True, blank=True)

    def __str__(self):
        return self.name

    def add_collection(self):

        # Collections are private to avoid display on the collection list page
        collection = Collection.objects.create(name="New Collection", user=self.user, is_private=True)

        layout = self.layout
        layout[0].insert(0, {"type": "collection", "uuid": str(collection.uuid)})
        self.layout = layout
        self.save()

        return collection

    def delete_collection(self, collection_uuid):

        collection = Collection.objects.get(uuid=collection_uuid)
        collection.delete()

        layout = self.layout
        for i, col in enumerate(layout):
            layout[i] = [x for x in col if "uuid" not in x or x["uuid"] != str(collection_uuid)]

        self.layout = layout
        self.save()


class SortOrderNodeBookmark(SortOrderMixin):

    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    bookmark = models.ForeignKey(Bookmark, on_delete=models.CASCADE)

    field_name = "node"

    def __str__(self):
        return f"SortOrder: {self.node}, {self.bookmark}"

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

    def __str__(self):
        return f"SortOrder: {self.node}, {self.blob}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("node", "blob")
        )


@receiver(pre_delete, sender=SortOrderNodeBlob)
def remove_blob(sender, instance, **kwargs):
    instance.handle_delete()


class SortOrderNodeTodo(SortOrderMixin):

    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE)

    field_name = "node"

    def __str__(self):
        return f"SortOrder: {self.node}, {self.todo}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("node", "todo")
        )


@receiver(pre_delete, sender=SortOrderNodeTodo)
def remove_Todo(sender, instance, **kwargs):
    instance.handle_delete()

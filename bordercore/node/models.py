import json
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone

from blob.models import Blob
from collection.models import Collection
from lib.mixins import SortOrderMixin, TimeStampedModel
from todo.models import Todo


def default_layout():
    """
    Django JSONField default must be a callable
    """
    return [[{"type": "todo"}], [], []]


class Node(TimeStampedModel):
    """
    A collection of blobs, bookmarks, and notes around a certain topic.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(blank=True, null=True)
    todos = models.ManyToManyField(Todo, through="SortOrderNodeTodo")
    layout = JSONField(default=default_layout, null=True, blank=True)

    def __str__(self):
        return self.name

    def add_collection(self, name="New Collection", uuid=None, display="list", rotate=-1, random_order=False):

        if uuid and uuid != "":
            # If a uuid is given, use an existing collection
            collection = Collection.objects.get(uuid=uuid)
            display = "individual"
            collection_type = "permanent"
        else:
            # New collections are private to avoid display on the collection list page
            collection = Collection.objects.create(name=name, user=self.user, is_private=True)
            collection_type = "ad-hoc"

        layout = self.layout
        layout[0].insert(0, {
            "type": "collection",
            "uuid": str(collection.uuid),
            "display": display,
            "collection_type": collection_type,
            "rotate": rotate,
            "random_order": random_order
        })
        self.layout = layout
        self.save()

        return collection

    def update_collection(self, collection_uuid, display, random_order, rotate):

        for column in self.layout:
            for row in column:
                if "uuid" in row and row["uuid"] == collection_uuid:
                    row["display"] = display
                    row["rotate"] = rotate
                    row["random_order"] = random_order

        self.save()

    def delete_collection(self, collection_uuid, collection_type):

        if collection_type == "ad-hoc":
            collection = Collection.objects.get(uuid=collection_uuid)
            collection.delete()

        layout = self.layout
        for i, col in enumerate(layout):
            layout[i] = [
                x
                for x in col
                if "uuid" not in x
                or x["uuid"] != str(collection_uuid)
            ]

        self.layout = layout
        self.save()

    def add_note(self, name="New Note"):

        note = Blob.objects.create(
            user=self.user,
            date=timezone.now().strftime("%Y-%m-%d"),
            name=name,
            is_note=True
        )
        note.index_blob()

        layout = self.layout
        layout[0].insert(
            0,
            {
                "type": "note",
                "uuid": str(note.uuid),
                "color": 1
            }
        )
        self.layout = layout
        self.save()

        return note

    def delete_note(self, note_uuid):

        note = Blob.objects.get(uuid=note_uuid)
        note.delete()

        layout = self.layout
        for i, col in enumerate(layout):
            layout[i] = [x for x in col if "uuid" not in x or x["uuid"] != str(note_uuid)]

        self.layout = layout
        self.save()

    def get_layout(self, populate_names=True):

        self.populate_names()
        return json.dumps(self.layout)

    def populate_names(self):
        """
        Get all collection and note names for this node in two queries
        rather than one for each.
        """

        # Get a list of all uuids for all collections and notes in this node.
        uuids = [
            val["uuid"]
            for sublist in self.layout
            for val in sublist
            if "uuid" in val
            and val["type"] in ["collection", "note"]
        ]

        # Populate a lookup dictionary with the collection and note names, uuid => name
        lookup = {}
        for x in Collection.objects.filter(uuid__in=uuids):
            lookup[str(x.uuid)] = x.name
        for x in Blob.objects.filter(uuid__in=uuids):
            lookup[str(x.uuid)] = x.name

        # Finally, add the collection and note names to the node's layout object
        for column in self.layout:
            for row in column:
                if row["type"] in ["collection", "note"]:
                    row["name"] = lookup[row["uuid"]]

    def populate_image_info(self):
        """
        """
        for column in self.layout:
            for row in column:
                if row["type"] == "image":
                    blob = Blob.objects.get(uuid=row["uuid"])
                    row["image_url"] = blob.get_cover_url()
                    row["image_title"] = blob.name

    def set_note_color(self, note_uuid, color):

        for column in self.layout:
            for row in column:
                if "uuid" in row and row["uuid"] == note_uuid:
                    row["color"] = color

        self.save()

    def add_image(self, image_uuid):

        layout = self.layout
        layout[0].insert(
            0,
            {
                "type": "image",
                "uuid": str(image_uuid),
            }
        )
        self.layout = layout
        self.save()

    def remove_image(self, image_uuid):

        layout = self.layout
        for i, col in enumerate(layout):
            layout[i] = [x for x in col if "uuid" not in x or x["uuid"] != str(image_uuid)]

        self.layout = layout
        self.save()

    def add_quote(self, quote_uuid):

        node_quote_uuid = str(uuid.uuid4())

        layout = self.layout
        layout[0].insert(
            0,
            {
                "node_quote_uuid": node_quote_uuid,
                "type": "quote",
                "uuid": str(quote_uuid),
                "color": 1,
                "format": "standard",
                "rotate": -1,
            }
        )
        self.layout = layout
        self.save()

        return node_quote_uuid

    def remove_quote(self, node_quote_uuid):

        layout = self.layout
        for i, col in enumerate(layout):
            layout[i] = [
                x
                for x in col
                if x.get("node_quote_uuid", None) != node_quote_uuid
            ]

        self.layout = layout
        self.save()

    def update_quote(self, node_quote_uuid, color, format, rotate, favorites_only=False):

        for column in self.layout:
            for row in column:
                if row.get("node_quote_uuid", None) == node_quote_uuid:
                    row["color"] = color
                    row["format"] = format
                    row["rotate"] = rotate
                    row["favorites_only"] = favorites_only

        self.save()

    def set_quote(self, quote_uuid):

        for column in self.layout:
            for row in column:
                if row["type"] == "quote":
                    row["uuid"] = str(quote_uuid)

        self.save()

    def add_todo_list(self):

        layout = self.layout
        layout[0].insert(
            0,
            {
                "type": "todo",
            }
        )
        self.layout = layout
        self.save()

    def delete_todo_list(self):

        layout = self.layout
        for i, col in enumerate(layout):
            layout[i] = [x for x in col if x["type"] != "todo"]
        self.layout = layout
        self.save()

        for so in SortOrderNodeTodo.objects.filter(node=self):
            so.todo.delete()


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
def remove_todo(sender, instance, **kwargs):
    instance.handle_delete()

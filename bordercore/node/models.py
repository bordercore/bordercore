import json
import random
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
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
    todos = models.ManyToManyField(Todo, through="NodeTodo")
    layout = JSONField(default=default_layout, null=True, blank=True)

    def __str__(self):
        return self.name

    def add_collection(self, name="New Collection", uuid=None, display="list", rotate=-1, random_order=False, limit=None):

        if uuid and uuid != "":
            # If a uuid is given, use an existing collection
            collection = Collection.objects.get(uuid=uuid)
            collection_type = "permanent"
        else:
            collection = Collection.objects.create(name=name, user=self.user)
            collection_type = "ad-hoc"

        layout = self.layout
        layout[0].insert(0, {
            "type": "collection",
            "uuid": str(collection.uuid),
            "display": display,
            "collection_type": collection_type,
            "rotate": rotate,
            "random_order": random_order,
            "limit": limit,
        })
        self.layout = layout
        self.save()

        return collection

    def update_collection(self, collection_uuid, display, random_order, rotate, limit):

        for column in self.layout:
            for row in column:
                if "uuid" in row and row["uuid"] == collection_uuid:
                    row["display"] = display
                    row["rotate"] = rotate
                    row["random_order"] = random_order
                    row["limit"] = limit

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

    def get_layout(self):

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
            lookup[str(x.uuid)] = {
                "name": x.name,
                "count": x.collectionobject_set.all().count()
            }
        for x in Blob.objects.filter(uuid__in=uuids):
            lookup[str(x.uuid)] = {
                "name": x.name
            }

        # Finally, add the collection and note names to the node's layout object
        for column in self.layout:
            for row in column:
                if row["type"] in ["collection", "note"]:
                    row["name"] = lookup[row["uuid"]]["name"]
                    if "count" in lookup[row["uuid"]]:
                        row["count"] = lookup[row["uuid"]]["count"]

    def populate_image_info(self):
        for column in self.layout:
            for row in column:
                if row["type"] == "image":
                    blob = Blob.objects.get(uuid=row["image_uuid"])
                    row["image_url"] = blob.get_cover_url()
                    row["image_title"] = blob.name

    def set_note_color(self, note_uuid, color):

        for column in self.layout:
            for row in column:
                if "uuid" in row and row["uuid"] == note_uuid:
                    row["color"] = color

        self.save()

    def set_quote(self, quote_uuid):

        for column in self.layout:
            for row in column:
                if row["type"] == "quote":
                    row["quote_uuid"] = str(quote_uuid)

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

        for so in NodeTodo.objects.filter(node=self):
            so.todo.delete()

    def get_todo_list(self):
        todo_list = self.todos.all().only("name", "note", "priority", "url", "uuid").order_by("nodetodo__sort_order")

        return [
            {
                "name": x.name,
                "note": x.note,
                "priority": x.priority,
                "uuid": x.uuid,
                "url": x.url,
            }
            for x
            in todo_list
        ]

    def get_preview(self):
        images = []

        # Get a list of all uuids for all images in this node.
        image_uuids = [
            val["uuid"]
            for sublist in self.layout
            for val in sublist
            if "uuid" in val
            and val["type"] in ["image"]
        ]
        if image_uuids:
            random_uuid = random.choice(image_uuids)
            blob = Blob.objects.get(uuid=random_uuid)
            images.append({
                "uuid": random_uuid,
                "cover_url": blob.get_cover_url(),
                "blob_url": reverse("blob:detail", kwargs={"uuid": random_uuid})
            })

        # Get a list of all uuids for all collections in this node.
        collection_uuids = [
            val["uuid"]
            for sublist in self.layout
            for val in sublist
            if "uuid" in val
            and val["type"] in ["collection"]
        ]
        all_objects = []
        for collection_uuid in collection_uuids:
            collection = Collection.objects.get(uuid=collection_uuid)
            all_objects.extend(collection.get_object_list()["object_list"])

        blobs = [x for x in all_objects if x["type"] == "blob"]
        blob_count = len([x for x in all_objects if x["type"] == "blob"])

        # We ultimately want two images. If we already found one image, then
        #  we only need one more from a collection. If not, we need two.
        images.extend([
            {
                "uuid": obj["uuid"],
                "cover_url": obj["cover_url"],
                "blob_url": obj["url"]
            }
            for obj in
            random.sample(blobs, min(2 - len(images), blob_count))
        ])

        notes = [
            val
            for sublist in self.layout
            for val in sublist
            if "uuid" in val
            and val["type"] in ["note"]
        ]

        todos = self.get_todo_list()

        return {
            "images": images,
            "notes": notes,
            "todos": todos
        }

    # Add an image, quote or node to a node
    def add_component(self, component_type, component, options=None):
        options = options or {}

        new_uuid = str(uuid.uuid4())

        layout = self.layout
        layout[0].insert(
            0,
            {
                "type": component_type,
                "uuid": new_uuid,
                f"{component_type}_uuid": str(component.uuid),
                "options": options,
            }
        )
        self.layout = layout
        self.save()

        return new_uuid

    # Update the options for a quote or node
    def update_component(self, uuid, options):
        for column in self.layout:
            for row in column:
                if row.get("uuid", None) == uuid:
                    row["options"] = options

        self.save()

    # Remove an image, quote, or node from a node
    def remove_component(self, uuid):
        layout = self.layout
        for i, col in enumerate(layout):
            layout[i] = [
                x
                for x in col
                if x.get("uuid", None) != str(uuid)
            ]

        self.layout = layout
        self.save()


class NodeTodo(SortOrderMixin):

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


@receiver(pre_delete, sender=NodeTodo)
def remove_todo(sender, instance, **kwargs):
    instance.handle_delete()

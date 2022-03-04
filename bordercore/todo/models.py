import uuid

from elasticsearch import helpers

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, JSONField, Max
from django.db.models.signals import m2m_changed

from lib.mixins import TimeStampedModel
from lib.util import get_elasticsearch_connection
from tag.models import SortOrderTagTodo, Tag

from .managers import TodoManager


class Todo(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    note = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=1000, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag)
    data = JSONField(null=True, blank=True)

    objects = TodoManager()

    PRIORITY_CHOICES = [
        (1, "High"),
        (2, "Medium"),
        (3, "Low"),
    ]
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2
    )

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all().order_by("name")])

    @staticmethod
    def get_priority_name(priority_value):
        for priority in Todo.PRIORITY_CHOICES:
            if priority[0] == priority_value:
                return priority[1]
        return None

    @staticmethod
    def get_priority_value(priority_name):
        for priority in Todo.PRIORITY_CHOICES:
            if priority[1] == priority_name:
                return priority[0]
        return None

    @staticmethod
    def get_todo_counts(user):

        # Get the list of tags, initially sorted by count per tag
        tags = Tag.objects.values("id", "name") \
                          .annotate(count=Count("todo", distinct=True)) \
                          .annotate(created=Max("todo__created")) \
                          .filter(user=user, todo__user=user) \
                          .order_by("-created")

        # Convert from queryset to list of dicts so we can further sort them
        counts = [{"name": x["name"], "count": x["count"]} for x in tags]

        return counts

    def save(self, *args, **kwargs):

        # Remove any custom parameters before calling the parent class
        index_es = kwargs.pop("index_es", True)

        super().save(*args, **kwargs)

        # Index the todo item in Elasticsearch
        if index_es:
            self.index_todo()

    def delete(self):

        es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)
        es.delete(index=settings.ELASTICSEARCH_INDEX, id=self.uuid)

        super().delete()

    def index_todo(self, es=None):

        if not es:
            es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

        count, errors = helpers.bulk(es, [self.elasticsearch_document])

    @property
    def elasticsearch_document(self):
        """
        Return a representation of the todo suitable for indexing in Elasticsearch
        """

        return {
            "_index": settings.ELASTICSEARCH_INDEX,
            "_id": self.uuid,
            "_source": {
                "bordercore_id": self.id,
                "uuid": self.uuid,
                "name": self.name,
                "tags": [tag.name for tag in self.tags.all()],
                "url": self.url,
                "note": self.note,
                "last_modified": self.modified,
                "priority": self.priority,
                "doctype": "todo",
                "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
                "date_unixtime": self.created.strftime("%s"),
                "user_id": self.user.id,
                **settings.ELASTICSEARCH_EXTRA_FIELDS
            }
        }


def tags_changed(sender, **kwargs):

    if kwargs["action"] == "post_add":
        todo = kwargs["instance"]

        for tag_id in kwargs["pk_set"]:
            so = SortOrderTagTodo(tag=Tag.objects.get(user=todo.user, pk=tag_id), todo=todo)
            so.save()


m2m_changed.connect(tags_changed, sender=Todo.tags.through)

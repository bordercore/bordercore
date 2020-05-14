import uuid
from functools import cmp_to_key

from elasticsearch import Elasticsearch

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Todo(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    task = models.TextField()
    note = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    due_date = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    data = JSONField(null=True, blank=True)

    PRIORITY_CHOICES = [
        (1, "High"),
        (2, "Medium"),
        (3, "Low"),
    ]
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2
    )

    def get_modified(self):
        return self.modified.strftime('%b %d, %Y')

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

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
    def get_todo_counts(user, first_tag):

        # Get the list of tags, initially sorted by count per tag
        tags = Tag.objects.values("id", "name") \
                          .annotate(count=Count("todo", distinct=True)) \
                          .filter(todo__user=user) \
                          .order_by("-count")

        # Convert from queryset to list of dicts so we can further sort them
        counts = [{"name": x["name"], "count": x["count"]} for x in tags]

        # Use a custom sort function to insure that the tag matching first_tag
        #  always comes out first.
        counts.sort(key=cmp_to_key(lambda x, y: -1 if x["name"] == first_tag else 1))

        return counts

    def delete(self):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        request_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "doctype": "todo"
                            }
                        },
                        {
                            "term": {
                                "uuid.keyword": self.uuid
                            }
                        },

                    ]
                }
            }
        }

        es.delete_by_query(index=settings.ELASTICSEARCH_INDEX, body=request_body)

        super(Todo, self).delete()

    def index_todo(self, es=None):

        if not es:
            es = Elasticsearch(
                [settings.ELASTICSEARCH_ENDPOINT],
                verify_certs=False
            )

        doc = {
            "bordercore_id": self.id,
            "uuid": self.uuid,
            "task": self.task,
            "tags": [tag.name for tag in self.tags.all()],
            "url": self.url,
            "note": self.note,
            "last_modified": self.modified,
            "doctype": "todo",
            "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
            "date_unixtime": self.created.strftime("%s"),
            "user_id": self.user.id
        }

        res = es.index(
            index=settings.ELASTICSEARCH_INDEX,
            id=self.uuid,
            body=doc
        )


@receiver(post_save, sender=Todo)
def post_save_wrapper(sender, instance, **kwargs):
    """
    This should be called anytime a todo task is added or updated.
    """

    # Index the todo item in Elasticsearch
    instance.index_todo()

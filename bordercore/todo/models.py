import datetime
import re
import urllib
import uuid

import markdown
from elasticsearch import Elasticsearch
from markdown.extensions.codehilite import CodeHiliteExtension

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Count, Max
from django.db.models.signals import m2m_changed, post_save
from django.dispatch.dispatcher import receiver

from lib.mixins import TimeStampedModel
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
        return ", ".join([tag.name for tag in self.tags.all()])

    @staticmethod
    def get_markdown_note(note):
        if note:
            return markdown.markdown(note, extensions=[CodeHiliteExtension(guess_lang=False), "tables"])

        return ""

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
                                "uuid": self.uuid
                            }
                        },

                    ]
                }
            }
        }

        es.delete_by_query(index=settings.ELASTICSEARCH_INDEX, body=request_body)

        super().delete()

    def index_todo(self, es=None):

        if not es:
            es = Elasticsearch(
                [settings.ELASTICSEARCH_ENDPOINT],
                verify_certs=False
            )

        doc = {
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
            "user_id": self.user.id
        }

        es.index(
            index=settings.ELASTICSEARCH_INDEX,
            id=self.uuid,
            body=doc
        )

    @staticmethod
    def search(search_term, user_id):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        search_term = search_term.lower()

        search_terms = re.split(r"\s+", urllib.parse.unquote(search_term))

        search_object = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "user_id": user_id
                            }
                        },
                        {
                            "term": {
                                "doctype": "todo"
                            }
                        },
                    ]
                }
            },
            "from": 0, "size": 1000,
            "_source":[
                "date",
                "last_modified",
                "name",
                "note",
                "priority",
                "url",
                "uuid"
            ]
        }

        # Separate query into terms based on whitespace and
        #  and treat it like an "AND" boolean search
        for one_term in search_terms:
            search_object["query"]["bool"]["must"].append(
                {
                    "bool": {
                        "should": [
                            {
                                "wildcard": {
                                    "name": {
                                        "value": f"*{one_term}*",
                                    }
                                }
                            }
                        ]
                    }
                }
            )

        results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

        matches = []
        for match in results["hits"]["hits"]:
            matches.append(
                {
                    "created": datetime.datetime.strptime(match["_source"]["date"]["gte"], "%Y-%m-%d %H:%M:%S"),
                    "name": match["_source"]["name"],
                    "note": match["_source"]["note"],
                    "priority": match["_source"]["priority"],
                    "url": match["_source"]["url"],
                    "uuid": match["_source"]["uuid"],
                }
            )

        return matches


@receiver(post_save, sender=Todo)
def post_save_wrapper(sender, instance, **kwargs):
    """
    This should be called anytime a todo task is added or updated.
    """

    # Index the todo item in Elasticsearch
    instance.index_todo()


def tags_changed(sender, **kwargs):

    if kwargs["action"] == "post_add":
        todo = kwargs["instance"]

        for tag_id in kwargs["pk_set"]:
            so = SortOrderTagTodo(tag=Tag.objects.get(user=todo.user, pk=tag_id), todo=todo)
            so.save()


m2m_changed.connect(tags_changed, sender=Todo.tags.through)

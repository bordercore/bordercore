from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from elasticsearch import Elasticsearch

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Todo(TimeStampedModel):
    task = models.TextField()
    note = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    due_date = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    is_urgent = models.BooleanField(default=False)

    def get_modified(self):
        return self.modified.strftime('%b %d, %Y')

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

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
                                "doctype": "bordercore_todo"
                            }
                        },
                        {
                            "term": {
                                "bordercore_id": self.id
                            }
                        },

                ]
                }
            }
        }

        es.delete_by_query(index=settings.ELASTICSEARCH_INDEX, body=request_body)

        super(Todo, self).delete()

    def post_save_wrapper(self):
        """
        This should be called anytime a bookmark is added or updated.
        """

        # Index the todo item in Elasticsearch
        self.index_todo()

    def index_todo(self):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        doc = {
            "bordercore_id": self.id,
            "bordercore_todo_task": self.task,
            "tags": [tag.name for tag in self.tags.all()],
            "url": self.url,
            "note": self.note,
            "last_modified": self.modified,
            "doctype": "bordercore_todo",
            "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
            "date_unixtime": self.created.strftime("%s"),
            "user_id": self.user.id
        }

        res = es.index(
            index=settings.ELASTICSEARCH_INDEX,
            id=f"bordercore_todo_{self.id}",
            body=doc
        )

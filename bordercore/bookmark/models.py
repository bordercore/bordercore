import json
import re
import uuid

import boto3
from elasticsearch import Elasticsearch

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import m2m_changed

from lib.mixins import TimeStampedModel
from tag.models import SortOrderTagBookmark, Tag


# This custom field lets us use a checkbox on the form, which, if checked,
#  results in a blob of JSON stored in the database rather than
#  the usual boolean value.
class DailyBookmarkJSONField(JSONField):

    def to_python(self, value):
        if value is True:
            return json.loads('{"viewed": "false"}')
        else:
            return None


class Bookmark(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    url = models.TextField()
    title = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(null=True)
    tags = models.ManyToManyField("tag.Tag")
    is_pinned = models.BooleanField(default=False)
    daily = DailyBookmarkJSONField(blank=True, null=True)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)
    importance = models.IntegerField(default=1)

    created = models.DateTimeField(db_index=True, auto_now_add=True)

    def __str__(self):
        return self.title

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
                                "doctype": "bookmark"
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

        super().delete()

    def index_bookmark(self, es=None):

        if not es:
            es = Elasticsearch(
                [settings.ELASTICSEARCH_ENDPOINT],
                verify_certs=False
            )

        doc = {
            "bordercore_id": self.id,
            "title": self.title,
            "bordercore_bookmark_note": self.note,
            "tags": [tag.name for tag in self.tags.all()],
            "url": self.url,
            "note": self.note,
            "importance": self.importance,
            "last_modified": self.modified,
            "doctype": "bookmark",
            "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
            "date_unixtime": self.created.strftime("%s"),
            "user_id": self.user.id,
            "uuid": self.uuid
        }

        res = es.index(
            index=settings.ELASTICSEARCH_INDEX,
            id=f"bordercore_bookmark_{self.id}",
            body=doc
        )

    def snarf_favicon(self):

        client = boto3.client("lambda")

        payload = {
            "url": self.url,
            "parse_domain": True
        }

        response = client.invoke(
            ClientContext="MyApp",
            FunctionName="SnarfFavicon",
            InvocationType="Event",
            LogType="Tail",
            Payload=json.dumps(payload)
        )

    def get_favicon_url(self, size=32):

        if not self.url:
            return ""

        p = re.compile("https?://([^/]*)")

        m = p.match(self.url)

        if m:
            domain = m.group(1)
            parts = domain.split(".")
            # We want the domain part of the hostname (eg npr.org instead of www.npr.org)
            if len(parts) == 3:
                domain = ".".join(parts[1:])
            return f"<img src=\"https://www.bordercore.com/favicons/{domain}.ico\" width=\"{size}\" height=\"{size}\" />"
        else:
            return ""

    @staticmethod
    def get_tagged_bookmarks(user, tag_name):

        bookmark_info = [(x.bookmark, x.note) for x in SortOrderTagBookmark.objects.filter(tag__name=tag_name).select_related("bookmark")]

        # If there is an associated note, add it to the bookmark object
        sorted_bookmarks = []
        for bookmarks in bookmark_info:
            if bookmarks[1]:
                bookmarks[0].note = bookmarks[1]
            sorted_bookmarks.append(bookmarks[0])

        return sorted_bookmarks


def tags_changed(sender, **kwargs):

    if kwargs["action"] == "post_add":
        if kwargs["action"] == "post_add":
            bookmark = kwargs["instance"]

            for tag_id in kwargs["pk_set"]:
                so = SortOrderTagBookmark(tag=Tag.objects.get(pk=tag_id), bookmark=bookmark)
                so.save()


m2m_changed.connect(tags_changed, sender=Bookmark.tags.through)

import json
import re
import uuid

import boto3
from elasticsearch import helpers

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import m2m_changed

from lib.mixins import TimeStampedModel
from lib.util import get_elasticsearch_connection
from tag.models import SortOrderTagBookmark, Tag

from .managers import BookmarkManager


class DailyBookmarkJSONField(JSONField):
    """
    This custom field lets us use a checkbox on the form, which, if checked,
    results in a blob of JSON stored in the database rather than
    the usual boolean value.
    """
    def to_python(self, value):
        if value is True:
            return json.loads('{"viewed": "false"}')
        else:
            return None


class Bookmark(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=1000)
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(null=True)
    tags = models.ManyToManyField("tag.Tag")
    is_pinned = models.BooleanField(default=False)
    daily = DailyBookmarkJSONField(blank=True, null=True)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)
    importance = models.IntegerField(default=1)

    created = models.DateTimeField(db_index=True, auto_now_add=True)

    objects = BookmarkManager()

    def __str__(self):
        return self.name

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def save(self, *args, **kwargs):

        new_object = True if not self.id else False

        super().save(*args, **kwargs)

        # Only generate a cover image when the bookmark is first
        #  saved by checking for the existence of an id
        if new_object:
            self.generate_cover_image()

    def delete(self):

        super().delete()

        es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)
        es.delete(index=settings.ELASTICSEARCH_INDEX, id=self.uuid)

        self.delete_cover_image()

    def generate_cover_image(self):

        # TODO: move this to settings
        SNS_TOPIC = "arn:aws:sns:us-east-1:192218769908:chromda"
        client = boto3.client("sns")

        message = {
            "url": self.url,
            "s3key": f"bookmarks/{self.uuid}.png"
        }

        client.publish(
            TopicArn=SNS_TOPIC,
            Message=json.dumps(message),
        )

    def delete_cover_image(self):
        """
        After deletion, remove the bookmark's cover images from S3
        """

        s3 = boto3.resource("s3")

        key = f"bookmarks/{self.uuid}.png"
        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, key).delete()

        key = f"bookmarks/{self.uuid}-small.png"
        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, key).delete()

    def index_bookmark(self, es=None):

        if not es:
            es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

        count, errors = helpers.bulk(es, [self.elasticsearch_document])

    @property
    def elasticsearch_document(self):
        """
        Return a representation of the bookmark suitable for indexing in Elasticsearch
        """

        return {
            "_index": settings.ELASTICSEARCH_INDEX,
            "_id": self.uuid,
            "_source": {
                "bordercore_id": self.id,
                "name": self.name,
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
        }

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


def tags_changed(sender, **kwargs):

    if kwargs["action"] == "post_add":
        bookmark = kwargs["instance"]

        for tag_id in kwargs["pk_set"]:
            so = SortOrderTagBookmark(tag=Tag.objects.get(pk=tag_id), bookmark=bookmark)
            so.save()


m2m_changed.connect(tags_changed, sender=Bookmark.tags.through)

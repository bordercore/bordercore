from __future__ import unicode_literals

import json
import uuid

import boto3

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Case, CharField, JSONField, Value, When

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Collection(TimeStampedModel):
    """
    A collection of blobs organized around a common theme or project
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    blob_list = JSONField(blank=True, null=True)
    tags = models.ManyToManyField(Tag)
    description = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def delete(self):

        # Delete the collection's thumbnail image in S3
        s3 = boto3.resource("s3")
        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, f"collections/{self.uuid}.jpg").delete()

        super().delete()

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def sort(self, blob_id, new_position):

        if blob_id not in [x["id"] for x in self.blob_list]:
            raise ValueError(f"blob_id={blob_id} not in collection {self}")

        # First remove the blob from the existing list
        saved_blob = []
        new_blob_list = []

        for blob in self.blob_list:
            if blob['id'] == blob_id:
                saved_blob = blob
            else:
                new_blob_list.append(blob)

        # Then re-insert it in its new position
        new_blob_list.insert(new_position - 1, saved_blob)
        self.blob_list = new_blob_list

        self.save()

    def get_blob(self, position):

        Blob = apps.get_model("blob", "Blob")

        if (position >= len(self.blob_list) or position < 0):
            return {}

        blob = Blob.objects.get(pk=self.blob_list[position]["id"])

        return {
            "blob_id": blob.id,
            "cover_info": blob.get_cover_info()
        }

    def get_blob_list(self, limit=None):

        Blob = apps.get_model("blob", "Blob")

        blob_list = self.blob_list[:limit] if limit else self.blob_list

        if blob_list:

            ids = [x['id'] for x in blob_list]
            order = Case(*[When(id=i, then=pos) for pos, i in enumerate(ids)])

            whens = [
                When(id=x['id'], then=Value(x.get('note', ''))) for x in blob_list
            ]

            blob_list = Blob.objects.filter(id__in=ids).annotate(
                collection_note=Case(
                    *whens,
                    output_field=CharField()
                )).order_by(order)

            for blob in blob_list:
                blob.cover_url = blob.get_cover_info(
                    size="small"
                ).get("url", None)

                blob.name = blob.get_name(use_filename_if_present=True).replace("\"", "\\\"")

            return blob_list

        else:

            return []

    def get_random_blobs(self):

        Blob = apps.get_model("blob", "Blob")

        if self.blob_list:

            blob_ids = [x["id"] for x in self.blob_list]

            blob_list = Blob.objects.filter(id__in=blob_ids).\
                filter(file__iregex=r'\.(gif|jpg|pdf|png)$').\
                values("uuid", "file").\
                order_by("?")[:4]
            return blob_list

        else:

            return []

    def create_collection_thumbnail(self):

        # Generate a fresh cover image for the collection
        client = boto3.client("sns")

        message = {
            "Records": [
                {
                    "s3": {
                        "bucket": {
                            "name": settings.AWS_STORAGE_BUCKET_NAME,
                        },
                        "collection_uuid": str(self.uuid)
                    }
                }
            ]
        }

        client.publish(
            TopicArn=settings.CREATE_COLLECTION_THUMBNAIL_TOPIC_ARN,
            Message=json.dumps(message),
        )

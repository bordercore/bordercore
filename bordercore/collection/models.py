from __future__ import unicode_literals

import json
import re
import uuid

import boto3

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse

from lib.mixins import SortOrderMixin, TimeStampedModel
from tag.models import Tag


class Collection(TimeStampedModel):
    """
    A collection of blobs organized around a common theme or project
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    blobs = models.ManyToManyField("blob.Blob", through="SortOrderCollectionBlob")
    tags = models.ManyToManyField(Tag)
    description = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def add_blob(self, blob):

        so = SortOrderCollectionBlob(collection=self, blob=blob)
        so.save()

    def delete(self):

        # Delete the collection's thumbnail image in S3
        s3 = boto3.resource("s3")
        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, f"collections/{self.uuid}.jpg").delete()

        super().delete()

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_blob(self, position):

        if (position >= len(self.blobs.all()) or position < 0):
            return {}

        so = SortOrderCollectionBlob.objects.filter(collection=self).select_related("blob")[position]

        return {
            "blob_id": so.blob.id,
            "cover_info": so.blob.get_cover_info()
        }

    def get_blob_list(self, limit=None):

        blob_list = []

        so = SortOrderCollectionBlob.objects.filter(collection=self).select_related("blob")

        if limit:
            so = so[:limit]

        for blob in so:
            blob_list.append(
                {
                    "id": blob.blob.id,
                    "uuid": blob.blob.uuid,
                    "name": re.sub("[\n\r]", "", blob.blob.name),
                    "url": reverse("blob:detail", kwargs={"uuid": blob.blob.uuid}),
                    "sha1sum": blob.blob.sha1sum,
                    "cover_url": blob.blob.get_cover_info(
                        size="small"
                    ).get("url", None)
                }
            )

        return blob_list

    def get_random_blobs(self):

        return self.blobs.filter(file__iregex=r"\.(gif|jpg|jpeg|pdf|png)$").\
            values("uuid", "file").\
            order_by("?")[:4]

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


class SortOrderCollectionBlob(SortOrderMixin):

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    blob = models.ForeignKey("blob.Blob", on_delete=models.CASCADE)

    field_name = "collection"

    def __str__(self):
        return f"SortOrder: {self.collection}, {self.blob}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("collection", "blob")
        )


@receiver(pre_delete, sender=SortOrderCollectionBlob)
def remove_blob(sender, instance, **kwargs):
    instance.handle_delete()

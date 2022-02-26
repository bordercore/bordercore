from __future__ import unicode_literals

import json
import logging
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

log = logging.getLogger(f"bordercore.{__name__}")


class Collection(TimeStampedModel):
    """
    A collection of blobs organized around a common theme or project
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    blobs = models.ManyToManyField("blob.Blob", through="SortOrderCollectionBlob")
    tags = models.ManyToManyField(Tag)
    description = models.TextField(blank=True, default="")
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

    def get_blob(self, position, randomize=False):

        so = SortOrderCollectionBlob.objects.filter(collection=self).select_related("blob").select_related("blob__user")

        if randomize:
            blob = so.order_by("?")[0]
        else:
            if (position >= len(self.blobs.all()) or position < 0):
                return {}
            blob = so[position]

        content_type = None
        try:
            content_type = blob.blob.get_elasticsearch_info()["content_type"]
        except Exception:
            log.warning(f"Can't get content type for uuid={blob.blob.uuid}")

        return {
            "url": f"{settings.MEDIA_URL}blobs/{blob.blob.get_url()}",
            "content_type": content_type
        }

    def get_blob_list(self, request=None, limit=None):

        blob_list = []

        queryset = SortOrderCollectionBlob.objects.filter(collection=self)

        if request and "tag" in request.GET:
            queryset = queryset.filter(blob__tags__name=request.GET["tag"])

        so = queryset.select_related("blob")

        if limit:
            so = so[:limit]

        for blob in so:
            blob_list.append(
                {
                    "id": blob.blob.id,
                    "uuid": blob.blob.uuid,
                    "filename": blob.blob.file.name,
                    "name": re.sub("[\n\r]", "", blob.blob.name),
                    "url": reverse("blob:detail", kwargs={"uuid": blob.blob.uuid}),
                    "sha1sum": blob.blob.sha1sum,
                    "cover_url": blob.blob.get_cover_url_small()
                }
            )

        return blob_list

    def get_recent_images(self, limit=4):
        """
        Return a list of the most recent images added to this collection
        """

        return self.blobs.filter(file__iregex=r"\.(gif|jpg|jpeg|pdf|png)$").\
            values("uuid", "file").\
            order_by("-created")[:limit]

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
    created = models.DateTimeField(auto_now_add=True)

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

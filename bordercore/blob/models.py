import datetime
import hashlib
import json
import logging
import re
import uuid
from collections import defaultdict
from pathlib import PurePath
from urllib.parse import quote_plus, urlparse

import boto3
import humanize
from elasticsearch import Elasticsearch, NotFoundError
from storages.backends.s3boto3 import S3Boto3Storage

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch.dispatcher import receiver

from collection.models import Collection
from lib.mixins import TimeStampedModel
from lib.time_utils import get_date_from_pattern
from lib.util import is_image
from tag.models import Tag

EDITIONS = {'1': 'First',
            '2': 'Second',
            '3': 'Third',
            '4': 'Fourth',
            '5': 'Fifth',
            '6': 'Sixth',
            '7': 'Seventh',
            '8': 'Eighth',
            '9': 'Ninth'}

MAX_COVER_IMAGE_WIDTH = 800

FILE_TYPES_TO_INGEST = [
    'azw3',
    'chm',
    'epub',
    'html',
    'mp3',
    'pdf',
    'txt'
]

ILLEGAL_FILENAMES = [
    "cover.jpg",
    "cover-large.jpg",
    "cover-small.jpg"
]

log = logging.getLogger(f"bordercore.{__name__}")


class DownloadableS3Boto3Storage(S3Boto3Storage):

    # Override this to prevent Django from cleaning the name (eg replacing spaces with underscores)
    def get_valid_name(self, name):
        return name


class Blob(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    content = models.TextField(null=True)
    name = models.TextField(null=True)
    sha1sum = models.CharField(max_length=40, blank=True, null=True)
    file = models.FileField(max_length=500, storage=DownloadableS3Boto3Storage(), blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    date = models.TextField(null=True)
    importance = models.IntegerField(default=1)
    is_private = models.BooleanField(default=False)
    is_note = models.BooleanField(default=False)
    is_indexed = models.BooleanField(default=True)
    documents = models.ManyToManyField("self", blank=True)

    class Meta:
        unique_together = (
            ("sha1sum", "user")
        )

    def __str__(self):
        return self.name or ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Save the filename so that when it changes by a blob edit
        #  in save() we know what the original was.
        setattr(self, "__original_filename", self.file.name)

    @staticmethod
    def get_content_type(argument):
        switcher = {
            "application/mp4": "Video",
            "application/octet-stream": "Video",
            "application/pdf": "PDF",
            "application/x-mobipocket-ebook": "E-Book",
            "audio/mpeg": "Audio",
            "image/gif": "Image",
            "image/jpeg": "Image",
            "image/png": "Image",
            "video/mp4": "Video",
            "video/webm": "Video",
            "video/x-m4v": "Video"
        }

        return switcher.get(argument, "")

    @staticmethod
    def get_duration_humanized(duration):
        duration = str(datetime.timedelta(seconds=int(duration)))

        # Remove any leading "0:0" or "0:"
        duration = re.sub(r"^(0\:0)|^0\:", "", duration)

        return duration

    def get_parent_dir(self):
        return f"{settings.MEDIA_ROOT}/{self.uuid}"

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_url(self):
        return f"{self.uuid}/{quote_plus(str(self.file))}"

    def get_name(self, remove_edition_string=False, use_filename_if_present=False):
        name = self.name
        if name:
            if remove_edition_string:
                pattern = re.compile(r'(.*) (\d)E$')
                matches = pattern.match(name)
                if matches and EDITIONS.get(matches.group(2), None):
                    return "%s" % (matches.group(1))
            return name
        else:
            if use_filename_if_present:
                return PurePath(str(self.file)).name
            else:
                return "No name"

    def get_edition_string(self):
        if self.name:
            pattern = re.compile(r'(.*) (\d)E$')
            matches = pattern.match(self.name)
            if matches and EDITIONS.get(matches.group(2), None):
                return "%s Edition" % (EDITIONS[matches.group(2)])

        return ""

    @property
    def doctype(self):
        if self.is_note is True:
            return "note"
        elif "is_book" in [x.name for x in self.metadata_set.all()]:
            return "book"
        elif is_image(self.file):
            return "image"
        elif self.sha1sum is not None:
            return "blob"
        else:
            return "document"

    def get_cleaned_date(self, date):
        """
        Return a sanitized version of the date for display by the vuejs-datepicker widget.
        Add "T00:00" so that JavaScript will use localtime rather than UTC.
        """

        if date is None:
            return ""

        if re.compile(r"^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d").match(date):
            # If the date has a time, remove it. The vuejs-datepicker widget will reject it.
            return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%dT00:00")
        else:
            return f"{date}T00:00"

    @staticmethod
    def get_s3_key_from_uuid(uuid, file):
        return "{}/{}/{}".format(settings.MEDIA_ROOT, uuid, file)

    def get_s3_key(self):
        if self.file:
            return f"{settings.MEDIA_ROOT}/{self.uuid}/{self.file}"
        else:
            return None

    def get_metadata(self):

        metadata = {}
        urls = []

        for x in self.metadata_set.all():
            if x.name == "Url":
                urls.append(
                    {
                        "url": x.value,
                        "domain": urlparse(x.value).netloc
                    }
                )
            if metadata.get(x.name, None):
                metadata[x.name] = ", ".join([metadata[x.name], x.value])
            else:
                metadata[x.name] = x.value

        return metadata, urls

    def get_elasticsearch_info(self):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "uuid": self.uuid
                            }
                        },
                        {
                            "term": {
                                "user_id": self.user.id
                            }
                        }
                    ]
                }
            },
            "_source": ["author", "task", "content_type", "doctype", "duration", "note", "filename", "bordercore_id", "attr_is_book", "last_modified", "name", "num_pages", "tags", "sha1sum", "size", "url"]
        }

        results = es.search(index=settings.ELASTICSEARCH_INDEX, body=query)["hits"]["hits"][0]

        if "content_type" in results["_source"]:
            results["_source"]["content_type"] = Blob.get_content_type(results["_source"]["content_type"])

        if "size" in results["_source"]:
            results["_source"]["size"] = humanize.naturalsize(results["_source"]["size"])

        if "duration" in results["_source"]:
            results["_source"]["duration"] = Blob.get_duration_humanized(results["_source"]["duration"])

        return {**results["_source"], "id": results["_id"]}

    def save(self, *args, **kwargs):

        # We rely on the readable() method to determine if we're
        #  adding a new file or editing an existing one. If it's
        #  new, we have access to the file since it was just
        #  uploaded, so calculate the sha1sum. If we're editing the
        #  file, we don't have access to any file, so don't try
        #  to calculate the sha1sum.

        if self.file and self.file.readable():

            hasher = hashlib.sha1()
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.sha1sum = hasher.hexdigest()

        super().save(*args, **kwargs)

        if self.sha1sum:

            # This is set in __init__
            filename_orig = getattr(self, "__original_filename")
            if filename_orig != self.file.name:
                key = f"{self.get_parent_dir()}/{filename_orig}"
                log.info(f"File name changed detected. Deleting old file: {key}")
                s3 = boto3.resource("s3")
                s3.Object(settings.AWS_STORAGE_BUCKET_NAME, key).delete()

    def has_been_modified(self):
        """
        If the modified time is greater than the creation time by
        more than one second, assume it has been edited.
        """

        if int(self.modified.strftime("%s")) - int(self.created.strftime("%s")) > 0:
            return True
        else:
            return False

    def get_related_blobs(self):
        related_blobs = []
        for blob in self.documents.all():
            related_blobs.append({"uuid": blob.uuid, "name": blob.name})
        return related_blobs

    def is_pinned_note(self):
        return self in self.user.userprofile.pinned_notes.all()

    def get_collection_info(self):
        return Collection.objects.filter(
            user=self.user,
            blob_list__contains=[{"id": self.id}],
            is_private=False)

    def get_linked_blobs(self):

        linked_blobs = []

        for collection in Collection.objects.filter(user=self.user, blob_list__contains=[{"id": self.id}]):
            blob_list = Blob.objects.filter(user=self.user, pk__in=[x["id"] for x in collection.blob_list if x["id"] != self.id])
            if collection.is_private:
                linked_blobs.append(
                    {
                        "uuid": collection.uuid,
                        "name": collection.name,
                        "is_private": collection.is_private,
                        "blob_list": blob_list
                    }
                )

        return linked_blobs

    def get_date(self):
        return get_date_from_pattern({"gte": self.date})

    def has_thumbnail_url(self):
        try:
            _ = self.get_cover_info(self.user, self.sha1sum, size='small')['url']
            return True
        except Exception:
            return False

    def get_cover_url_small(self):
        return self.get_cover_info(self.user, self.sha1sum, size='small')['url']

    @staticmethod
    def get_image_dimensions(s3_key, max_cover_image_width=MAX_COVER_IMAGE_WIDTH):

        info = {}

        s3 = boto3.resource("s3")
        obj = s3.Object(bucket_name=settings.AWS_STORAGE_BUCKET_NAME, key=s3_key)

        try:

            info["width"] = int(obj.metadata["image-width"])
            info["height"] = int(obj.metadata["image-height"])

            if info["width"] > max_cover_image_width:
                info["height_cropped"] = int(max_cover_image_width * info["height"] / info["width"])
                info["width_cropped"] = max_cover_image_width

        except KeyError as e:
            log.warning(f"Warning: Object has no metadata {e}")

        return info

    @staticmethod
    def is_ingestible_file(filename):

        file_extension = PurePath(str(filename)).suffix
        if file_extension[1:].lower() in FILE_TYPES_TO_INGEST:
            return True
        else:
            return False

    def get_cover_info(self, size="large", max_cover_image_width=MAX_COVER_IMAGE_WIDTH):

        if self.sha1sum is None:
            return {"url": ""}

        info = {}
        url = None

        prefix = settings.COVER_URL + f"{self.uuid}"

        file_extension = PurePath(self.file.name).suffix

        if size != "large":
            url = f"{prefix}/cover.jpg"
        else:
            # Is the blob itself an image?
            if file_extension[1:].lower() in ["gif", "jpg", "jpeg", "png"]:
                # For the large version, use the image itself
                url = f"{settings.MEDIA_URL}{self.get_s3_key()}"
                info = Blob.get_image_dimensions(self.get_s3_key(), max_cover_image_width)
            else:
                url = f"{prefix}/cover-{size}.jpg"
                info = Blob.get_image_dimensions(f"{PurePath(self.get_s3_key()).parent}/cover-{size}.jpg", max_cover_image_width)

        info["url"] = url

        return info

    @staticmethod
    def get_cover_info_static(user, sha1sum, size="large", max_cover_image_width=MAX_COVER_IMAGE_WIDTH):

        if sha1sum is None:
            return {"url": ""}

        b = Blob.objects.get(user=user, sha1sum=sha1sum)

        return b.get_cover_info(size, max_cover_image_width)

    def index_blob(self, file_changed=True):
        """
        Index the blob into Elasticsearch, but only if there is no
        file associated with it. If there is, then a lambda will be
        triggered once it's written to S3 to do the indexing
        """

        client = boto3.client("sns")

        message = {
            "Records": [
                {
                    "s3": {
                        "bucket": {
                            "name": settings.AWS_STORAGE_BUCKET_NAME
                        },
                        "uuid": str(self.uuid),
                        "file_changed": file_changed
                    }
                }
            ]
        }

        client.publish(
            TopicArn="arn:aws:sns:us-east-1:192218769908:NewS3Blob",
            Message=json.dumps(message),
        )

    def tree(self):
        return defaultdict(self.tree)

    def get_tree(self):

        if not self.content:
            return []

        content_out = ""

        nodes = defaultdict(self.tree)

        nodes["label"] = "root"
        nodes["nodes"] = []  # Necessary?

        node_id = 1
        current_node = nodes
        current_level = None
        current_label = "root"

        top_level = None

        for line in self.content.split("\n"):
            x = re.search(r"^(#+)(.*)", line.strip())
            if x:

                content_out = f"{content_out}%#@!{node_id}!@#%\n{line}\n"
                level = len(x.group(1))
                heading = x.group(2).strip()

                if not top_level:
                    top_level = level

                if not current_level:
                    # This is the first level encountered. Note: might not be 1.
                    current_label = heading
                    current_level = level

                if level > current_level:
                    for node in current_node["nodes"]:
                        if node["label"] == current_label:
                            node["nodes"].append(
                                {
                                    "id": node_id,
                                    "label": heading,
                                    "nodes": []
                                }
                            )
                            current_node = node

                elif current_level > level:

                    if level == top_level:
                        current_node = nodes
                    else:
                        current_node = nodes
                        for _ in range(level - top_level):
                            current_node = current_node["nodes"][-1]

                    current_node["nodes"].append(
                        {
                            "id": node_id,
                            "label": heading,
                            "nodes": []
                        }
                    )

                else:
                    current_node["nodes"].append(
                        {
                            "id": node_id,
                            "label": heading,
                            "nodes": []
                        }
                    )
                current_level = level
                current_label = heading
                node_id = node_id + 1

            else:
                content_out = f"{content_out}{line}\n"

        self.content = content_out

        return nodes["nodes"]

    def delete(self):

        # Delete from Elasticsearch

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        try:
            es.delete(index=settings.ELASTICSEARCH_INDEX, id=self.uuid)
        except NotFoundError:
            log.warning(f"Tried to delete blob, but can't find it in elasticsearch: {self.uuid}")

        # Delete from any collections
        for collection in Collection.objects.filter(user=self.user, blob_list__contains=[{'id': self.id}]):
            collection.blob_list = [x for x in collection.blob_list if x['id'] != self.id]
            collection.save()

        super().delete()


@receiver(post_save, sender=Blob)
def set_s3_metadata_file_modified(sender, instance, **kwargs):
    """
    Store a file's modification time as S3 metadata after it's saved.
    """

    # instance.file_modified will be "None" if we're editing a blob's
    # information or renaming the file, but not changing the file itself.
    # In that case we don't want to update its "file_modified" metadata.
    if not instance.file or not instance.file_modified:
        return

    s3 = boto3.resource("s3")
    key = instance.get_s3_key()

    s3_object = s3.Object(settings.AWS_STORAGE_BUCKET_NAME, key)

    s3_object.metadata.update({"file-modified": str(instance.file_modified)})

    # Note: since "Content-Type" is system-defined metadata, it will be reset
    #  to "binary/octent-stream" if you don't explicitly specify it.
    s3_object.copy_from(
        ContentType=s3_object.content_type,
        CopySource={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        Metadata=s3_object.metadata,
        MetadataDirective="REPLACE"
    )


@receiver(pre_save, sender=Blob)
def mymodel_pre_save(sender, instance, **kwargs):

    # Use a custom S3 location for the blob, based on the blob's UUID
    instance.file.storage.location = f"blobs/{instance.uuid}"


@receiver(pre_delete, sender=Blob)
def mymodel_delete_s3(sender, instance, **kwargs):

    if instance.file:

        dir = f"{settings.MEDIA_ROOT}/{instance.uuid}"
        s3 = boto3.resource("s3")
        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        # TODO: Add sanity check to prevent unwanted deletes?
        for fn in my_bucket.objects.filter(Prefix=dir):
            log.info(f"Deleting blob {fn}")
            fn.delete()

        # Pass false so FileField doesn't save the model.
        instance.file.delete(False)


class MetaData(TimeStampedModel):
    name = models.TextField()
    value = models.TextField()
    blob = models.ForeignKey(Blob, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'value', 'blob')

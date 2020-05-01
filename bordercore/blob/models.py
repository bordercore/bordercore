import hashlib
import json
import logging
import re
import urllib.parse
import uuid
from pathlib import PurePath
from urllib.parse import urlparse

import boto3
import markdown
from elasticsearch import Elasticsearch
from storages.backends.s3boto3 import S3Boto3Storage

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch.dispatcher import receiver

from blob.amazon import AmazonMixin
from collection.models import Collection
from lib.mixins import TimeStampedModel
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

# These blobs are too big to be indexed by Elasticsearch,
# generating "Broken pip" errors.

BLOBS_NOT_TO_INDEX = [
    "50d894af-8dad-44ab-a15e-2435dd8f827a",
    "56ba664e-e918-4598-b198-8e01da064f75",
    "95546f46-3842-49d4-93d3-82fad914e3ce",
    "9c461f7e-7a1b-4f44-a312-053184d803c0",
    "b9d3b971-682a-42ba-9db4-6b867edd60eb",
    "ed124f8d-e5c1-4221-bad4-74b64bac152e"
]

log = logging.getLogger(f"bordercore.{__name__}")


# Override FileSystemStorage to get better control of how files are named
class BlobFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise(Exception("name's length is greater than max_length"))
        return name

    # Override this to prevent Django from cleaning the name (eg replacing spaces with underscores)
    def get_valid_name(self, name):
        return name

    def _save(self, name, content):
        if self.exists(name):
            # if the file exists, do not call the superclasses _save method
            return name
        # if the file is new, DO call it
        return super(BlobFileSystemStorage, self)._save(name, content)


class DownloadableS3Boto3Storage(S3Boto3Storage):

    # Override this to prevent Django from cleaning the name (eg replacing spaces with underscores)
    def get_valid_name(self, name):
        return name

    def _save(self, name, content):
        """
        Override _save() to set a custom S3 location for the object
        """

        hasher = hashlib.sha1()
        for chunk in content.chunks():
            hasher.update(chunk)
        sha1sum = hasher.hexdigest()

        self.location = "blobs/{}/{}".format(sha1sum[0:2], sha1sum)
        return super()._save(name, content)


class Document(TimeStampedModel, AmazonMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    content = models.TextField(null=True)
    title = models.TextField(null=True)
    sha1sum = models.CharField(max_length=40, unique=True, blank=True, null=True)
    file = models.FileField(max_length=500, storage=DownloadableS3Boto3Storage())
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)
    date = models.TextField(null=True)
    importance = models.IntegerField(default=1)
    is_private = models.BooleanField(default=False)
    is_note = models.BooleanField(default=False)
    documents = models.ManyToManyField("self")

    def __init__(self, *args, **kwargs):
        super(Document, self).__init__(*args, **kwargs)

        # Save the sha1sum so that when it changes by a blob edit
        #  in save() we know what the original was.
        setattr(self, "__original_sha1sum", getattr(self, 'sha1sum'))

    def get_content(self):
        return markdown.markdown(self.content, extensions=['codehilite(guess_lang=False)', 'tables'])

    def get_note(self):
        return markdown.markdown(self.note, extensions=['codehilite(guess_lang=False)', 'tables'])

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
            "video/mp4": "Video"
        }

        return switcher.get(argument, "")

    def get_parent_dir(self):
        return "{}/{}/{}".format(settings.MEDIA_ROOT, self.sha1sum[0:2], self.sha1sum)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def get_url(self):
        return f"{self.sha1sum[0:2]}/{self.sha1sum}/{self.file}"

    def get_title(self, remove_edition_string=False, use_filename_if_present=False):
        title = self.title
        if title:
            if remove_edition_string:
                pattern = re.compile(r'(.*) (\d)E$')
                matches = pattern.match(title)
                if matches and EDITIONS.get(matches.group(2), None):
                    return "%s" % (matches.group(1))
            return title
        else:
            if use_filename_if_present:
                return PurePath(str(self.file)).name
            else:
                return "No title"

    def get_edition_string(self):
        if self.title:
            pattern = re.compile(r'(.*) (\d)E$')
            matches = pattern.match(self.title)
            if matches and EDITIONS.get(matches.group(2), None):
                return "%s Edition" % (EDITIONS[matches.group(2)])

        return ""

    @staticmethod
    def get_s3_key_from_sha1sum(sha1sum, file):
        return "{}/{}/{}/{}".format(settings.MEDIA_ROOT, sha1sum[0:2], sha1sum, file)

    def get_s3_key(self):
        if self.file:
            return "{}/{}/{}/{}".format(settings.MEDIA_ROOT, self.sha1sum[0:2], self.sha1sum, self.file)
        else:
            return None

    def get_urls(self):

        return [
            {
                "url": x.value,
                "domain": urlparse(x.value).netloc
            }
            for x
            in self.metadata_set.filter(name="Url")
        ]

    def get_metadata(self):

        metadata = {}

        for x in self.metadata_set.all():
            if metadata.get(x.name, None):
                metadata[x.name] = ", ".join([metadata[x.name], x.value])
            else:
                metadata[x.name] = x.value

        return metadata

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
                                "uuid.keyword": self.uuid
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
            "_source": ["author", "task", "content_type", "doctype", "note", "filename", "bordercore_id", "attr_is_book", "last_modified", "num_pages", "tags", "title", "sha1sum", "size", "url"]
        }

        results = es.search(index=settings.ELASTICSEARCH_INDEX, body=query)["hits"]["hits"][0]

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

        super(Document, self).save(*args, **kwargs)

        if self.sha1sum:

            # This is set in __init__
            sha1sum_orig = getattr(self, '__original_sha1sum')

            sha1sum_new = self.sha1sum
            if sha1sum_orig is not None and sha1sum_orig != sha1sum_new:
                log.info(f"Updating file from sha1sum={sha1sum_orig} to sha1sum={sha1sum_new}")
                self.change_file(sha1sum_orig)

    def change_file(self, old_sha1sum):

        # Sanity check to prevent unwanted deletions
        pattern = re.compile(r"\b[0-9a-f]{40}\b")
        if not re.match(pattern, old_sha1sum):
            log.error(f"Trying to update a sha1sum, but given invalid sha1sum: {old_sha1sum}")
            return

        dir_old = f"{settings.MEDIA_ROOT}/{old_sha1sum[:2]}/{old_sha1sum}"

        s3 = boto3.resource("s3")
        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        for fn in my_bucket.objects.filter(Prefix=dir_old):
            log.info(f"Deleting key {fn.key}")
            s3.Object(settings.AWS_STORAGE_BUCKET_NAME, fn.key).delete()

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
            related_blobs.append({'uuid': blob.uuid, 'title': blob.title})
        return related_blobs

    def get_collection_info(self):
        return Collection.objects.filter(user=self.user, blob_list__contains=[{'id': self.id}])

    def has_thumbnail_url(self):
        try:
            _ = Document.get_cover_info(self.user, self.sha1sum, size='small')['url']
            return True
        except Exception:
            return False

    def get_cover_url_small(self):
        return Document.get_cover_info(self.user, self.sha1sum, size='small')['url']

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

    @staticmethod
    def get_cover_info(user, sha1sum, size="large", max_cover_image_width=MAX_COVER_IMAGE_WIDTH):
        if sha1sum is None:
            return {}

        info = {}
        url = None

        b = Document.objects.get(user=user, sha1sum=sha1sum)

        prefix = PurePath(b.get_s3_key()).parent

        file_extension = PurePath(b.file.name).suffix

        if size != "large":
            url = f"{prefix}/cover.jpg"
        else:
            # Is the blob itself an image?
            if file_extension[1:].lower() in ["gif", "jpg", "jpeg", "png"]:
                # For the large version, use the image itself
                url = b.get_s3_key()
                info = Document.get_image_dimensions(url, max_cover_image_width)
            else:
                url = f"{prefix}/cover-{size}.jpg"
                info = Document.get_image_dimensions(url, max_cover_image_width)

        info["url"] = urllib.parse.quote(url)

        return info

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

        response = client.publish(
            TopicArn="arn:aws:sns:us-east-1:192218769908:NewS3Blob",
            Message=json.dumps(message),
        )
        # TODO: Handle response errors

    def delete(self):

        # Delete from Elasticsearch

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        es.delete(index=settings.ELASTICSEARCH_INDEX, id=self.uuid)

        # Delete from any collections
        for collection in Collection.objects.filter(user=self.user, blob_list__contains=[{'id': self.id}]):
            collection.blob_list = [x for x in collection.blob_list if x['id'] != self.id]
            collection.save()

        super(Document, self).delete()


@receiver(post_save, sender=Document)
def set_s3_metadata_file_modified(sender, instance, **kwargs):
    """
    Store a file's modification time as S3 metadata after it's saved.
    """

    # instance.file_modified will be "None" if we're editing a blob's
    # information, but not changing the blob itself. In that case we
    # don't want to update its "file_modified" metadata.
    if not instance.file or instance.file_modified is None:
        return

    s3 = boto3.resource("s3")
    key = instance.get_s3_key()

    s3_object = s3.Object(settings.AWS_STORAGE_BUCKET_NAME, key)

    s3_object.metadata.update({"file-modified": str(instance.file_modified)})
    s3_object.copy_from(CopySource={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key}, Metadata=s3_object.metadata, MetadataDirective="REPLACE")


@receiver(pre_delete, sender=Document)
def mymodel_delete_s3(sender, instance, **kwargs):

    if instance.file:

        dir = "{}/{}/{}".format(settings.MEDIA_ROOT, instance.sha1sum[0:2], instance.sha1sum)
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
    blob = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('name', 'value', 'blob')

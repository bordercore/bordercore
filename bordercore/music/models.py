import uuid

import boto3
import markdown
from elasticsearch import Elasticsearch
from markdown.extensions.codehilite import CodeHiliteExtension

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Album(TimeStampedModel):
    title = models.TextField()
    artist = models.TextField()
    year = models.IntegerField()
    original_release_year = models.IntegerField(null=True)
    compilation = models.BooleanField(default=False)
    comment = models.TextField(null=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def get_comment(self):
        return markdown.markdown(self.comment, extensions=[CodeHiliteExtension(guess_lang=False), "tables"])

    class Meta:
        unique_together = ("title", "artist")


class SongSource(TimeStampedModel):
    name = models.TextField()
    description = models.TextField()

    def __unicode__(self):
        return self.name


class Song(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.TextField()
    artist = models.TextField()
    album = models.ForeignKey(Album, null=True, on_delete=models.PROTECT)
    track = models.IntegerField(null=True)
    year = models.IntegerField(null=True)
    length = models.IntegerField(blank=True, null=True)
    comment = models.TextField(null=True)
    source = models.ForeignKey(SongSource, on_delete=models.PROTECT)
    last_time_played = models.DateTimeField(null=True)
    times_played = models.IntegerField(default=0, blank=True, null=True)
    original_album = models.TextField(null=True)
    original_year = models.IntegerField(null=True)
    tags = models.ManyToManyField(Tag)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

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
                                "doctype": "song"
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

        super(Song, self).delete()

    def index_song(self, es=None):

        if not es:
            es = Elasticsearch(
                [settings.ELASTICSEARCH_ENDPOINT],
                verify_certs=False
            )

        doc = {
            "uuid": self.uuid,
            "bordercore_id": self.id,
            "title": self.title,
            "artist": self.artist,
            "year": self.year,
            "track": self.track,
            "tags": [tag.name for tag in self.tags.all()],
            "note": self.comment,
            "last_modified": self.modified,
            "doctype": "song",
            "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
            "date_unixtime": self.created.strftime("%s"),
            "user_id": self.user.id
        }

        if self.album:
            doc["album"] = self.album.title
            doc["album_id"] = self.album.id

        es.index(
            index=settings.ELASTICSEARCH_INDEX,
            id=self.uuid,
            body=doc
        )


@receiver(post_save, sender=Song)
def post_save_wrapper(sender, instance, **kwargs):
    """
    This should be called anytime a song is created or updated.
    """

    # Index the song in Elasticsearch
    instance.index_song()


@receiver(post_delete, sender=Song)
def mymodel_delete_s3(sender, instance, **kwargs):
    """
    Remove the song from S3 after the model is deleted
    """

    s3_client = boto3.client("s3")

    s3_client.delete_object(
        Bucket=settings.AWS_BUCKET_NAME_MUSIC,
        Key=f"songs/{instance.uuid}"
    )


class Listen(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

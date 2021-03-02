import hashlib
import os
import uuid

import boto3
import humanize
import markdown
from elasticsearch import Elasticsearch
from markdown.extensions.codehilite import CodeHiliteExtension
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse

from lib.mixins import TimeStampedModel
from lib.time_utils import convert_seconds
from tag.models import Tag


class Album(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
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

    def __str__(self):
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
                                "uuid": self.uuid
                            }
                        },

                    ]
                }
            }
        }

        es.delete_by_query(index=settings.ELASTICSEARCH_INDEX, body=request_body)

        super().delete()

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
            doc["album_uuid"] = self.album.uuid

        es.index(
            index=settings.ELASTICSEARCH_INDEX,
            id=self.uuid,
            body=doc
        )

    @staticmethod
    def get_id3_info(request, messages, song):
        """
        Write a song to the file system and extract its ID3 information
        """

        sha1sum = hashlib.sha1(song).hexdigest()
        filename = f"/tmp/{request.user.userprofile.uuid}-{sha1sum}.mp3"

        try:
            f = open(filename, "wb")
            f.write(song)
            f.close()
        except (IOError) as e:
            messages.add_message(request, messages.ERROR, f"IOError: {e}")

        info = MP3(filename, ID3=EasyID3)

        data = {
            "filesize": humanize.naturalsize(os.stat(filename).st_size),
            "sha1sum": sha1sum,
            "bit_rate": info.info.bitrate,
            "sample_rate": info.info.sample_rate
        }

        for field in ("artist", "title"):
            data[field] = info[field][0] if info.get(field) else None
        if info.get("date"):
            data["year"] = info["date"][0]
        if info.get("album"):
            data["album_name"] = info["album"][0]
        data["length"] = int(info.info.length)
        data["length_pretty"] = convert_seconds(info.info.length)

        if info.get("tracknumber"):
            track_info = info["tracknumber"][0].split("/")
            track_number = track_info[0]
            data["track"] = track_number

        return data

    @staticmethod
    def get_album_info(user, song_info):

        # If an album was specified, check if we have the album
        if song_info["album_name"]:
            album_artist = song_info["album_artist"] if song_info["compilation"] else song_info["artist"]
            album_info = None
            try:
                album_info = Album.objects.get(user=user,
                                               title=song_info["album_name"],
                                               artist=album_artist)
            except ObjectDoesNotExist:
                pass
            if not album_info:
                # No existing album found. Create a new one.
                album_info = Album(user=user,
                                   title=song_info["album_name"],
                                   artist=album_artist,
                                   year=song_info["year"],
                                   original_release_year=song_info.get("original_release_year", None) or song_info["year"],
                                   compilation=song_info["compilation"])
                album_info.save()
        else:
            # No album was specified
            album_info = None

        return album_info

    @staticmethod
    def get_song_url(song):
        """
        Get the appropriate page url for a song.
        If the song is part of an album, return the album detail page.
        Otherwise return the artist detai page.
        """

        if song.album:
            listen_url = reverse("music:album_detail", args=[song.album.uuid])
        else:
            listen_url = reverse("music:artist_detail", args=[song.artist])

        return listen_url


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

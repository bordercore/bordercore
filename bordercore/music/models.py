"""
Models for music management application.

This module contains models for managing artists, albums, songs, playlists, and listening history
with support for Elasticsearch indexing and AWS S3 storage.
"""

import io
import uuid
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import boto3
import humanize
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Count, JSONField, Model, Sum
from django.db.models.functions import Coalesce
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from lib.mixins import SortOrderMixin, TimeStampedModel
from lib.time_utils import convert_seconds
from lib.util import remove_non_ascii_characters
from search.services import delete_document, index_document
from tag.models import Tag


class Artist(TimeStampedModel):
    """An artist is a musical performer or group that creates songs and albums.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("name", "user")

    def __str__(self) -> str:
        """Return string representation of the artist.

        Returns:
            The artist's name.
        """
        return self.name


class Album(TimeStampedModel):
    """An album is a collection of songs released together by an artist that can be tagged and tracked.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.TextField()
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT)
    year = models.IntegerField()
    original_release_year = models.IntegerField(null=True)
    compilation = models.BooleanField(default=False)
    note = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("title", "artist")

    def __str__(self) -> str:
        """Return string representation of the album.

        Returns:
            The album title.
        """
        return self.title

    def get_tags(self) -> str:
        """Get all tags associated with this album as a comma-separated string.

        Returns:
            Comma-separated string of tag names.
        """
        return ", ".join([tag.name for tag in self.tags.all()])

    @property
    def playtime(self) -> str:
        """Get the total album playtime in a humanized format.

        Returns:
            Humanized string representation of the total album duration.
        """

        total_time_seconds = Song.objects.filter(
            album=self
        ).aggregate(
            total_time=Coalesce(Sum("length"), 0)
        )["total_time"]

        return humanize.precisedelta(
            timedelta(seconds=total_time_seconds),
            minimum_unit="minutes",
            format="%.f"
        )

    def index_album(self) -> None:
        """Index this album in Elasticsearch."""
        index_document(self.elasticsearch_document)

    @property
    def elasticsearch_document(self) -> Dict[str, Any]:
        """Return a representation of the album suitable for indexing in Elasticsearch.

        Returns:
            Dictionary containing the album data formatted for Elasticsearch indexing.
        """

        return {
            "_index": settings.ELASTICSEARCH_INDEX,
            "_id": self.uuid,
            "_source": {
                "uuid": self.uuid,
                "bordercore_id": self.id,
                "title": self.title,
                "artist": self.artist.name,
                "artist_uuid": self.artist.uuid,
                "year": self.year,
                "original_release_year": self.original_release_year,
                "compilation": self.compilation,
                "tags": [tag.name for tag in self.tags.all()],
                "note": self.note,
                "last_modified": self.modified,
                "doctype": "album",
                "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
                "date_unixtime": self.created.strftime("%s"),
                "user_id": self.user.id,
                **settings.ELASTICSEARCH_EXTRA_FIELDS
            }
        }

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the album and index it in Elasticsearch.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().save(*args, **kwargs)

        # Index the album in Elasticsearch
        self.index_album()

    def delete(
            self,
            using: Any | None = None,
            keep_parents: bool = False,
    ) -> tuple[int, dict[str, int]]:
        """Delete the album and remove it from Elasticsearch."""
        delete_document(str(self.uuid))
        return super().delete(using=using, keep_parents=keep_parents)

    @staticmethod
    def scan_zipfile(zipfile_obj: bytes, include_song_data: bool = False) -> Dict[str, Any]:
        """Scan a ZIP file containing MP3 files and extract metadata.

        Args:
            zipfile_obj: ZIP file content as bytes.
            include_song_data: Whether to include the actual song data in the result.

        Returns:
            Dictionary containing album, artist, and song information from the ZIP file.
        """
        song_info = []
        artist = set()
        album = None

        with zipfile.ZipFile(BytesIO(zipfile_obj), mode="r") as archive:
            for file in archive.infolist():
                if file.filename.endswith("mp3"):
                    with archive.open(file.filename) as myfile:
                        song_data = myfile.read()
                        id3_info = Song.get_id3_info(song_data)
                        if include_song_data:
                            id3_info["data"] = song_data
                        song_info.append(id3_info)
                        artist.add(id3_info["artist"])
                        album = id3_info["album_name"]

        return {
            "album": album,
            "artist": list(artist),
            "song_info": song_info,
        }

    @staticmethod
    def create_album_from_zipfile(
        zipfile_obj: bytes,
        artist_name: str,
        song_source: "SongSource",
        tags: Optional[str],
        user: User,
        changes: Dict[str, Dict[str, Any]]
    ) -> UUID:
        """Create an album from a ZIP file containing MP3 files.

        Args:
            zipfile_obj: ZIP file content as bytes.
            artist_name: Name of the artist.
            song_source: The source where the songs came from.
            tags: Comma-separated string of tags to apply to songs.
            user: The user creating the album.
            changes: Dictionary of changes to apply to specific tracks.

        Returns:
            UUID of the created album.
        """
        info = Album.scan_zipfile(zipfile_obj, include_song_data=True)

        artist, _ = Artist.objects.get_or_create(name=artist_name, user=user)

        album = Song.get_or_create_album(
            user,
            {
                "album_name": info["song_info"][0]["album_name"],
                "artist": artist,
                "compilation": False,
                "year": info["song_info"][0]["year"],
            }
        )

        for song_info in info["song_info"]:
            song = Song(
                artist=artist,
                album=album,
                length=song_info["length"],
                source=song_source,
                title=song_info["title"],
                track=song_info["track"],
                user=user,
                year=song_info["year"],
            )
            # Edit the title and add a note if the user made any changes
            if changes.keys():
                note = changes[str(song_info["track"])].get("note", None)
                if note:
                    song.note = note
                title_edited = changes[str(song_info["track"])].get("title", None)
                if title_edited:
                    song.title = title_edited
            song.save()

            if tags:
                song.tags.set(
                    [
                        Tag.objects.get_or_create(name=tag, user=user)[0]
                        for tag in
                        tags.split(",")
                    ]
                )

            # Upload the song and its artwork to S3
            Song.handle_s3(song, song_info["data"])

        if album is not None:
            return album.uuid
        raise ValueError("Album creation failed unexpectedly")


class SongSource(TimeStampedModel):
    """A song source is a platform or service where songs can be acquired or imported from.
    """
    name = models.TextField()
    description = models.TextField()

    DEFAULT = "Amazon"

    def __str__(self) -> str:
        """Return string representation of the song source.

        Returns:
            The source name.
        """
        return self.name


class Song(TimeStampedModel):
    """A song is an individual musical track that can be played, rated, tagged, and organized within albums.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.TextField()
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT)
    album = models.ForeignKey(Album, null=True, on_delete=models.PROTECT)
    track = models.IntegerField(null=True)
    year = models.IntegerField(null=True)
    length = models.IntegerField(blank=True, null=True)
    note = models.TextField(null=True)
    source = models.ForeignKey(SongSource, on_delete=models.PROTECT)
    rating = models.IntegerField(blank=True, null=True)
    last_time_played = models.DateTimeField(null=True)
    times_played = models.IntegerField(default=0, blank=True, null=True)
    original_album = models.TextField(null=True)
    original_year = models.IntegerField(null=True)
    tags = models.ManyToManyField(Tag)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self) -> str:
        """Return string representation of the song.

        Returns:
            The song title.
        """
        return self.title

    def get_tags(self) -> str:
        """Get all tags associated with this song as a comma-separated string.

        Returns:
            Comma-separated string of tag names.
        """
        return ", ".join([tag.name for tag in self.tags.all()])

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the song and index it in Elasticsearch.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().save(*args, **kwargs)

        # Index the song in Elasticsearch
        self.index_song()

    def delete(
            self,
            using: Any | None = None,
            keep_parents: bool = False,
    ) -> tuple[int, dict[str, int]]:
        """Delete the song, remove it from Elasticsearch, and delete from S3."""
        result = super().delete()

        # Delete from Elasticsearch
        delete_document(str(self.uuid))

        # Delete from S3
        s3_client = boto3.client("s3")

        s3_client.delete_object(
            Bucket=settings.AWS_BUCKET_NAME_MUSIC,
            Key=f"songs/{self.uuid}"
        )

        return result

    def index_song(self) -> None:
        """Index this song in Elasticsearch."""
        index_document(self.elasticsearch_document)

    @property
    def elasticsearch_document(self) -> Dict[str, Any]:
        """Return a representation of the song suitable for indexing in Elasticsearch.

        Returns:
            Dictionary containing the song data formatted for Elasticsearch indexing.
        """

        doc = {
            "_index": settings.ELASTICSEARCH_INDEX,
            "_id": self.uuid,
            "_source": {
                "uuid": self.uuid,
                "bordercore_id": self.id,
                "title": self.title,
                "artist": self.artist.name,
                "artist_uuid": self.artist.uuid,
                "year": self.year,
                "track": self.track,
                "tags": [tag.name for tag in self.tags.all()],
                "note": self.note,
                "last_modified": self.modified,
                "doctype": "song",
                "date": {
                    "gte": self.created.strftime("%Y-%m-%d %H:%M:%S"),
                    "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")
                },
                "date_unixtime": self.created.strftime("%s"),
                "user_id": self.user.id,
                **settings.ELASTICSEARCH_EXTRA_FIELDS
            }
        }

        if self.album:
            doc["_source"]["album"] = self.album.title
            doc["_source"]["album_uuid"] = str(self.album.uuid)

        return doc

    @property
    def url(self) -> str:
        """Get the appropriate page URL for a song.

        If the song is part of an album, return the album detail page.
        Otherwise return the artist detail page.

        Returns:
            URL string for the song's detail page.
        """
        if self.album:
            url = reverse("music:album_detail", args=[self.album.uuid])
        else:
            url = reverse("music:artist_detail", args=[self.artist.uuid])

        return url

    def listen_to(self) -> None:
        """Increment a song's 'times played' counter and update its 'last time played' timestamp.

        Also creates a Listen record for tracking purposes.
        """
        current_plays = self.times_played or 0
        self.times_played = current_plays + 1
        self.last_time_played = datetime.now()
        self.save()

        Listen(song=self, user=self.user).save()

    @staticmethod
    def get_id3_info(song: bytes) -> Dict[str, Any]:
        """Read a song's ID3 information.

        Args:
            song: Song data as bytes.

        Returns:
            Dictionary containing the song's metadata.
        """

        info = MP3(fileobj=BytesIO(song), ID3=EasyID3)

        data = {
            "filesize": humanize.naturalsize(len(song)),
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
    def get_or_create_album(user: User, song_info: Dict[str, Any]) -> Optional[Album]:
        """Get or create an album based on song information.

        Args:
            user: The user creating/owning the album.
            song_info: Dictionary containing song metadata including album information.

        Returns:
            Album instance if album information is available, None otherwise.
        """
        # If an album was specified, check if we have the album
        if song_info["album_name"]:
            album_artist = song_info["album_artist"] if song_info["compilation"] else song_info["artist"]
            album_info = None
            try:
                album_info = Album.objects.get(user=user,
                                               title=song_info["album_name"],
                                               artist=album_artist)
            except ObjectDoesNotExist:
                # No existing album found. Create a new one.

                artist, _ = Artist.objects.get_or_create(name=album_artist, user=user)

                album_info = Album(user=user,
                                   title=song_info["album_name"],
                                   artist=artist,
                                   year=song_info["year"],
                                   original_release_year=song_info.get("original_release_year", None) or song_info["year"],
                                   compilation=song_info["compilation"])
                album_info.save()
        else:
            # No album was specified
            album_info = None

        return album_info

    @staticmethod
    def get_song_tags(user: User) -> List[Dict[str, Union[str, int]]]:
        """Get a count of all song tags, grouped by tag.

        Args:
            user: The user whose song tags to retrieve.

        Returns:
            List of dictionaries containing tag names and their counts, sorted by count descending.
        """
        return sorted(
            Tag.objects.values("name").
            filter(
                song__isnull=False,
                song__user=user
            ).
            annotate(count=Count("song")),
            key=lambda s: s["count"],
            reverse=True
        )

    @staticmethod
    def handle_s3(song: "Song", song_bytes: bytes) -> None:
        """Handle uploading song and album artwork to S3.

        Args:
            song: The song instance to upload.
            song_bytes: The song data as bytes.
        """

        s3_client = boto3.client("s3")

        key = f"songs/{song.uuid}"
        fo = io.BytesIO(song_bytes)

        # Note: S3 Metadata cannot contain non ASCII characters
        s3_client.upload_fileobj(
            fo,
            settings.AWS_BUCKET_NAME_MUSIC,
            key,
            ExtraArgs={
                "Metadata": {
                    "artist": remove_non_ascii_characters(song.artist.name, default="Artist"),
                    "title": remove_non_ascii_characters(song.title, default="Title")
                }
            }
        )

        if not song.album:
            return

        fo = io.BytesIO(song_bytes)
        audio = MP3(fileobj=fo)

        if audio:
            artwork = audio.tags.getall("APIC")
            if artwork:
                key = f"album_artwork/{song.album.uuid}"
                s3_client.upload_fileobj(
                    io.BytesIO(artwork[0].data),
                    settings.AWS_BUCKET_NAME_MUSIC,
                    key,
                    ExtraArgs={"ContentType": "image/jpeg"}
                )


class Playlist(TimeStampedModel):
    """A playlist is a curated collection of songs that can be manually created or automatically generated based on criteria.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    note = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    size = models.IntegerField(null=True, blank=True)
    parameters = JSONField(null=True, blank=True)

    def __str__(self) -> str:
        """Return string representation of the playlist.

        Returns:
            The playlist name.
        """
        return self.name

    def get_absolute_url(self) -> str:
        """Get the absolute URL for this playlist.

        Returns:
            URL string for the playlist detail page.
        """
        return reverse("music:playlist_detail", kwargs={"uuid": self.uuid})

    class PlaylistType(models.TextChoices):
        """Enumeration of playlist types."""
        MANUAL = "manual", _("Manually Selected")
        TAG = "smart", _("Smart")

    type = models.CharField(
        max_length=100,
        choices=PlaylistType.choices,
        default=PlaylistType.MANUAL,
    )

    def populate(self, refresh: bool = False) -> None:
        """Populate a smart playlist based on its parameters.

        Args:
            refresh: If True, clear existing playlist items before populating.

        Raises:
            ValueError: If called on a manual playlist.
        """
        if self.type == "manual":
            raise ValueError("You cannot call populate() on a manual playlist.")

        if not self.parameters:
            return

        # If refresh is true, then populate the playlist with all new songs
        if refresh:
            PlaylistItem.objects.filter(playlist=self).delete()

        song_list = Song.objects.all()

        if "tag" in self.parameters:
            song_list = song_list.filter(tags__name=self.parameters["tag"])

        if "rating" in self.parameters:
            song_list = song_list.filter(rating=int(self.parameters["rating"]))

        if self.parameters.get("start_year", None) and self.parameters.get("end_year", None):
            song_list = song_list.annotate(
                year_effective=Coalesce("original_year", "year")). \
                filter(
                    year_effective__gte=self.parameters["start_year"],
                    year_effective__lte=self.parameters["end_year"],
                )

        if self.parameters.get("exclude_albums", False):
            song_list = song_list.exclude(album__isnull=False)

        if "exclude_recent" in self.parameters:
            song_list = song_list.exclude(last_time_played__gte=timezone.now() - timedelta(days=int(self.parameters["exclude_recent"])))

        # If we're not returning recently added songs, randomize the final list
        if self.parameters.get("sort_by") == "recent":
            song_list = song_list.order_by("-created")
        elif self.parameters.get("sort_by") == "random":
            song_list = song_list.order_by("?")

        if self.size:
            song_list = song_list[:self.size]

        # This seems like a good candidate for bulk_create(), but that will
        #  result in all new items having sort_order=1
        for song in song_list:
            playlistitem = PlaylistItem(playlist=self, song=song)
            playlistitem.save()


class PlaylistItem(TimeStampedModel, SortOrderMixin):
    """A playlist item is an individual song entry within a playlist that maintains sort order and relationships.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    field_name = "playlist"

    def __str__(self) -> str:
        """Return string representation of the playlist item.

        Returns:
            String showing the playlist and song relationship.
        """
        return f"{self.playlist} - {self.song}"

    class Meta:
        unique_together = (
            ("playlist", "song")
        )


@receiver(pre_delete, sender=PlaylistItem)
def remove_playlistitem(sender: type[Model], instance: PlaylistItem, **kwargs: Any) -> None:
    """
    Signal handler to clean up when a PlaylistItem is deleted.
    """
    instance.handle_delete()


class Listen(TimeStampedModel):
    """A listen is a recorded event that tracks when a user plays a specific song for analytics and history purposes.
    """
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    def __str__(self) -> str:
        """Return string representation of the listen event.

        Returns:
            String describing the listen event.
        """
        return str(f"Listened to song '{self.song}'")

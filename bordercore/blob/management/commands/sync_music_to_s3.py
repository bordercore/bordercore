import string
from pathlib import Path

import boto3
from botocore.errorfactory import ClientError

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from music.models import Song
from music.views import get_song_location


class Command(BaseCommand):
    help = "Sync all filesystem blobs to S3"

    BLOB_DIR = "/home/media"
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    printable = set(string.printable)

    def add_arguments(self, parser):
        parser.add_argument(
            "--uuid",
            help="The uuid of a single song to index",
        )
        parser.add_argument(
            "--dry-run",
            help="Dry run. Take no action",
            action="store_true"
        )
        parser.add_argument(
            "--verbose",
            help="Increase verbosity",
            action="store_true"
        )

    @atomic
    def handle(self, *args, uuid, dry_run, verbose, **kwargs):

        self.s3 = boto3.resource("s3")
        s3_client = boto3.client("s3")

        if uuid:
            song_list = Song.objects.filter(uuid=uuid)
        else:
            song_list = Song.objects.all()

        for s in song_list:
            key = f"songs/{s.uuid}"

            try:
                s3_client.head_object(Bucket=self.bucket_name, Key=key)
                if verbose:
                    self.stdout.write("{s.uuid} Song already exists in S3")
            except ClientError:

                tracknumber = str(s.track)
                if len(tracknumber) == 1:
                    tracknumber = "0" + tracknumber

                file_path = self.BLOB_DIR + get_song_location(s)["url"]

                if not Path(file_path).is_file():
                    self.stdout.write(f"  Error: file not found: {s.uuid} {file_path}")
                    continue

                # Non-ascii characters aren't allowed as metadata. Remove them.
                clean_title = "".join(filter(lambda x: x in self.printable, s.title))
                clean_artist = "".join(filter(lambda x: x in self.printable, s.artist))

                self.stdout.write(f"{s.uuid} Synching to S3: {s.artist} - {s.title}")

                if not dry_run:
                    s3_client.upload_file(
                        file_path,
                        self.bucket_name,
                        key,
                        ExtraArgs={"Metadata": {"artist": clean_artist, "title": clean_title}})

                    if (s.album):
                        self.update_album_artwork(s.album)

    def update_album_artwork(self, song):

        key = f"artwork/{song.album.id}"

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
        except ClientError:

            artist_name = "Various" if song.album.compilation else song.album.artist

            file_path = f"{self.BLOB_DIR}/music/albums/{artist_name}/{song.album.title}/artwork.jpg"

            if not Path(file_path).is_file():
                self.stdout.write(f"  Error: album artwork not found: {file_path}")
                return

            self.s3_client.upload_file(file_path, self.bucket_name, key)

            # Set the ACL to be public read-only
            object_acl = self.s3.ObjectAcl(self.bucket_name, key)
            object_acl.put(ACL="public-read")

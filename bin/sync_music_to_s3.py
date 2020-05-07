import os
import os.path
import string
import sys
from time import sleep

import boto3
from botocore.errorfactory import ClientError

import django
from django.conf import settings

from music.models import Song
from music.views import get_song_location

django.setup()


file_prefix = "/home/media"

s3_client = boto3.client("s3")
s3 = boto3.resource("s3")

bucket_name = settings.AWS_BUCKET_NAME_MUSIC

printable = set(string.printable)


def update_album_artwork(album):

    key = f"artwork/{album.id}"

    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
    except ClientError:

        artist_name = "Various" if album.compilation else s.artist

        file_path = f"{file_prefix}/music/albums/{artist_name}/{s.album.title}/artwork.jpg"

        if not os.path.isfile(file_path):
            print(f"  Error: album artwork not found: {file_path}")
            return

        s3_client.upload_file(file_path, bucket_name, key)

        # Set the ACL to be public read-only
        object_acl = s3.ObjectAcl(bucket_name, key)
        object_acl.put(ACL="public-read")


uuid = None

try:
    uuid = sys.argv[1]
except IndexError:
    pass

if uuid:
    song_list = Song.objects.filter(uuid=uuid)
else:
    song_list = Song.objects.all()

for s in song_list:
    print(f"{s.artist} - {s.title}")
    key = f"songs/{s.uuid}"

    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        print("  Skipping. Object already exists in S3")
    except ClientError:

        tracknumber = str(s.track)
        if len(tracknumber) == 1:
            tracknumber = "0" + tracknumber

        file_path = file_prefix + get_song_location(s)["url"]

        if not os.path.isfile(file_path):
            print(f"  Error: file not found: {s.uuid} {file_path}")
            continue

        # Non-ascii characters aren't allowed as metadata. Remove them.
        clean_title = "".join(filter(lambda x: x in printable, s.title))
        clean_artist = "".join(filter(lambda x: x in printable, s.artist))

        s3_client.upload_file(
            file_path,
            bucket_name,
            key,
            ExtraArgs={"Metadata": {"artist": clean_artist, "title": clean_title}})

        if (s.album):
            update_album_artwork(s.album)

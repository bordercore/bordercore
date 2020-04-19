import boto3
import pytest
from botocore.errorfactory import ClientError

import django
from django.conf import settings

from music.models import Song

pytestmark = pytest.mark.data_quality

django.setup()


bucket_name = settings.AWS_BUCKET_NAME_MUSIC

s3_client = boto3.client("s3")


def test_album_songs_have_length_field():
    "Assert that all album songs have a length field"
    s = Song.objects.filter(length__isnull=True).filter(album__isnull=False)
    assert len(s) == 0, "%s songs fail this test" % len(s)


def test_all_songs_exist_in_s3():

    songs = Song.objects.all().only("uuid")

    for song in songs:
        try:
            key = f"songs/{song.uuid}"
            s3_client.head_object(Bucket=bucket_name, Key=key)
        except ClientError:
            assert False, f"song not found in S3: {song.uuid}"

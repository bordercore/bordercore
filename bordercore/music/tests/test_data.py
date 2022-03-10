import re
from pathlib import Path

import boto3
import pytest
from botocore.errorfactory import ClientError

import django
from django.conf import settings

from lib.util import get_elasticsearch_connection, get_missing_blob_ids
from music.models import Album, Song

pytestmark = pytest.mark.data_quality

django.setup()


bucket_name = settings.AWS_BUCKET_NAME_MUSIC

s3_client = boto3.client("s3")


@pytest.fixture()
def es():

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)
    yield es


def test_album_songs_have_length_field():
    "Assert that all album songs have a length field"
    s = Song.objects.filter(length__isnull=True)
    assert len(s) == 0, "%s songs fail this test" % len(s)


def test_all_songs_exist_in_s3():

    songs = Song.objects.all().only("uuid")

    for song in songs:
        try:
            key = f"songs/{song.uuid}"
            s3_client.head_object(Bucket=bucket_name, Key=key)
        except ClientError:
            assert False, f"song not found in S3: {song.uuid}"


def test_songs_in_db_exist_in_elasticsearch(es):
    "Assert that all songs in the database exist in Elasticsearch"

    songs = Song.objects.all().only("uuid")
    step_size = 100
    song_count = songs.count()

    for batch in range(0, song_count, step_size):

        # The batch_size will always be equal to "step_size", except probably
        #  the last batch, which will be less.
        batch_size = step_size if song_count - batch > step_size else song_count - batch

        query = [
            {
                "term": {
                    "_id": str(x.uuid)
                }
            }
            for x
            in songs[batch:batch + step_size]
        ]

        search_object = {
            "query": {
                "bool": {
                    "should": query
                }
            },
            "size": batch_size,
            "_source": [""]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

        assert found["hits"]["total"]["value"] == batch_size,\
            "songs found in the database but not in Elasticsearch: " + get_missing_blob_ids(songs[batch:batch + step_size], found)


def test_songs_in_s3_exist_in_db():
    "Assert that all songs in S3 also exist in the database"

    s3_resource = boto3.resource("s3")

    song_cache = {}
    for song in Song.objects.all().values("uuid"):
        song_cache[str(song["uuid"])] = True

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            match = re.search(r"^songs/(.+)", str(key["Key"]))
            if match:
                assert match.group(1) in song_cache, f"Song found in S3 but not in DB: {match.group(1)}"


def test_elasticsearch_songs_exist_in_s3(es):
    "Assert that all songs in Elasticsearch exist in S3"

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "doctype": "song"
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 10000,
        "_source": ["artist", "title", "uuid"]
    }

    songs_in_elasticsearch = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    s3_resource = boto3.resource("s3")

    songs_in_s3 = {}

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^songs/(.+)", str(key["Key"]))
            if m:
                songs_in_s3[m.group(1)] = True

    for song in songs_in_elasticsearch:
        if not song["_source"]["uuid"] in songs_in_s3:
            assert False, f"song {song['_source']['uuid']} exists in Elasticsearch but not in S3"


def test_albums_in_db_exist_in_elasticsearch(es):
    "Assert that all albums the database exist in Elasticsearch"

    albums = Album.objects.all().only("uuid")
    step_size = 100
    album_count = albums.count()

    for batch in range(0, album_count, step_size):

        # The batch_size will always be equal to "step_size", except probably
        #  the last batch, which will be less.
        batch_size = step_size if album_count - batch > step_size else album_count - batch

        query = [
            {
                "term": {
                    "_id": str(x.uuid)
                }
            }
            for x
            in albums[batch:batch + step_size]
        ]

        search_object = {
            "query": {
                "bool": {
                    "should": query
                }
            },
            "size": batch_size,
            "_source": [""]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

        assert found["hits"]["total"]["value"] == batch_size,\
            "albums found in the database but not in Elasticsearch: " + get_missing_blob_ids(albums[batch:batch + step_size], found)


@pytest.mark.wumpus
def test_song_in_s3_exist_on_filesystem():
    "Assert that all songs in S3 also exist on the filesystem"

    s3_resource = boto3.resource("s3")

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            match = re.search(r"^songs/(.+)", str(key["Key"]))
            if match:
                song = Song.objects.get(uuid=match.group(1))
                if song.album:
                    track_number = song.track
                    if len(str(song.track)) == 1:
                        track_number = f"0{song.track}"
                    if song.album.compilation:
                        path = f"/home/media/music/v/Various/{song.album.title}/{track_number} - {song.title}.mp3"
                    else:
                        path = f"/home/media/music/{song.artist.name.lower()[0]}/{song.artist}/{song.album.title}/{track_number} - {song.title}.mp3"
                else:
                    path = f"/home/media/music/{song.artist.name.lower()[0]}/{song.artist}/{song.title}.mp3"
                assert Path(path).is_file(), f"Song in S3 not found on filesystem: {song.uuid} {path}"

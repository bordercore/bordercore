import hashlib
from pathlib import Path

import factory
import pytest

from django import urls
from django.db.models import signals

pytestmark = pytest.mark.django_db


def test_music_list(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:list")
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_music_song_update(auto_login_user, song):

    _, client = auto_login_user()

    # The submitted form
    url = urls.reverse("music:song_update", kwargs={"song_id": song[1].id})
    resp = client.post(url, {
        "Go": "Update",
        "artist": "Artist Changed",
        "title": "Title Changed",
        "source": "1",
        "tags": ""
    })

    assert resp.status_code == 200

    url = urls.reverse("music:song_update", kwargs={"song_id": song[1].id})
    resp = client.post(url, {
        "Go": "Delete",
    })

    assert resp.status_code == 200


def test_music_album_detail(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:album_detail", kwargs={"pk": song[1].id})
    resp = client.get(url)

    assert resp.status_code == 200


def test_music_artist_detail(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:artist_detail", kwargs={"artist_name": song[1].artist})
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_music_create(s3_resource, s3_bucket, auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:create_song")

    mp3 = Path(__file__).parent / "resources/Mysterious Lights.mp3"

    with open(mp3, "rb") as fp:
        resp = client.post(url, {
            "song": fp,
            "upload": "Upload"
        })

    assert resp.status_code == 200

    hasher = hashlib.sha1()
    with open(mp3, "rb") as f:
        buf = f.read()
        hasher.update(buf)
        sha1sum = hasher.hexdigest()

    resp = client.post(url, {
        "sha1sum": sha1sum,
        "create": "Create",
        "artist": "Artist",
        "title": "Title",
        "album": "album_0",
        "original_release_year": "",
        "source": "1",
        "year": 2021,
        "tags": "synthwave"
    })

    assert resp.status_code == 200


def test_music_get_song_list(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:get_song_list")
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_music_get_song_info(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:get_song_info", kwargs={"id": song[1].id})
    resp = client.get(url)

    assert resp.status_code == 200


def test_music_search_tag(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:search_tag")
    resp = client.get(f"{url}?tag=sythnwave")

    assert resp.status_code == 200

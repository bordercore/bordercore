import hashlib
from pathlib import Path
from shutil import copy2

import factory
import pytest

from django import urls
from django.db.models import signals

pytestmark = [pytest.mark.django_db, pytest.mark.views]


def test_music_list(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:list")
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_music_song_update(auto_login_user, song, song_source):

    _, client = auto_login_user()

    # The submitted form
    url = urls.reverse("music:update", kwargs={"song_uuid": song[1].uuid})
    resp = client.post(url, {
        "Go": "Update",
        "artist": "Artist Changed",
        "title": "Title Changed",
        "source": song_source.id,
        "tags": "django"
    })

    assert resp.status_code == 302

    url = urls.reverse("music:update", kwargs={"song_uuid": song[1].uuid})
    resp = client.post(url, {
        "Go": "Delete",
        "tags": ""
    })

    assert resp.status_code == 200


def test_music_album_detail(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:album_detail", kwargs={"uuid": song[1].album.uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_music_artist_detail(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:artist_detail", kwargs={"artist": song[1].artist})
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_music_create(s3_resource, s3_bucket, auto_login_user, song, song_source):

    user, client = auto_login_user()

    # The empty form
    url = urls.reverse("music:create")
    resp = client.get(url)

    assert resp.status_code == 200

    # Adding a new song
    mp3 = Path(__file__).parent / "resources/Mysterious Lights.mp3"

    hasher = hashlib.sha1()
    with open(mp3, "rb") as f:
        buf = f.read()
        hasher.update(buf)
        sha1sum = hasher.hexdigest()

    # Mimic the file upload process by copying the song to /tmp
    #  for processing by the view
    copy2(mp3, f"/tmp/{user.userprofile.uuid}-{sha1sum}.mp3")

    url = urls.reverse("music:create")

    with open(mp3, "rb") as f:
        resp = client.post(url, {
            "song": mp3,
            "sha1sum": sha1sum,
            "artist": "Bryan Teoh",
            "title": "Mysterious Lights",
            "album_name": "FreePD Music",
            "original_release_year": "",
            "source": song_source.id,
            "year": 2020,
            "tags": "synthwave",
            "Go": "Create"
        })

    with open("/tmp/create-song-test-result.html", "wb") as foo:
        foo.write(resp.content)

    assert resp.status_code == 302


@factory.django.mute_signals(signals.pre_delete)
def test_music_delete(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:delete", kwargs={"uuid": song[0].uuid})
    resp = client.post(url)

    assert resp.status_code == 302


def test_music_recent_songs(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:recent_songs")
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_music_get_song_info(auto_login_user, song):

    _, client = auto_login_user()

    url = urls.reverse("music:get_song_info", kwargs={"uuid": song[1].uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_music_search_tag(auto_login_user, song, tag):

    _, client = auto_login_user()

    url = urls.reverse("music:search_tag")
    resp = client.get(f"{url}?tag={tag[0].name}")

    assert resp.status_code == 200


def test_music_playlist_detail(auto_login_user, playlist):

    _, client = auto_login_user()

    url = urls.reverse("music:playlist_detail", kwargs={"uuid": playlist[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_music_playlist_create(auto_login_user, song):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("music:playlist_create")
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("music:playlist_create")
    resp = client.post(url, {
        "name": "Test Playlist",
        "type": "manual",
        "tag": "django",
    })

    assert resp.status_code == 302


def test_music_playlist_delete(auto_login_user, playlist):

    _, client = auto_login_user()

    url = urls.reverse("music:delete_playlist", kwargs={"uuid": playlist[0].uuid})
    resp = client.post(url, {
        "Go": "Confirm"
    })

    assert resp.status_code == 302


def test_music_get_playlist(auto_login_user, playlist):

    _, client = auto_login_user()

    url = urls.reverse("music:get_playlist", kwargs={"uuid": playlist[0].uuid})
    resp = client.get(url)
    assert resp.status_code == 200

    url = urls.reverse("music:get_playlist", kwargs={"uuid": playlist[1].uuid})
    resp = client.get(url)
    assert resp.status_code == 200


def test_music_sort_playlist(auto_login_user, playlist):

    _, client = auto_login_user()

    url = urls.reverse("music:sort_playlist")
    resp = client.post(url, {
        "playlistitem_uuid": playlist[0].playlistitem_set.all()[0].uuid,
        "position": 2
    })

    assert resp.status_code == 200
    assert resp.json()["status"] == "OK"


def test_music_search_playlists(auto_login_user, playlist):

    _, client = auto_login_user()

    url = urls.reverse("music:search_playlists")
    resp = client.get(f"{url}?query=playlist")

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["uuid"] == str(playlist[0].uuid)


def test_music_add_to_playlist(auto_login_user, playlist, song):

    _, client = auto_login_user()

    url = urls.reverse("music:add_to_playlist")
    resp = client.post(url, {
        "playlist_uuid": playlist[0].uuid,
        "song_uuid": song[2].uuid
    })

    assert resp.status_code == 200
    assert resp.json()["status"] == "OK"

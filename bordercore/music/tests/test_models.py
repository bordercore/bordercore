from pathlib import Path

import pytest

from music.models import Album, Listen, Song, SongSource
from music.tests.factories import AlbumFactory, SongFactory

pytestmark = pytest.mark.django_db


def test_listen_to(auto_login_user, song):

    song[0].listen_to()

    assert song[0].times_played == 1
    assert Listen.objects.all().count() == 2
    assert Listen.objects.first().song == song[0]


def test_get_id3_info(auto_login_user, song):

    song_path = Path(__file__).parent / "resources/Mysterious Lights.mp3"

    with open(song_path, "rb") as f:
        song_file = f.read()

    song_info = Song.get_id3_info(song_file)

    # A song with an album
    assert song_info["artist"] == "Bryan Teoh"
    assert song_info["title"] == "Mysterious Lights"
    assert song_info["year"] == "2020"
    assert song_info["album_name"] == "FreePD Music"
    assert song_info["length"] == 178
    assert song_info["length_pretty"] == "2:58"


def test_music_playtime():

    album = AlbumFactory()
    SongFactory.create_batch(10, length=300, album=album)

    assert album.playtime == "50 minutes"


def test_music_song_url():

    # Test url for a song that's part of an album
    album = AlbumFactory()
    songs = SongFactory.create_batch(10, length=300, album=album)

    assert songs[0].url == f"/music/album/{album.uuid}/"

    # Test url for a song that's not part of an album
    song = SongFactory(album=None)

    assert song.url == f"/music/artist/{song.artist.uuid}/"


def test_music_scan_zipfile():

    album_zip = Path(__file__).parent / "resources/test-album.zip"
    in_file = open(album_zip, "rb")
    zipfile_obj = in_file.read()
    in_file.close()

    info = Album.scan_zipfile(zipfile_obj)
    songs = info["song_info"]

    assert info["album"] == "The Joshua Tree"
    assert info["artist"][0] == "U2"
    assert len(songs) == 2
    assert songs[0]["filesize"] == "7.6 kB"
    assert songs[0]["bit_rate"] == 15999
    assert songs[0]["sample_rate"] == 11025
    assert songs[0]["artist"] == "U2"
    assert songs[0]["title"] == "With or Without You"
    assert songs[0]["album_name"] == "The Joshua Tree"
    assert songs[0]["length"] == 3
    assert songs[0]["length_pretty"] == "0:03"
    assert songs[1]["filesize"] == "7.6 kB"
    assert songs[1]["bit_rate"] == 15999
    assert songs[1]["sample_rate"] == 11025
    assert songs[1]["artist"] == "U2"
    assert songs[1]["title"] == "Running to Stand Still"
    assert songs[1]["album_name"] == "The Joshua Tree"
    assert songs[1]["length"] == 3
    assert songs[1]["length_pretty"] == "0:03"


def test_create_album_from_zipfile(s3_resource, s3_bucket, auto_login_user, song_source):

    user, _ = auto_login_user()

    album_zip = Path(__file__).parent / "resources/test-album.zip"
    in_file = open(album_zip, "rb")
    zipfile_obj = in_file.read()
    in_file.close()

    song_source = SongSource.objects.get(name=SongSource.DEFAULT)
    artist_name = "U2"
    tags = "rock"

    album_uuid = Album.create_album_from_zipfile(
        zipfile_obj,
        artist_name,
        song_source,
        tags=tags,
        user=user,
        changes={}
    )

    album = Album.objects.get(uuid=album_uuid)
    assert album.compilation is False
    assert album.artist.name == "U2"
    assert album.title == "The Joshua Tree"
    assert album.year == 1987
    assert album.song_set.count() == 2
    song_1 = album.song_set.get(title="Running to Stand Still")
    song_2 = album.song_set.get(title="With or Without You")
    assert song_1.tags.first().name == "rock"
    assert song_1.artist.name == "U2"
    assert song_1.album == album
    assert song_1.track == 5
    assert song_1.year == 1987
    assert song_1.source == song_source
    assert song_1.length == 3
    assert song_2.tags.first().name == "rock"
    assert song_2.artist.name == "U2"
    assert song_2.album == album
    assert song_2.track == 3
    assert song_2.year == 1987
    assert song_2.source == song_source
    assert song_2.length == 3


def test_create_album_from_zipfile_with_changes(s3_resource, s3_bucket, auto_login_user, song_source):

    user, _ = auto_login_user()

    album_zip = Path(__file__).parent / "resources/test-album.zip"
    in_file = open(album_zip, "rb")
    zipfile_obj = in_file.read()
    in_file.close()

    song_source = SongSource.objects.get(name=SongSource.DEFAULT)
    artist_name = "U2"
    tags = "rock"

    album_uuid = Album.create_album_from_zipfile(
        zipfile_obj,
        artist_name,
        song_source,
        tags=tags,
        user=user,
        changes={
            "3": {"note": "Live version"},
            "5": {"title": "Running to Stand Still (feat ...)", "note": "Cover"},
        }
    )

    album = Album.objects.get(uuid=album_uuid)
    assert album.compilation is False
    assert album.artist.name == "U2"
    assert album.title == "The Joshua Tree"
    assert album.year == 1987
    assert album.song_set.count() == 2
    song_1 = album.song_set.get(title="Running to Stand Still (feat ...)")
    song_2 = album.song_set.get(title="With or Without You")
    assert song_1.tags.first().name == "rock"
    assert song_1.artist.name == "U2"
    assert song_1.title == "Running to Stand Still (feat ...)"
    assert song_1.album == album
    assert song_1.track == 5
    assert song_1.year == 1987
    assert song_1.source == song_source
    assert song_1.length == 3
    assert song_1.note == "Cover"
    assert song_2.tags.first().name == "rock"
    assert song_2.artist.name == "U2"
    assert song_2.title == "With or Without You"
    assert song_2.album == album
    assert song_2.track == 3
    assert song_2.year == 1987
    assert song_2.source == song_source
    assert song_2.length == 3
    assert song_2.note == "Live version"

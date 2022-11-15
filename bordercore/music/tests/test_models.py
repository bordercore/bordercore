from pathlib import Path
from unittest.mock import MagicMock

import pytest

from music.models import Song
from music.tests.factories import AlbumFactory, SongFactory

pytestmark = pytest.mark.django_db


def test_get_id3_info(auto_login_user, song):

    mock_request = MagicMock()
    mock_request.session = {}
    mock_request.session["song_source"] = "Amazon"

    song_path = Path(__file__).parent / "resources/Mysterious Lights.mp3"

    with open(song_path, "rb") as f:
        song_file = f.read()

    song_info = Song.get_id3_info(mock_request, {}, song_file)

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

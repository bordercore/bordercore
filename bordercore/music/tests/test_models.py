import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from music.models import Listen, Song

pytestmark = pytest.mark.django_db


def test_listen_to(auto_login_user, song):

    song[0].listen_to()

    assert song[0].times_played == 1
    assert Listen.objects.all().count() == 2
    assert Listen.objects.first().song == song[0]


def test_get_id3_info(auto_login_user, song):

    mock_request = MagicMock()
    mock_request.session = {}
    mock_request.session["song_source"] = "Amazon"

    song_path = Path(__file__).parent / "resources/Mysterious Lights.mp3"

    with open(song_path, "rb") as f:
        song_file = f.read()

    sha1sum = hashlib.sha1(song_file).hexdigest()

    song_info = Song.get_id3_info(mock_request, {}, song_file)

    # A song with an album
    assert song_info["sha1sum"] == sha1sum
    assert song_info["artist"] == "Bryan Teoh"
    assert song_info["title"] == "Mysterious Lights"
    assert song_info["year"] == "2020"
    assert song_info["album_name"] == "FreePD Music"
    assert song_info["length"] == 178
    assert song_info["length_pretty"] == "2:58"

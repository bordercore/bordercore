import pytest

import django

from lib.util import (get_missing_blob_ids, get_missing_bookmark_ids,
                      get_pagination_range, is_audio, is_image, is_pdf,
                      is_video, remove_non_ascii_characters, truncate)

django.setup()

from bookmark.models import Bookmark  # isort:skip
from blob.models import Blob  # isort:skip

pytestmark = pytest.mark.django_db


def test_get_missing_blob_ids(auto_login_user):

    user, _ = auto_login_user()

    found = {
        "hits": {
            "hits": [
                {
                    "_index": "bordercore",
                    "_type": "_doc",
                    "_id": "68568bae-5d53-41e2-ac64-3016e9c96fe1",
                    "_score": 1.0,
                    "_source": {
                    }
                },
                {
                    "_index": "bordercore",
                    "_type": "_doc",
                    "_id": "d77befd1-9172-4872-b527-628217f25d89",
                    "_score": 1.0,
                    "_source": {
                    }
                }
            ]
        }
    }

    expected = [
        Blob.objects.create(
            uuid="68568bae-5d53-41e2-ac64-3016e9c96fe1",
            user=user),
        Blob.objects.create(
            uuid="d77befd1-9172-4872-b527-628217f25d89",
            user=user)
    ]

    assert get_missing_blob_ids(expected, found) == ""

    found = {
        "hits": {
            "hits": [
                {
                    "_index": "bordercore",
                    "_type": "_doc",
                    "_id": "68568bae-5d53-41e2-ac64-3016e9c96fe1",
                    "_score": 1.0,
                    "_source": {
                    }
                },
                {
                    "_index": "bordercore",
                    "_type": "_doc",
                    "_id": "93870195-55a2-426e-970e-d67c63629329",
                    "_score": 1.0,
                    "_source": {
                    }
                }
            ]
        }
    }

    assert get_missing_blob_ids(expected, found) == "d77befd1-9172-4872-b527-628217f25d89"


def test_get_missing_bookmark_ids(auto_login_user):

    user, _ = auto_login_user()

    found = {
        "hits": {
            "hits": [
                {
                    "_index": "bordercore",
                    "_type": "_doc",
                    "_id": "3f40b11c-0b0e-4e11-aeb7-41c2bfee5d91",
                    "_score": 17.678326,
                    "_source": {
                        "uuid": "3f40b11c-0b0e-4e11-aeb7-41c2bfee5d91"
                    }
                },
                {
                    "_index": "bordercore",
                    "_type": "_doc",
                    "_id": "d2edec1c-493a-4d9c-877b-21900e848187bordercore_bookmark_69",
                    "_score": 17.32817,
                    "_source": {
                        "uuid": "d2edec1c-493a-4d9c-877b-21900e848187"
                    }
                }
            ]
        }
    }

    expected = [
        Bookmark.objects.create(
            uuid="3f40b11c-0b0e-4e11-aeb7-41c2bfee5d91",
            user=user),
        Bookmark.objects.create(
            uuid="d2edec1c-493a-4d9c-877b-21900e848187",
            user=user)
    ]

    assert get_missing_bookmark_ids(expected, found) == ""

    found = {
        "hits": {
            "hits": [
                {
                    "_index": "bordercore",
                    "_type": "_doc",
                    "_id": "3f40b11c-0b0e-4e11-aeb7-41c2bfee5d91",
                    "_score": 17.678326,
                    "_source": {
                        "uuid": "3f40b11c-0b0e-4e11-aeb7-41c2bfee5d91"
                    }
                },
                {
                    "_index": "bordercore",
                    "_type": "_doc",
                    "_id": "167873d9-28b6-49db-8d9b-d0ed6172f7de",
                    "_score": 17.32817,
                    "_source": {
                        "uuid": "167873d9-28b6-49db-8d9b-d0ed6172f7de"
                    }
                }
            ]
        }
    }

    assert get_missing_bookmark_ids(expected, found) == "d2edec1c-493a-4d9c-877b-21900e848187"


def test_truncate():

    string = "foobar"
    assert truncate(string) == "foobar"

    string = "foobar"
    assert truncate(string, 3) == "foo..."


def test_remove_non_ascii_characters():

    string = "foobar"
    assert remove_non_ascii_characters(string) == string

    string = "Níl Sén La"
    assert remove_non_ascii_characters(string) == "Nl Sn La"

    string = ""
    assert remove_non_ascii_characters(string) == "Default"


def test_util_is_image():

    file = "path/to/file.png"
    assert is_image(file) is True

    file = "path/to/file.gif"
    assert is_image(file) is True

    file = "path/to/file.jpg"
    assert is_image(file) is True

    file = "path/to/file.jpeg"
    assert is_image(file) is True

    file = "file.png"
    assert is_image(file) is True

    file = "path/to/file.pdf"
    assert is_image(file) is False


def test_util_is_pdf():

    file = "path/to/file.pdf"
    assert is_pdf(file) is True

    file = "path/to/file.gif"
    assert is_pdf(file) is False


def test_util_is_video():

    file = "path/to/file.mp4"
    assert is_video(file) is True

    file = "path/to/file.gif"
    assert is_video(file) is False


def test_util_is_audio():

    file = "path/to/file.mp3"
    assert is_audio(file) is True

    file = "path/to/file.gif"
    assert is_audio(file) is False


def test_get_pagination_range():

    x = get_pagination_range(1, 60, 2)
    assert x == [1, 2, 3, 4, 5]

    x = get_pagination_range(5, 60, 2)
    assert x == [3, 4, 5, 6, 7]

    x = get_pagination_range(60, 60, 2)
    assert x == [56, 57, 58, 59, 60]

    x = get_pagination_range(4, 4, 2)
    assert x == [1, 2, 3, 4]

    x = get_pagination_range(1, 4, 2)
    assert x == [1, 2, 3, 4]

    x = get_pagination_range(1, 3, 2)
    assert x == [1, 2, 3]

    x = get_pagination_range(3, 3, 2)
    assert x == [1, 2, 3]

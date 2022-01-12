import os
import urllib.request
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import urlparse

from faker import Factory as FakerFactory
from instaloader.instaloader import Instaloader

from blob.services import (get_authors, get_recent_blobs, import_artstation,
                           import_instagram, import_newyorktimes, parse_date,
                           parse_shortcode)

# from django.core.files.temp import NamedTemporaryFile


faker = FakerFactory.create()


def test_get_recent_blobs(auto_login_user, blob_image_factory, blob_text_factory):

    user, _ = auto_login_user()

    blob_list, doctypes = get_recent_blobs(user)

    assert doctypes["image"] == 1
    assert doctypes["document"] == 3
    assert doctypes["all"] == 10

    assert blob_image_factory[0].name in [
        x["name"]
        for x in
        blob_list
    ]

    assert blob_text_factory[0].name in [
        x["name"]
        for x in
        blob_list
    ]


class MockInstaloaderPostResponse:

    def __init__(self, url, shortcode):
        self.url = url
        self.shortcode = shortcode
        self.date_utc = None
        self.date = faker.date()
        self.caption = faker.text()
        self.owner_profile = Mock()
        self.owner_profile.full_name = faker.language_name()


def test_import_instagram(auto_login_user, monkeypatch):

    shortcode = "CUA4IQcARX2"
    url = f"https://www.instagram.com/p/{shortcode}/"

    def mock(*args, **kwargs):
        pass

    def mock_getmtime(*args, **kwargs):
        return faker.unix_time()

    user, _ = auto_login_user()

    mock_post = MockInstaloaderPostResponse(url=url, shortcode=shortcode)

    monkeypatch.setattr(Instaloader, "login", mock)
    monkeypatch.setattr(Instaloader, "download_pic", mock)
    monkeypatch.setattr(os, "rename", mock)
    monkeypatch.setattr(os.path, "getmtime", mock_getmtime)

    with MagicMock().patch("__builtin__.open") as my_mock, patch("instaloader.Post.from_shortcode") as mock_from_shortcode:
        mock_from_shortcode.return_value = mock_post
        my_mock.return_value.__enter__ = lambda s: s
        my_mock.return_value.__exit__ = Mock()
        my_mock.return_value.read.return_value = faker.text()
        blob = import_instagram(user, urlparse(url))

        assert blob.user == user
        assert blob.date == mock_post.date
        assert blob.name == mock_post.caption
        assert blob.metadata.filter(name="Url")[0].value == f"https://instagram.com/p/{shortcode}/"
        assert blob.metadata.filter(name="Artist")[0].value == mock_post.owner_profile.full_name


@patch("requests.get")
@patch("blob.services.get_sha1sum")
def test_import_artstation(mock_get_sha1sum, mock_requests, auto_login_user, monkeypatch):

    shortcode = "QnxsqB"
    url = f"https://www.artstation.com/artwork/{shortcode}/"

    def mock(*args, **kwargs):
        pass

    artstation_json = {
        "created_at": "2022-01-07T17:46:42.111-06:00",
        "assets": [
            {
                "image_url": "https://cdnb.artstation.com/p/assets/images/images/044/970/399/large/krystopher-decker-lara-final-da.jpg?1641599195"
            }
        ],
        "title": faker.text(),
        "permalink": faker.url(),
        "user": {
            "full_name": faker.language_name()
        }
    }

    user, _ = auto_login_user()

    mock_requests.return_value.json.return_value = artstation_json

    monkeypatch.setattr(urllib.request, "urlretrieve", mock)

    # TODO: mock NamedTemporaryFile() to prevent a temp file from being created
    # mock_temp_file = MockNamedTemporaryFile()
    # NamedTemporaryFile = mock_temp_file
    mock_get_sha1sum.return_value = faker.sha1()

    with MagicMock().patch("__builtin__.open") as my_mock:
        my_mock.return_value.__enter__ = lambda s: s
        my_mock.return_value.__exit__ = Mock()
        my_mock.return_value.read.return_value = faker.text()

        blob = import_artstation(user, urlparse(url))

        assert blob.user == user
        assert blob.date == "2022-01-07"
        assert blob.name == artstation_json["title"]
        assert blob.metadata.filter(name="Url")[0].value == artstation_json["permalink"]
        assert blob.metadata.filter(name="Artist")[0].value == artstation_json["user"]["full_name"]


def test_get_authors():

    first_name = faker.first_name()
    last_name = faker.last_name()

    assert get_authors([{"firstname": first_name, "lastname": last_name}]) == [f"{first_name} {last_name}"]


@patch("requests.get")
def test_import_newyorktimes(mock_requests, auto_login_user, monkeypatch):

    user, _ = auto_login_user()

    url = faker.url()
    title = faker.text()

    newyorktimes_json = {
        "status": "OK",
        "response": {
            "docs": [
                {
                    "headline": {
                        "main": title,
                    },
                    "abstract": faker.text(),
                    "web_url": url,
                    "pub_date": "2022-01-15T14:20:32+0000",
                    "byline": {
                        "person": [
                            {
                                "firstname": faker.first_name(),
                                "lastname": faker.last_name(),
                            }
                        ]
                    }
                }
            ]
        }
    }

    mock_requests.return_value.json.return_value = newyorktimes_json

    blob = import_newyorktimes(user, url)

    assert blob.user == user
    assert blob.date == "2022-01-15"
    assert blob.name == title
    assert blob.metadata.filter(name="Url")[0].value == newyorktimes_json["response"]["docs"][0]["web_url"]
    assert blob.metadata.filter(name="Author")[0].value == newyorktimes_json["response"]["docs"][0]["byline"]["person"][0]["firstname"] \
        + " " + newyorktimes_json["response"]["docs"][0]["byline"]["person"][0]["lastname"]


def test_parse_shortcode():

    assert parse_shortcode("https://www.instagram.com/p/CUA4IQcARX2/") == "CUA4IQcARX2"

    assert parse_shortcode("https://www.instagram.com/tv/CWbejF6DD9B/") == "CWbejF6DD9B"

    assert parse_shortcode("https://www.instagram.com/p/CWixXZTLWgf/?utm_source=ig_web_copy_link") == "CWixXZTLWgf"

    assert parse_shortcode("https://www.artstation.com/artwork/0XQTnK") == "0XQTnK"

    try:
        parse_shortcode("https://www.instagram.com/42/")
    except Exception:
        pass
    else:
        assert False, "Bogus shortcode should raise exception"


def test_parse_date():

    assert parse_date("2021-08-15 23:40:56") == "2021-08-15"
    assert parse_date("2021-11-15T15:56:23.875-06:00") == "2021-11-15"
    assert parse_date("January 1, 2022") == "January 1, 2022"

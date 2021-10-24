import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import django
from django import urls
from django.test import RequestFactory

from search.views import (SearchTagDetailView, get_doc_types_from_request,
                          get_doctype, get_name, is_cached, sort_results)

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    pass

pytestmark = [pytest.mark.django_db, pytest.mark.views]

django.setup()


def test_get_doc_types_from_request():

    request_mock = Mock()

    request_mock.GET = {}
    assert get_doc_types_from_request(request_mock) == []

    request_mock.GET = {"doc_type": ""}
    assert get_doc_types_from_request(request_mock) == []

    request_mock.GET = {"doc_type": "music"}
    assert get_doc_types_from_request(request_mock) == ["album", "song"]

    request_mock.GET = {"doc_type": "book"}
    assert get_doc_types_from_request(request_mock) == ["book"]

    request_mock.GET = {"doc_type": "blob,book,document"}
    assert get_doc_types_from_request(request_mock) == ["blob", "book", "document"]


@patch("search.views.Elasticsearch")
def test_search_notes(mock_elasticsearch, auto_login_user):

    _, client = auto_login_user()

    filepath = Path(__file__).parent / "resources/search_results_notes.json"

    with open(filepath) as f:
        data = json.load(f)

    instance = mock_elasticsearch.return_value
    instance.search.return_value = data

    url = urls.reverse("search:notes")
    resp = client.get(f"{url}?search=linux")

    assert resp.status_code == 200

    # soup = BeautifulSoup(resp.content, "html.parser")

    # match = soup.select("div#vue-app card")[0]["title"]
    # assert data["hits"]["hits"][0]["source"]["name"] == match

    # matches = soup.select("div#note:nth-of-type(0) a#tag")
    # for tag in matches:
    #     assert tag.findAll(text=True)[0] in data["hits"]["hits"][0]["source"]["tags"]


def test_sort_results():

    matches = [
        {
            "doctype": "Bookmark",
            "value": "http://python.org"
        },
        {
            "doctype": "Tag",
            "value": "python"
        },
        {
            "doctype": "Note",
            "value": "Running Emacs Inside Docker"
        },
    ]

    response = sort_results(matches)

    assert response[0]["splitter"] is True
    assert response[1]["value"] == "python"
    assert response[1]["doctype"] == "Tag"
    assert response[2]["splitter"] is True
    assert response[3]["doctype"] == "Note"
    assert response[3]["value"] == "Running Emacs Inside Docker"
    assert response[4]["splitter"] is True
    assert response[5]["doctype"] == "Bookmark"
    assert response[5]["value"] == "http://python.org"
    assert len(response) == 6


def test_get_name():

    assert get_name("Song", {"artist": "U2", "title": "Running to Stand Still"}) == "Running to Stand Still - U2"
    assert get_name("Album", {"artist": "U2", "title": "The Joshua Tree"}) == "The Joshua Tree"
    assert get_name("Artist", {"artist": "U2"}) == "U2"
    assert get_name("Book", {"name": "War and Peace"}) == "War And Peace"
    assert get_name("Book", {"name": "war and peace"}) == "War And Peace"


def test_get_doctype():

    assert get_doctype({"_source": {"doctype": "song"}}) == "Song"
    assert get_doctype({"_source": {"doctype": "song"}, "highlight": {"album": ""}}) == "Album"
    assert get_doctype({"_source": {"doctype": "song"}, "highlight": {"artist": ""}}) == "Artist"
    assert get_doctype({"_source": {"doctype": "song"}, "highlight": {"artist": "", "album": ""}}) == "Artist"


def test_is_cached():

    cache_checker = is_cached()

    assert cache_checker("Artist", "U2") is False
    assert cache_checker("Artist", "U2") is True
    assert cache_checker("Album", "The Joshau Tree") is False
    assert cache_checker("Book", "War and Peace") is False


@patch("search.views.Elasticsearch")
def test_search_tag(mock_elasticsearch, auto_login_user, blob_image_factory, blob_pdf_factory):

    _, client = auto_login_user()

    filepath = Path(__file__).parent / "resources/search_results_tags.json"

    with open(filepath) as f:
        data = json.load(f)

    instance = mock_elasticsearch.return_value
    instance.search.return_value = data

    url = urls.reverse("search:kb_search_tag_detail", kwargs={"taglist": "carl sagan"})
    resp = client.get(url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    matches = soup.select("#document li")
    assert len(matches) == 3

    matches = soup.select("#blob li")
    assert len(matches) == 2


def test_get_doc_counts():

    request = RequestFactory().get("/")
    view = SearchTagDetailView()
    view.setup(request)

    aggregations = {
        "buckets": [
            {
                "key": "document",
                "doc_count": 3
            },
            {
                "key": "blob",
                "doc_count": 2
            }
        ]
    }

    result = view.get_doc_counts([], aggregations)
    assert len(result) == 2
    assert result[0] == ("document", 3)
    assert result[1] == ("blob", 2)


def test_tag_list_js(auto_login_user):

    user, _ = auto_login_user()

    request = RequestFactory().get("/")
    request.user = user
    view = SearchTagDetailView()
    view.setup(request)

    results = view.get_tag_list_js(["django", "video"])

    assert len(results) == 2
    assert results[0]["text"] == "django"
    assert results[0]["is_meta"] == "false"
    assert results[1]["text"] == "video"
    assert results[1]["is_meta"] == "false"

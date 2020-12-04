import json
from pathlib import Path
from unittest.mock import patch

import pytest

import django
from django import urls

from search.views import get_title, is_cached

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    pass


django.setup()

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip
from blob.models import Blob  # isort:skip


@pytest.fixture(scope="function")
def user(db, client, django_user_model):
    username = "testuser"
    password = "password"
    email = "testuser@testdomain.com"

    user = django_user_model.objects.create_user(username, email, password)
    client.login(username=username, password=password)

    return user


@pytest.mark.django_db
@patch("search.views.Elasticsearch")
def test_search(mock_elasticsearch, user, client):

    filepath = Path(__file__).parent / "resources/search_results.json"

    with open(filepath) as f:
        data = json.load(f)

    instance = mock_elasticsearch.return_value
    instance.search.return_value = data

    url = urls.reverse("search:search")
    resp = client.get(f"{url}?search=carl+sagan")

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    matches = soup.select("h4.search_book_title")
    assert len(matches) == 14

    matches = soup.select("span.search_book_title")
    assert len(matches) == 5

    match = soup.select("h4.search_book_title a")[0].text
    assert data["hits"]["hits"][0]["source"]["title"] == match


@pytest.mark.django_db
@patch("search.views.Elasticsearch")
def test_search_notes(mock_elasticsearch, user, client):

    filepath = Path(__file__).parent / "resources/search_results_notes.json"

    with open(filepath) as f:
        data = json.load(f)

    instance = mock_elasticsearch.return_value
    instance.search.return_value = data

    url = urls.reverse("search:notes")
    resp = client.get(f"{url}?search=linux")

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    matches = soup.select("div#note")
    assert len(matches) == 10

    match = soup.select("div#note h2")[0].text.strip()
    assert data["hits"]["hits"][0]["source"]["title"] == match

    matches = soup.select("div#note:nth-child(1) a#tag")
    for tag in matches:
        assert tag.text in data["hits"]["hits"][0]["source"]["tags"]


def test_is_cached():

    cache_checker = is_cached()

    assert cache_checker("Artist", "U2") is False
    assert cache_checker("Artist", "U2") is True
    assert cache_checker("Album", "The Joshau Tree") is False
    assert cache_checker("Book", "War and Peace") is False

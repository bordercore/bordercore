from urllib.parse import urlparse

import factory
import pytest
from elasticsearch import Elasticsearch

from django import urls
from django.db.models import signals

from blob.models import Blob

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    pass

pytestmark = pytest.mark.django_db


@pytest.fixture
def monkeypatch_blob(monkeypatch):
    """
    Prevent the blob object from interacting with Elasticsearch by
    patching out various methods.
    """

    def mock(*args, **kwargs):
        pass

    monkeypatch.setattr(Elasticsearch, "delete", mock)
    monkeypatch.setattr(Blob, "get_elasticsearch_info", mock)
    monkeypatch.setattr(Blob, "index_blob", mock)


@factory.django.mute_signals(signals.post_save)
def test_blob_create(monkeypatch_blob, auto_login_user):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("blob:create")
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("blob:create")
    resp = client.post(url, {
        "tags": "django",
        "importance": 1,
    })

    assert resp.status_code == 302


@factory.django.mute_signals(signals.pre_delete)
def test_blob_delete(monkeypatch_blob, auto_login_user, blob_text_factory):

    _, client = auto_login_user()

    url = urls.reverse("blob:delete", kwargs={"uuid": blob_text_factory.uuid})
    resp = client.post(url)

    assert resp.status_code == 302


@factory.django.mute_signals(signals.post_save)
def test_blob_update(monkeypatch_blob, auto_login_user, blob_text_factory):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("blob:update", kwargs={"uuid": blob_text_factory.uuid})
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("blob:update", kwargs={"uuid": blob_text_factory.uuid})
    resp = client.post(url, {
        "name": "Name Changed",
        "note": "Note Changed",
        "importance": 1,
        "tags": "django"
    })

    assert resp.status_code == 302


@pytest.mark.parametrize("blob", [pytest.lazy_fixture("blob_image_factory"), pytest.lazy_fixture("blob_text_factory")])
def test_blob_detail(monkeypatch_blob, auto_login_user, blob):
    """Verify we redirect to the memes page when a user is logged in"""

    _, client = auto_login_user()

    url = urls.reverse("blob:detail", args=(blob.uuid,))
    resp = client.get(url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    assert soup.select("div#vue-app h2#name")[0].findAll(text=True)[0].strip() == blob.get_name(remove_edition_string=True)

    url = [x.value for x in blob.metadata_set.all() if x.name == "Url"][0]
    assert soup.select("strong a")[0].findAll(text=True)[0] == urlparse(url).netloc

    author = [x.value for x in blob.metadata_set.all() if x.name == "Author"][0]
    assert soup.select("span#author")[0].findAll(text=True)[0] == author

    assert soup.select("span.metadata_value")[0].findAll(text=True)[0] == "John Smith, Jane Doe"


def test_blob_metadata_name_search(auto_login_user, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("blob:metadata_name_search")
    resp = client.get(f"{url}?query=foobar")

    assert resp.status_code == 200


def test_blob_collection_mutate(auto_login_user, blob_text_factory, collection):

    _, client = auto_login_user()

    url = urls.reverse("blob:collection_mutate")

    resp = client.post(url, {
        "blob_id": blob_text_factory.id,
        "collection_id": collection.id,
        "mutation": "add"
    })

    assert resp.status_code == 200

    resp = client.post(url, {
        "blob_id": blob_text_factory.id,
        "collection_id": collection.id,
        "mutation": "delete"
    })

    assert resp.status_code == 200


def test_blob_parse_date(auto_login_user):

    _, client = auto_login_user()

    url = urls.reverse("blob:parse_date", kwargs={"input_date": "2021-01-01"})
    resp = client.get(url)

    assert resp.status_code == 200

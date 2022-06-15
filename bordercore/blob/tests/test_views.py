import time
from unittest.mock import Mock
from urllib.parse import urlparse

import factory
import pytest
from faker import Factory as FakerFactory

from django import urls
from django.db.models import signals

from blob.models import Blob
from blob.tests.factories import BlobFactory
from blob.views import (get_metadata_from_form, handle_linked_collection,
                        handle_metadata)
from collection.models import Collection
from collection.tests.factories import CollectionFactory

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    pass

pytestmark = [pytest.mark.django_db, pytest.mark.views]

faker = FakerFactory.create()


@pytest.fixture
def monkeypatch_collection(monkeypatch):
    """
    Prevent the collection object from interacting with AWS by
    patching out a method.
    """

    def mock(*args, **kwargs):
        pass

    monkeypatch.setattr(Collection, "create_collection_thumbnail", mock)


def test_blob_list(auto_login_user, blob_text_factory):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("blob:list")
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_blob_create(monkeypatch_blob, auto_login_user, blob_text_factory):

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

    # A blob linked to an existing blob -- empty form
    url = urls.reverse("blob:create")
    resp = client.get(url, {
        "tags": "django",
        "importance": 1,
        "linked_blob_uuid": blob_text_factory[0].uuid
    })

    assert resp.status_code == 200

    # A blob linked to an existing blob -- submitted form
    url = urls.reverse("blob:create")
    resp = client.post(url, {
        "tags": "django",
        "importance": 1,
        "linked_blob_uuid": blob_text_factory[0].uuid
    })

    assert resp.status_code == 302

    new_blob = Blob.objects.all().order_by("-created")[0]
    assert new_blob.blobs.first().uuid == blob_text_factory[0].uuid


@factory.django.mute_signals(signals.pre_delete)
def test_blob_delete(monkeypatch_blob, auto_login_user, blob_text_factory):

    _, client = auto_login_user()

    url = urls.reverse("blob:delete", kwargs={"uuid": blob_text_factory[0].uuid})
    resp = client.post(url)

    assert resp.status_code == 302


@factory.django.mute_signals(signals.post_save)
def test_blob_update(monkeypatch_blob, auto_login_user, blob_text_factory):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("blob:update", kwargs={"uuid": blob_text_factory[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("blob:update", kwargs={"uuid": blob_text_factory[0].uuid})
    resp = client.post(url, {
        "name": "Name Changed",
        "note": "Note Changed",
        "importance": 1,
        "tags": "django"
    })

    assert resp.status_code == 302


@pytest.mark.parametrize("blob", [pytest.lazy_fixture("blob_image_factory"), pytest.lazy_fixture("blob_text_factory")])
def test_blob_detail(auto_login_user, blob):

    _, client = auto_login_user()

    url = urls.reverse("blob:detail", args=(blob[0].uuid,))
    resp = client.get(url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    assert soup.select("div#vue-right-panel #blob-name")[0].findAll(text=True)[0].strip() == blob[0].get_name(remove_edition_string=True)

    url = [x.value for x in blob[0].metadata.all() if x.name == "Url"][0]
    assert soup.select("strong a")[0].findAll(text=True)[0] == urlparse(url).netloc

    author = [x.value for x in blob[0].metadata.all() if x.name == "Author"][0]
    assert author in [x for sublist in soup.select("span") for x in sublist]


def test_clone(monkeypatch_blob, auto_login_user):

    user, client = auto_login_user()

    blob = BlobFactory.create(user=user)

    url = urls.reverse("blob:clone", kwargs={"uuid": str(blob.uuid)})
    resp = client.get(url)

    assert resp.status_code == 302


def test_handle_metadata(auto_login_user, blob_text_factory, blob_image_factory):

    user, client = auto_login_user()

    request_mock = Mock()
    request_mock.user = user
    fake_name = faker.name()
    fake_url = faker.url()

    request_mock.POST = {
        "1_Artist": fake_name,
        "2_Url": fake_url
    }

    handle_metadata(blob_text_factory[0], request_mock)

    metadata = blob_text_factory[0].metadata.all()
    assert len(metadata) == 2
    assert "Artist" in [x.name for x in metadata]
    assert fake_name in [x.value for x in metadata]
    assert "Url" in [x.name for x in metadata]
    assert fake_url in [x.value for x in metadata]

    request_mock.POST = {
        "1_Author": fake_name,
        "is_book": "true"
    }

    handle_metadata(blob_image_factory[0], request_mock)

    metadata = blob_image_factory[0].metadata.all()
    assert len(metadata) == 2
    assert "Author" in [x.name for x in metadata]
    assert fake_name in [x.value for x in metadata]
    assert "is_book" in [x.name for x in metadata]


def test_get_metadata_from_form(auto_login_user):

    request_mock = Mock()
    fake_name = faker.name()
    fake_url = faker.url()

    request_mock.POST = {
        "1_Author": fake_name,
        "2_Url": fake_url
    }

    metadata = get_metadata_from_form(request_mock)

    assert len(metadata) == 2
    assert "Author" in [x["name"] for x in metadata]
    assert fake_name in [x["value"] for x in metadata]
    assert "Url" in [x["name"] for x in metadata]
    assert fake_url in [x["value"] for x in metadata]

    request_mock.POST = {
        "1_Author": "",
    }

    metadata = get_metadata_from_form(request_mock)

    assert len(metadata) == 0


def test_handle_linked_collection(monkeypatch_collection, auto_login_user, blob_image_factory):

    user, client = auto_login_user()

    collection = CollectionFactory(user=user)

    request_mock = Mock()
    request_mock.user = user
    request_mock.POST = {
        "linked_collection": collection.uuid
    }

    handle_linked_collection(blob_image_factory[0], request_mock)

    collection_updated = Collection.objects.get(uuid=collection.uuid)

    assert blob_image_factory[0] in [x.blob for x in collection_updated.collectionobject_set.all()]


def test_blob_metadata_name_search(auto_login_user, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("blob:metadata_name_search")
    resp = client.get(f"{url}?query=foobar")

    assert resp.status_code == 200


def test_blob_parse_date(auto_login_user):

    _, client = auto_login_user()

    url = urls.reverse("blob:parse_date", kwargs={"input_date": "2021-01-01"})
    resp = client.get(url)
    assert resp.json() == {'output_date': '2021-01-01T00:00', 'error': None}
    assert resp.status_code == 200

    # Test a bogus date
    url = urls.reverse("blob:parse_date", kwargs={"input_date": "2021-01-34"})
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.json() == {'output_date': '', 'error': "time data '01/34/2021' does not match format '%m/%d/%Y'"}


def test_get_elasticsearch_info(auto_login_user):

    user, client = auto_login_user()

    blob = BlobFactory.create(user=user, tags=("django", "linux"),)

    url = urls.reverse("blob:get_elasticsearch_info", kwargs={"uuid": blob.uuid})
    resp = client.get(url)

    assert resp.status_code == 200
    assert resp.json() == {"info": {}, "status": "OK"}

    BlobFactory.index_blob(blob)

    # Pause to allow time for the blob to be indexed
    time.sleep(1)

    url = urls.reverse("blob:get_elasticsearch_info", kwargs={"uuid": blob.uuid})
    resp_json = client.get(url).json()

    assert resp.status_code == 200
    assert resp_json["status"] == "OK"
    assert resp_json["info"]["id"] == str(blob.uuid)
    assert resp_json["info"]["name"] == blob.name
    assert resp_json["info"]["filename"] == ""
    assert resp_json["info"]["note"] == blob.note
    assert resp_json["info"]["doctype"] == "document"


def test_get_related_blobs(auto_login_user):

    user, client = auto_login_user()

    blob_1 = BlobFactory.create(user=user)
    blob_2 = BlobFactory.create(user=user)

    blob_1.blobs.add(blob_2)

    url = urls.reverse("blob:related_blobs", kwargs={"uuid": str(blob_1.uuid)})
    resp = client.get(url)

    assert resp.status_code == 200

    payload = resp.json()
    assert payload["status"] == "OK"
    assert len(payload["blob_list"]) == 1
    assert payload["blob_list"][0]["uuid"] == str(blob_2.uuid)


def test_blob_link(auto_login_user):

    user, client = auto_login_user()

    blob_1 = BlobFactory.create(user=user)
    blob_2 = BlobFactory.create(user=user)

    url = urls.reverse("blob:link")
    resp = client.post(url, {
        "blob_1_uuid": blob_1.uuid,
        "blob_2_uuid": blob_2.uuid,
    })

    assert resp.status_code == 200

    linked_blob = Blob.objects.get(uuid=blob_1.uuid)
    assert linked_blob.blobs.count() == 1
    assert linked_blob.blobs.first() == blob_2


def test_blob_unlink(auto_login_user):

    user, client = auto_login_user()

    blob_1 = BlobFactory.create(user=user)
    blob_2 = BlobFactory.create(user=user)

    blob_1.blobs.add(blob_2)

    url = urls.reverse("blob:unlink")
    resp = client.post(url, {
        "blob_1_uuid": blob_1.uuid,
        "blob_2_uuid": blob_2.uuid,
    })

    assert resp.status_code == 200

    linked_blob = Blob.objects.get(uuid=blob_1.uuid)
    assert linked_blob.blobs.count() == 0

import pytest

from django import urls

from collection.models import SortOrderCollectionBlob

pytestmark = [pytest.mark.django_db, pytest.mark.views]


def test_collection_list(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_collection_detail(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:detail", kwargs={"collection_uuid": collection[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200

    for blob in SortOrderCollectionBlob.objects.filter(collection=collection[0]):
        blob.delete()

    url = urls.reverse("collection:detail", kwargs={"collection_uuid": collection[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_sort_collection(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:sort")
    resp = client.post(url, {
        "collection_uuid": collection[0].uuid,
        "blob_uuid": collection[0].blobs.all()[0].uuid,
        "position": "3"
    })

    assert resp.status_code == 200


def test_get_blob(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:get_blob", kwargs={
        "collection_uuid": collection[0].uuid,
        "blob_position": 1,
    })
    resp = client.get(url)

    assert resp.status_code == 200


def test_create_collection(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:create")
    resp = client.post(url, {
        "name": "Collection name",
        "description": "Collection description",
        "tags": "django"
    })

    assert resp.status_code == 302


def test_update_collection(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:update", kwargs={"collection_uuid": collection[0].uuid})
    resp = client.post(url, {
        "name": "New name",
        "tags": "django"
    })

    assert resp.status_code == 302


def test_delete_collection(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection-detail", kwargs={"uuid": collection[0].uuid})
    resp = client.delete(url)

    assert resp.status_code == 204


def test_search(auto_login_user, collection, blob_image_factory, blob_pdf_factory):

    _, client = auto_login_user()

    url = urls.reverse("collection:search")
    resp = client.get(f"{url}?query=Display")

    assert resp.status_code == 200

    payload = resp.json()

    assert len(payload) == 1

    assert payload[0]["name"] == collection[1].name
    assert payload[0]["num_blobs"] == 1


def test_collection_blob_list(auto_login_user, collection, blob_image_factory, blob_pdf_factory):

    _, client = auto_login_user()

    url = urls.reverse("collection:get_blob_list", kwargs={"collection_uuid": collection[0].uuid})
    resp = client.get(f"{url}?query=Display")

    assert resp.status_code == 200

    payload = resp.json()

    assert len(payload) == 2

    assert blob_image_factory[0].name in [x["name"] for x in payload["blob_list"]]
    assert blob_pdf_factory[0].name in [x["name"] for x in payload["blob_list"]]

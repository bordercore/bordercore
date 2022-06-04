import pytest

from django import urls

from blob.tests.factories import BlobFactory
from collection.models import SortOrderCollectionBCObject

pytestmark = [pytest.mark.django_db, pytest.mark.views]


def test_collection_list(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_collection_detail(auto_login_user, collection):

    user, client = auto_login_user()

    url = urls.reverse("collection:detail", kwargs={"collection_uuid": collection[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200

    for so in SortOrderCollectionBCObject.objects.filter(collection=collection[0]):
        so.blob.delete()

    url = urls.reverse("collection:detail", kwargs={"collection_uuid": collection[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200

    # Test collections with blobs with no "null" names
    blob = BlobFactory(user=user, name=None)
    collection[0].add_object(blob)

    url = urls.reverse("collection:detail", kwargs={"collection_uuid": collection[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_sort_collection(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:sort_objects")
    resp = client.post(url, {
        "collection_uuid": collection[0].uuid,
        "object_uuid": collection[0].sortordercollectionbcobject_set.all()[0].blob.uuid,
        "new_position": "3"
    })

    assert resp.status_code == 200


def test_get_blob(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:get_blob", kwargs={
        "collection_uuid": collection[0].uuid
    })
    resp = client.get(f"{url}?position=1")

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


def test_collection_get_blob_list(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:get_blob_list", kwargs={
        "collection_uuid": collection[0].uuid
    })
    resp = client.get(url)

    assert resp.status_code == 200

    resp_json = resp.json()

    assert len(resp_json["blob_list"]) == 2

    blob_list = collection[0].sortordercollectionbcobject_set.all()
    assert str(blob_list[0].blob.uuid) in [
        x["uuid"] for x in resp_json["blob_list"]
    ]
    assert str(blob_list[1].blob.uuid) in [
        x["uuid"] for x in resp_json["blob_list"]
    ]


def test_add_blob(auto_login_user, collection, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("collection:add_blob")
    resp = client.post(url, {
        "collection_uuid": collection[0].uuid,
        "blob_uuid": blob_image_factory[0].uuid
    })

    assert resp.status_code == 200

    # Test for adding a duplicate blob
    resp = client.post(url, {
        "collection_uuid": collection[0].uuid,
        "blob_uuid": blob_image_factory[0].uuid
    })
    assert resp.json()["status"] == "Error"


def test_remove_object(auto_login_user, collection, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("collection:remove_object")
    resp = client.post(url, {
        "collection_uuid": collection[0].uuid,
        "object_uuid": blob_image_factory[0].uuid
    })

    assert resp.status_code == 200

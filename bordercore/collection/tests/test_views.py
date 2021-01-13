import pytest

from django import urls

pytestmark = pytest.mark.django_db


def test_collection_list(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_collection_detail(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:detail", kwargs={"collection_id": collection.id})
    resp = client.get(url)

    assert resp.status_code == 200

    # Test a collection with no objects
    collection.blob_list = None
    collection.save()
    url = urls.reverse("collection:detail", kwargs={"collection_id": collection.id})
    resp = client.get(url)

    assert resp.status_code == 200


def test_collection_get_info(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:get_info")
    resp = client.get(f"{url}?query_type=id&id={collection.id}")

    assert resp.status_code == 200

    url = urls.reverse("collection:get_info")
    resp = client.get(f"{url}?query_type=name&name={collection.name}")

    assert resp.status_code == 200

    # Test for an object that doesn't exist
    url = urls.reverse("collection:get_info")
    resp = client.get(f"{url}?query_type=id&id=666")

    assert resp.status_code == 200


def test_sort_collection(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:sort")
    resp = client.post(url, {
        "collection_id": collection.id,
        "blob_id": collection.blob_list[0]["id"],
        "position": "3"
    })

    assert resp.status_code == 200


def test_get_blob(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:get_blob", kwargs={
        "collection_id": collection.id,
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

    url = urls.reverse("collection:update", kwargs={"pk": collection.id})
    resp = client.post(url, {
        "collection_id": collection.id,
        "name": "New name",
        "tags": "django"
    })

    assert resp.status_code == 302


def test_delete_collection(auto_login_user, collection):

    _, client = auto_login_user()

    url = urls.reverse("collection:delete", kwargs={"pk": collection.id})
    resp = client.post(url, {"collection_id": collection.id})

    assert resp.status_code == 302

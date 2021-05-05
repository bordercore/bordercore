import pytest

from django import urls

from node.models import SortOrderNodeBlob, SortOrderNodeBookmark

pytestmark = pytest.mark.django_db


def test_node_overview(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_node_detail(auto_login_user, node, blob_image_factory, blob_pdf_factory):

    _, client = auto_login_user()

    url = urls.reverse("node:detail", kwargs={"uuid": node.uuid})
    resp = client.get(url)

    assert resp.status_code == 200

    # Test a node with no objects
    s = SortOrderNodeBlob.objects.get(node__uuid=node.uuid, blob__uuid=blob_image_factory.uuid)
    s.delete()
    s = SortOrderNodeBlob.objects.get(node__uuid=node.uuid, blob__uuid=blob_pdf_factory.uuid)
    s.delete()
    url = urls.reverse("node:detail", kwargs={"uuid": node.uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_get_blob_list(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:get_blob_list", kwargs={"uuid": node.uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_sort_blobs(auto_login_user, node, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("node:sort_blobs")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "blob_uuid": blob_image_factory.uuid,
        "new_position": "2"
    })

    assert resp.status_code == 200


def test_add_blob(auto_login_user, node, blob_image_factory):

    _, client = auto_login_user()

    # First delete the blob, then add it back via the view
    s = SortOrderNodeBlob.objects.get(node__uuid=node.uuid, blob__uuid=blob_image_factory.uuid)
    s.delete()

    url = urls.reverse("node:add_blob")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "blob_uuid": blob_image_factory.uuid
    })

    assert resp.status_code == 200


def test_remove_blob(auto_login_user, node, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("node:remove_blob")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "blob_uuid": blob_image_factory.uuid
    })

    assert resp.status_code == 200


def test_edit_blob_note(auto_login_user, node, blob_image_factory):

    _, client = auto_login_user()

    url = urls.reverse("node:edit_blob_note")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "blob_uuid": blob_image_factory.uuid,
        "note": "Sample Note"
    })

    assert resp.status_code == 200


def test_get_bookmark_list(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:get_bookmark_list", kwargs={"uuid": node.uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_sort_bookmarks(auto_login_user, node, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("node:sort_bookmarks")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "bookmark_id": bookmark[0].id,
        "new_position": "2"
    })

    assert resp.status_code == 200


def test_add_bookmark(auto_login_user, node, bookmark):

    _, client = auto_login_user()

    # First delete the bookmark, then add it back via the view
    s = SortOrderNodeBookmark.objects.get(node__uuid=node.uuid, bookmark__id=bookmark[0].id)
    s.delete()

    url = urls.reverse("node:add_bookmark")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "bookmark_id": bookmark[0].id
    })

    assert resp.status_code == 200


def test_remove_bookmark(auto_login_user, node, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("node:remove_bookmark")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "bookmark_id": bookmark[0].id
    })

    assert resp.status_code == 200


def test_edit_bookmark_note(auto_login_user, node, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("node:edit_bookmark_note")
    resp = client.post(url, {
        "node_uuid": node.uuid,
        "bookmark_id": bookmark[0].id,
        "note": "Sample Note"
    })

    assert resp.status_code == 200


def test_search_bookmarks(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:search_bookmarks")
    resp = client.get(f"{url}?term=Bookmark")

    assert resp.status_code == 200


def test_search_blob_names(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:search_blob_names")
    resp = client.get(f"{url}?term=Bookmark")

    assert resp.status_code == 200


def test_get_note(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:get_note", kwargs={"uuid": node.uuid})
    resp = client.get(url)

    assert resp.status_code == 200


def test_edit_note(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("node:edit_note")
    resp = client.post(url, {
        "uuid": node.uuid,
        "note": "Sample Changed Note"
    })

    assert resp.status_code == 200

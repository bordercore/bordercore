import datetime
import json

import pytest
from faker import Factory as FakerFactory

from django import urls

from blob.models import SortOrderBlobBookmark
from blob.tests.factories import BlobFactory
from bookmark.models import Bookmark
from bookmark.tests.factories import BookmarkFactory
from tag.tests.factories import TagFactory

pytestmark = [pytest.mark.django_db, pytest.mark.views]

faker = FakerFactory.create()


def test_bookmark_click(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:click", kwargs={"bookmark_uuid": bookmark[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 302


def test_bookmark_update(monkeypatch_bookmark, auto_login_user, bookmark):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("bookmark:update", kwargs={"uuid": bookmark[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("bookmark:update", kwargs={"uuid": bookmark[0].uuid})
    resp = client.post(url, {
        "url": "https://www.bordercore.com/bookmark/",
        "name": "Sample Title Changed",
        "tags": "linux",
        "importance": "1"
    })

    updated_bookmark = Bookmark.objects.get(uuid=bookmark[0].uuid)
    assert updated_bookmark.name == "Sample Title Changed"
    assert resp.status_code == 302


def test_bookmark_create(monkeypatch_bookmark, auto_login_user, bookmark):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("bookmark:create")
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("bookmark:create")

    resp = client.post(url, {
        "url": "https://www.bordercore.com/foo",
        "name": "Sample Title",
        "tags": "django",
        "importance": "1"
    })

    assert resp.status_code == 302


def test_bookmark_delete(monkeypatch_bookmark, auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:delete", kwargs={"uuid": bookmark[0].uuid})
    resp = client.post(url)

    assert resp.status_code == 302


def test_bookmark_list(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:get_bookmarks_by_page", kwargs={"page_number": 1})
    resp = client.get(url)

    assert resp.status_code == 200

    url = urls.reverse("bookmark:get_bookmarks_by_page", kwargs={"page_number": 2})
    resp = client.get(url)

    assert resp.status_code == 200


def test_bookmark_snarf_link(monkeypatch_bookmark, auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:snarf")
    resp = client.get(f"{url}?url=http%3A%2F%2Fwww.bordercore.com%2F&name=Sample%2BTitlte")

    assert resp.status_code == 302


def test_bookmark_get_tags_used_by_bookmarks(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:get_tags_used_by_bookmarks")
    resp = client.get(url)

    assert resp.status_code == 200


def test_bookmark_overview(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:overview")
    resp = client.get(url)

    assert resp.status_code == 200


def test_bookmark_get_bookmarks_by_tag(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:get_bookmarks_by_tag", kwargs={"tag_filter": "django"})
    resp = client.get(url)

    assert resp.status_code == 200


def test_bookmark_sort_pinned_tags(auto_login_user, sort_order_user_tag, tag):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:sort_pinned_tags")
    resp = client.post(url, {
        "tag_id": tag[1].id,
        "new_position": 1
    })

    assert resp.status_code == 200


def test_bookmark_sort_bookmarks(auto_login_user, tag, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:sort")
    resp = client.post(url, {
        "tag": tag[0].name,
        "bookmark_uuid": bookmark[0].uuid,
        "position": 3
    })

    assert resp.status_code == 200


def test_bookmark_add_note(auto_login_user, tag, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:add_note")
    resp = client.post(url, {
        "tag": tag[0].name,
        "bookmark_uuid": bookmark[0].uuid,
        "note": "Sample Note"
    })

    assert resp.status_code == 200


def test_bookmark_get_new_bookmarks_count(auto_login_user, bookmark):

    _, client = auto_login_user()

    timestamp = datetime.datetime.now()

    url = urls.reverse("bookmark:get_new_bookmarks_count", kwargs={"timestamp": f"{timestamp:%s}"})
    resp = client.get(url)

    assert resp.status_code == 200
    assert json.loads(resp.content)["count"] == 5


def test_bookmark_get_title_from_url(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:get_title_from_url")
    resp = client.get(f"{url}?url=http%3A%2F%2Fwww.bordercore.com")

    assert resp.status_code == 200


def test_get_related_bookmark_list(auto_login_user, bookmark):

    user, client = auto_login_user()

    blob = BlobFactory(user=user, tags=[])
    SortOrderBlobBookmark.objects.create(blob=blob, bookmark=bookmark[0])

    url = urls.reverse("bookmark:get_related_bookmark_list", kwargs={"uuid": blob.uuid})
    resp = client.get(f"{url}?model_name=blob.Blob")

    assert resp.status_code == 200


def test_add_related_bookmark(auto_login_user, bookmark):

    user, client = auto_login_user()

    blob = BlobFactory(user=user, tags=[])

    url = urls.reverse("bookmark:add_related_bookmark")
    resp = client.post(url, {
        "bookmark_uuid": bookmark[0].uuid,
        "object_uuid": blob.uuid,
        "model_name": "blob.Blob"
    })

    assert len(blob.sortorderblobbookmark_set.all()) == 1
    assert blob.sortorderblobbookmark_set.first().bookmark == bookmark[0]
    assert resp.status_code == 200


def test_remove_related_bookmark(auto_login_user, bookmark):

    user, client = auto_login_user()

    blob = BlobFactory(user=user, tags=[])
    so = SortOrderBlobBookmark(blob=blob, bookmark=bookmark[0])
    so.save()

    url = urls.reverse("bookmark:remove_related_bookmark")
    resp = client.post(url, {
        "bookmark_uuid": bookmark[0].uuid,
        "object_uuid": blob.uuid,
        "model_name": "blob.Blob"
    })

    assert len(blob.sortorderblobbookmark_set.all()) == 0
    assert resp.status_code == 200


def test_sort_related_bookmark(auto_login_user, bookmark):

    user, client = auto_login_user()

    blob = BlobFactory(user=user, tags=[])
    so = SortOrderBlobBookmark(blob=blob, bookmark=bookmark[0])
    so.save()
    so = SortOrderBlobBookmark(blob=blob, bookmark=bookmark[1])
    so.save()

    url = urls.reverse("bookmark:sort_related_bookmarks")
    resp = client.post(url, {
        "bookmark_uuid": bookmark[1].uuid,
        "object_uuid": blob.uuid,
        "model_name": "blob.Blob",
        "new_position": "2"
    })

    assert len(blob.sortorderblobbookmark_set.all()) == 2
    related_bookmarks = blob.sortorderblobbookmark_set.all()
    assert related_bookmarks[0].bookmark == bookmark[0]
    assert related_bookmarks[1].bookmark == bookmark[1]
    assert resp.status_code == 200


def test_edit_related_bookmark_note(auto_login_user, bookmark):

    user, client = auto_login_user()

    blob = BlobFactory(user=user, tags=[])
    so = SortOrderBlobBookmark(blob=blob, bookmark=bookmark[0])
    so.save()

    note = faker.text()

    url = urls.reverse("bookmark:edit_related_bookmark_note")
    resp = client.post(url, {
        "bookmark_uuid": bookmark[0].uuid,
        "object_uuid": blob.uuid,
        "model_name": "blob.Blob",
        "note": note
    })

    assert blob.sortorderblobbookmark_set.first().note == note
    assert resp.status_code == 200


def test_add_tag(auto_login_user, monkeypatch_bookmark):

    user, client = auto_login_user()

    bookmark = BookmarkFactory(user=user)
    tag = TagFactory(user=user)

    url = urls.reverse("bookmark:add_tag")
    resp = client.post(url, {
        "bookmark_uuid": bookmark.uuid,
        "tag_id": tag.id
    })

    updated_bookmark = Bookmark.objects.get(uuid=bookmark.uuid)
    assert updated_bookmark.tags.count() == 1
    assert updated_bookmark.tags.first() == tag
    assert resp.status_code == 200

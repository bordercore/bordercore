import datetime
import json

import pytest

from django import urls

from bookmark.models import Bookmark

pytestmark = pytest.mark.django_db


@pytest.fixture
def monkeypatch_index_bookmark(monkeypatch):
    """
    Prevent the bookmark object from interacting with Elasticsearch by
    patching out the Bookmark.index_bookmark() method
    """

    def mock(*args, **kwargs):
        pass
    monkeypatch.setattr(Bookmark, "index_bookmark", mock)


def test_bookmark_click(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:click", kwargs={"bookmark_id": bookmark[0].id})
    resp = client.get(url)

    assert resp.status_code == 302


def test_bookmark_update(monkeypatch_index_bookmark, auto_login_user, bookmark):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("bookmark:update", kwargs={"pk": bookmark[0].id})
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("bookmark:update", kwargs={"pk": bookmark[0].id})
    resp = client.post(url, {
        "url": "https://www.bordercore.com/bookmark/",
        "title": "Sample Title Changed",
        "tags": "linux",
        "importance": "1"
    })

    assert resp.status_code == 302


def test_bookmark_create(monkeypatch_index_bookmark, auto_login_user, bookmark):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("bookmark:create")
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("bookmark:create")

    resp = client.post(url, {
        "url": "https://www.bordercore.com/foo",
        "title": "Sample Title",
        "tags": "django",
        "importance": "1"
    })

    assert resp.status_code == 302


def test_bookmark_delete(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:delete", kwargs={"pk": bookmark[0].id})
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


def test_bookmark_snarf_link(monkeypatch_index_bookmark, auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:snarf")
    resp = client.get(f"{url}?url=http%3A%2F%2Fwww.bordercore.com%2F&title=Sample%2BTitlte")

    assert resp.status_code == 302


def test_bookmark_get_tags_used_by_bookmarks(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:get_tags_used_by_bookmarks")
    resp = client.get(url)

    assert resp.status_code == 200


def test_bookmark_get_bookmarks_by_random(auto_login_user, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:get_bookmarks_by_random")
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


def test_bookmark_sort_favorite_tags(auto_login_user, sort_order_user_tag, tag):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:sort_favorite_tags")
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
        "link_id": bookmark[0].id,
        "position": 3
    })

    assert resp.status_code == 200


def test_bookmark_add_note(auto_login_user, tag, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:add_note")
    resp = client.post(url, {
        "tag": tag[0].name,
        "link_id": bookmark[0].id,
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

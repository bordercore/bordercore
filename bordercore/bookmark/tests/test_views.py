import datetime
import json

import pytest
from faker import Factory as FakerFactory

from django import urls

from blob.models import SortOrderBlobBookmark
from blob.tests.factories import BlobFactory
from bookmark.models import Bookmark
from drill.models import Question, SortOrderQuestionBookmark
from drill.tests.factories import QuestionFactory
from node.models import Node, SortOrderNodeBookmark
from node.tests.factories import NodeFactory

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


def test_get_related_bookmark_list(auto_login_user, node):

    _, client = auto_login_user()

    url = urls.reverse("bookmark:get_related_bookmark_list", kwargs={"uuid": node.uuid})
    resp = client.get(f"{url}?model_name=node.Node")

    assert resp.status_code == 200


def test_add_related_bookmark(auto_login_user, bookmark):

    user, client = auto_login_user()

    node = NodeFactory(user=user)

    url = urls.reverse("bookmark:add_related_bookmark")
    resp = client.post(url, {
        "bookmark_uuid": bookmark[0].uuid,
        "object_uuid": node.uuid,
        "model_name": "node.Node"
    })

    assert len(node.sortordernodebookmark_set.all()) == 1
    assert node.sortordernodebookmark_set.first().bookmark == bookmark[0]
    assert resp.status_code == 200

    question = QuestionFactory(user=user)
    question_modified = question.modified

    url = urls.reverse("bookmark:add_related_bookmark")
    resp = client.post(f"{url}?update_modified=true", {
        "bookmark_uuid": bookmark[0].uuid,
        "object_uuid": question.uuid,
        "model_name": "drill.Question"
    })
    assert len(question.sortorderquestionbookmark_set.all()) == 1
    assert question.sortorderquestionbookmark_set.first().bookmark == bookmark[0]

    # Since we've passed in the 'update_modified' parameter, verify
    #  that the timestamp has been modified and is indeed later.
    updated_question = Question.objects.get(uuid=question.uuid)
    assert updated_question.modified > question_modified
    assert resp.status_code == 200

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

    node = NodeFactory(user=user)
    node_modified = node.modified
    so = SortOrderNodeBookmark(node=node, bookmark=bookmark[0])
    so.save()

    url = urls.reverse("bookmark:remove_related_bookmark")
    resp = client.post(f"{url}?update_modified=true", {
        "bookmark_uuid": bookmark[0].uuid,
        "object_uuid": node.uuid,
        "model_name": "node.Node"
    })

    assert len(node.sortordernodebookmark_set.all()) == 0
    assert resp.status_code == 200

    # Since we've passed in the 'update_modified' parameter, verify
    #  that the timestamp has been modified and is indeed later.
    updated_node = Node.objects.get(uuid=node.uuid)
    assert updated_node.modified > node_modified

    question = QuestionFactory(user=user)
    so = SortOrderQuestionBookmark(question=question, bookmark=bookmark[0])
    so.save()

    url = urls.reverse("bookmark:remove_related_bookmark")
    resp = client.post(url, {
        "bookmark_uuid": bookmark[0].uuid,
        "object_uuid": question.uuid,
        "model_name": "drill.Question"
    })

    assert len(question.sortorderquestionbookmark_set.all()) == 0
    assert resp.status_code == 200

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

    node = NodeFactory(user=user)
    so = SortOrderNodeBookmark(node=node, bookmark=bookmark[0])
    so.save()
    so = SortOrderNodeBookmark(node=node, bookmark=bookmark[1])
    so.save()

    url = urls.reverse("bookmark:sort_related_bookmarks")
    resp = client.post(url, {
        "bookmark_uuid": bookmark[1].uuid,
        "object_uuid": node.uuid,
        "model_name": "node.Node",
        "new_position": "2"
    })

    assert len(node.sortordernodebookmark_set.all()) == 2
    related_bookmarks = node.sortordernodebookmark_set.all()
    assert related_bookmarks[0].bookmark == bookmark[0]
    assert related_bookmarks[1].bookmark == bookmark[1]
    assert resp.status_code == 200


def test_edit_related_bookmark_note(auto_login_user, bookmark):

    user, client = auto_login_user()

    node = NodeFactory(user=user)
    so = SortOrderNodeBookmark(node=node, bookmark=bookmark[0])
    so.save()

    note = faker.text()

    url = urls.reverse("bookmark:edit_related_bookmark_note")
    resp = client.post(url, {
        "bookmark_uuid": bookmark[0].uuid,
        "object_uuid": node.uuid,
        "model_name": "node.Node",
        "note": note
    })

    assert node.sortordernodebookmark_set.first().note == note
    assert resp.status_code == 200

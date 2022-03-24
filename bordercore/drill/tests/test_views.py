import json
from pathlib import Path
from unittest.mock import MagicMock

import factory
import pytest
import responses

from django import urls
from django.db.models import signals

from drill.models import (Question, SortOrderQuestionBlob,
                          SortOrderQuestionBookmark)
from drill.views import handle_related_blobs, handle_related_bookmarks

pytestmark = [pytest.mark.django_db, pytest.mark.views]


@pytest.fixture
def monkeypatch_drill(monkeypatch):
    """
    Prevent the question object from interacting with Elasticsearch by
    patching out the Question.delete() method
    """

    def mock(*args, **kwargs):
        pass
    monkeypatch.setattr(Question, "delete", mock)


def test_drill_list(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:list")
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_create(auto_login_user, question):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("drill:add")
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("drill:add")
    resp = client.post(url, {
        "question": "Sample Question",
        "answer": "Sample Answer",
        "tags": "django"
    })

    assert resp.status_code == 302


def test_drill_handle_related_bookmarks(monkeypatch_drill, auto_login_user, question, bookmark):

    user, client = auto_login_user()

    mock_request = MagicMock()
    mock_request.user = user
    mock_request.POST = {
        "related-bookmarks": json.dumps(
            [
                {
                    "uuid": str(bookmark[0].uuid),
                    "note": ""
                }
            ]
        )
    }

    handle_related_bookmarks(question[1], mock_request)

    so = SortOrderQuestionBookmark.objects.filter(question=question[1], bookmark=bookmark[0])
    assert so.exists()


def test_drill_handle_related_blobs(monkeypatch_drill, auto_login_user, question, blob_image_factory):

    user, client = auto_login_user()

    mock_request = MagicMock()
    mock_request.user = user
    mock_request.POST = {
        "related-blobs": json.dumps(
            [
                {
                    "uuid": str(blob_image_factory[0].uuid),
                    "note": ""
                }
            ]
        )
    }

    handle_related_blobs(question[0], mock_request)

    so = SortOrderQuestionBlob.objects.filter(question=question[0], blob=blob_image_factory[0])
    assert so.exists()


def test_drill_delete(monkeypatch_drill, auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:delete", kwargs={"uuid": question[0].uuid})
    resp = client.post(url, {})

    assert resp.status_code == 302


def test_drill_detail(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:detail", kwargs={"uuid": question[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_update(auto_login_user, question):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("drill:update", kwargs={"uuid": question[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("drill:update", kwargs={"uuid": question[0].uuid})
    resp = client.post(url, {
        "question": "Sample Question Changed",
        "answer": "Sample Answer Changed",
        "tags": "django"
    })

    assert resp.status_code == 302


def test_drill_show_answer(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:answer", kwargs={"uuid": question[0].uuid})
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_start_study_session(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse(
        "drill:start_study_session",
        kwargs={
            "session_type": "favorites"
        }
    )
    resp = client.get(url)

    assert resp.status_code == 302


@factory.django.mute_signals(signals.post_save)
def test_drill_study(auto_login_user, question):

    _, client = auto_login_user()

    session = client.session

    session["drill_study_session"] = {
        "type": "random",
        "current": str(question[0].uuid),
        "list": [str(x.uuid) for x in question]
    }
    session.save()

    url = urls.reverse(
        "drill:study"
    )

    # Study the second question
    resp = client.get(url)
    assert resp.status_code == 302
    session = client.session
    assert session["drill_study_session"]["current"] == str(question[1].uuid)

    # Study the third question
    resp = client.get(url)
    assert resp.status_code == 302
    session = client.session
    assert session["drill_study_session"]["current"] == str(question[2].uuid)

    # Study the fourth question
    resp = client.get(url)
    assert resp.status_code == 302
    session = client.session
    assert session["drill_study_session"]["current"] == str(question[3].uuid)

    # Verify that the study session is over, since we've exhausted all questions
    resp = client.get(url)
    assert resp.status_code == 302
    session = client.session
    assert "drill_study_session" not in session


@factory.django.mute_signals(signals.post_save)
def test_drill_get_current_question(auto_login_user, question):

    _, client = auto_login_user()

    session = client.session

    # Create a study session of random questions and set
    #  the current question to the second one.
    session["drill_study_session"] = {
        "type": "random",
        "current": str(question[1].uuid),
        "list": [str(x.uuid) for x in question]
    }
    session.save()

    url = urls.reverse(
        "drill:resume"
    )
    resp = client.get(url)
    assert resp.status_code == 302


@factory.django.mute_signals(signals.post_save)
def test_drill_record_response(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse(
        "drill:record_response",
        kwargs={
            "uuid": question[0].uuid,
            "response": "Sample Response"
        }
    )
    resp = client.get(url)

    assert resp.status_code == 302


@factory.django.mute_signals(signals.post_save)
def test_drill_get_pinned_tags(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse(
        "drill:get_pinned_tags"
    )
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_pin_tag(auto_login_user, question, tag):

    _, client = auto_login_user()

    url = urls.reverse("drill:pin_tag")
    resp = client.post(url, {
        "tag": tag[2].name
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200

    url = urls.reverse("drill:pin_tag")
    resp = client.post(url, {
        "tag": tag[2].name
    })

    assert json.loads(resp.content)["status"] == "Error"
    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_unpin_tag(auto_login_user, question, tag):

    _, client = auto_login_user()

    url = urls.reverse("drill:unpin_tag")
    resp = client.post(url, {
        "tag": tag[0].name
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200

    resp = client.post(url, {
        "tag": tag[0].name
    })

    assert json.loads(resp.content)["status"] == "Error"
    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_sort_pinned_tags(auto_login_user, question, tag):

    _, client = auto_login_user()

    url = urls.reverse("drill:sort_pinned_tags")
    resp = client.post(url, {
        "tag_name": tag[0].name,
        "new_position": 1
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_is_favorite_mutate(auto_login_user, question, tag):

    _, client = auto_login_user()

    url = urls.reverse("drill:is_favorite_mutate")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "mutation": "add"
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200

    # Retrieve the question from the database and verify it is now a favorite
    question_refreshed = Question.objects.get(uuid=question[0].uuid)
    assert question_refreshed.is_favorite is True

    url = urls.reverse("drill:is_favorite_mutate")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "mutation": "delete"
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200

    # Retrieve the question from the database and verify it is no longer a favorite
    question_refreshed = Question.objects.get(uuid=question[0].uuid)
    assert question_refreshed.is_favorite is False


@responses.activate
def test_get_title_from_url(auto_login_user, bookmark):

    _, client = auto_login_user()

    with open(Path(__file__).parent / "resources/bordercore.html") as f:
        html = f.read()

    responses.add(responses.GET, "https://www.bordercore.com/bookmarks/", body=html)

    url = urls.reverse("drill:get_title_from_url")

    # Test existing bookmark
    resp = client.get(f"{url}?url={bookmark[0].url}")
    content = json.loads(resp.content)
    assert content["status"] == "OK"
    assert resp.status_code == 200
    assert content["bookmarkUuid"] == str(bookmark[0].uuid)
    assert content["title"] == bookmark[0].name

    # Test new bookmark
    resp = client.get(f"{url}?url=https://www.bordercore.com/bookmarks/")
    content = json.loads(resp.content)
    assert content["status"] == "OK"
    assert resp.status_code == 200
    assert content["bookmarkUuid"] is None
    assert content["title"] == "Bordercore Bookmarks"


def test_drill_get_blob_list(auto_login_user, question, blob_note):

    _, client = auto_login_user()

    so = SortOrderQuestionBlob(question=question[0], blob=blob_note[0])
    so.save()

    url = urls.reverse("drill:get_blob_list", kwargs={"uuid": question[0].uuid})

    resp = client.get(url)

    content = json.loads(resp.content)
    assert content["status"] == "OK"

    assert len(content["blob_list"]) == 1
    assert content["blob_list"][0]["name"] == blob_note[0].name
    assert content["blob_list"][0]["uuid"] == str(blob_note[0].uuid)


def test_drill_sort_blob_list(auto_login_user, question, blob_note):

    _, client = auto_login_user()

    so = SortOrderQuestionBlob(question=question[0], blob=blob_note[0])
    so.save()

    so = SortOrderQuestionBlob(question=question[0], blob=blob_note[1])
    so.save()

    url = urls.reverse("drill:sort_blob_list")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "blob_uuid": blob_note[1].uuid,
        "new_position": 2,
    })

    assert resp.status_code == 200

    so = SortOrderQuestionBlob.objects.get(question=question[0], blob=blob_note[0])
    assert so.sort_order == 1
    so = SortOrderQuestionBlob.objects.get(question=question[0], blob=blob_note[1])
    assert so.sort_order == 2


def test_drill_add_blob(auto_login_user, question, blob_note):

    _, client = auto_login_user()

    url = urls.reverse("drill:add_blob")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "blob_uuid": blob_note[0].uuid,
    })

    assert resp.status_code == 200

    assert SortOrderQuestionBlob.objects.filter(question__uuid=question[0].uuid, blob__uuid=blob_note[0].uuid).exists()

    url = urls.reverse("drill:add_blob")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "blob_uuid": blob_note[0].uuid,
    })

    assert resp.status_code == 200
    assert json.loads(resp.content) == {"message": "Blob already related to this question", "status": "Warning"}


def test_drill_remove_blob(auto_login_user, question, blob_note):

    _, client = auto_login_user()

    so = SortOrderQuestionBlob(question=question[0], blob=blob_note[0])
    so.save()

    url = urls.reverse("drill:remove_blob")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "blob_uuid": blob_note[0].uuid,
    })

    assert resp.status_code == 200

    assert not SortOrderQuestionBlob.objects.filter(question__uuid=question[0].uuid, blob__uuid=blob_note[0].uuid).exists()


def test_drill_edit_blob_note(auto_login_user, question, blob_note):

    _, client = auto_login_user()

    so = SortOrderQuestionBlob(question=question[0], blob=blob_note[0])
    so.save()

    note = "Updated Note"

    url = urls.reverse("drill:edit_blob_note")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "blob_uuid": blob_note[0].uuid,
        "note": note
    })

    assert resp.status_code == 200

    so = SortOrderQuestionBlob.objects.get(question__uuid=question[0].uuid, blob__uuid=blob_note[0].uuid)
    assert so.note == note

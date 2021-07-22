import json
from pathlib import Path

import factory
import pytest
import responses

from django import urls
from django.db.models import signals

from drill.models import Question, SortOrderDrillBookmark

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


def test_drill_search_list(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:search")
    resp = client.get(f"{url}?search=foobar")

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
        "tag": tag[0].name
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200

    url = urls.reverse("drill:pin_tag")
    resp = client.post(url, {
        "tag": tag[0].name
    })

    assert json.loads(resp.content)["status"] == "Error"
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


def test_drill_get_bookmark_list(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse(
        "drill:get_bookmark_list",
        kwargs={
            "uuid": question[0].uuid
        }
    )
    resp = client.get(url)

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_sort_bookmark_list(auto_login_user, question, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("drill:sort_bookmark_list")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "bookmark_uuid": bookmark[0].uuid,
        "new_position": 2
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_add_bookmark(auto_login_user, question, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("drill:add_bookmark")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "bookmark_uuid": bookmark[2].uuid,
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200

    assert len(SortOrderDrillBookmark.objects.filter(question=question[0])) == 3


@factory.django.mute_signals(signals.post_save)
def test_remove_bookmark(auto_login_user, question, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("drill:remove_bookmark")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "bookmark_uuid": bookmark[1].uuid,
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200

    assert len(SortOrderDrillBookmark.objects.filter(question=question[0])) == 1


@factory.django.mute_signals(signals.post_save)
def test_edit_bookmark_note(auto_login_user, question, bookmark):

    _, client = auto_login_user()

    url = urls.reverse("drill:edit_bookmark_note")
    resp = client.post(url, {
        "question_uuid": question[0].uuid,
        "bookmark_uuid": bookmark[1].uuid,
        "note": "New note"
    })

    assert json.loads(resp.content)["status"] == "OK"
    assert resp.status_code == 200

    assert SortOrderDrillBookmark.objects.get(
        question=question[0],
        bookmark=bookmark[1]
    ).note == "New note"


@responses.activate
def test_get_title_from_url(auto_login_user, bookmark):

    _, client = auto_login_user()

    with open(Path(__file__).parent / "resources/bordercore.html") as f:
        html = f.read()

    responses.add(responses.GET, "https://www.bordercore.com/bookmarks/", body=html)

    url = urls.reverse(
        "drill:get_title_from_url"
    )

    # Test existing bookmark
    resp = client.get(f"{url}?url=https://www.bordercore.com")
    content = json.loads(resp.content)
    assert content["status"] == "OK"
    assert resp.status_code == 200
    assert content["bookmarkUuid"] == str(bookmark[4].uuid)
    assert content["title"] == bookmark[4].name

    # Test new bookmark
    resp = client.get(f"{url}?url=https://www.bordercore.com/bookmarks/")
    content = json.loads(resp.content)
    assert content["status"] == "OK"
    assert resp.status_code == 200
    assert content["bookmarkUuid"] is None
    assert content["title"] == "Bordercore Bookmarks"

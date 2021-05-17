import json

import factory
import pytest
from elasticsearch import Elasticsearch

from django import urls
from django.db.models import signals

from drill.models import Question

pytestmark = pytest.mark.django_db



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

import factory
import pytest

from django import urls
from django.db.models import signals

pytestmark = pytest.mark.django_db


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


def test_drill_delete(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:delete", kwargs={"pk": question.id})
    resp = client.post(url, {})

    assert resp.status_code == 302


def test_drill_detail(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:detail", kwargs={"question_id": question.id})
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_update(auto_login_user, question):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("drill:update", kwargs={"pk": question.id})
    resp = client.get(url)

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("drill:update", kwargs={"pk": question.id})
    resp = client.post(url, {
        "question": "Sample Question Changed",
        "answer": "Sample Answer Changed",
        "tags": "django"
    })

    assert resp.status_code == 302


def test_drill_study_random(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:study_random")
    resp = client.get(url)

    assert resp.status_code == 302


def test_drill_study_tag(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:study_tag", kwargs={"tag": "django"})
    resp = client.get(url)

    assert resp.status_code == 302


def test_drill_show_answer(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:answer", kwargs={"question_id": question.id})
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_drill_record_response(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse(
        "drill:record_response",
        kwargs={
            "question_id": question.id,
            "response": "Sample Response"
        }
    )
    resp = client.get(url)

    assert resp.status_code == 302


def test_drill_skip_question(auto_login_user, question):

    _, client = auto_login_user()

    url = urls.reverse("drill:skip", kwargs={"question_id": question.id})
    resp = client.get(url)

    assert resp.status_code == 302

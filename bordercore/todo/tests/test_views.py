import factory
import pytest

from django import urls
from django.db.models import signals

from todo.views import Todo

pytestmark = [pytest.mark.django_db, pytest.mark.views]


@pytest.fixture
def monkeypatch_todo(monkeypatch):
    """
    Prevent the todo object from interacting with Elasticsearch by
    patching out various methods.
    """

    def mock(*args, **kwargs):
        pass

    monkeypatch.setattr(Todo, "delete", mock)


def test_todo_list_empty(auto_login_user):

    _, client = auto_login_user()

    url = urls.reverse("todo:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_todo_list(auto_login_user, todo):

    _, client = auto_login_user()

    url = urls.reverse("todo:list")
    resp = client.get(url)

    assert resp.status_code == 200


@factory.django.mute_signals(signals.post_save)
def test_todo_detail(auto_login_user, todo):

    _, client = auto_login_user()

    url = urls.reverse("todo:update", kwargs={"uuid": todo.uuid})
    resp = client.post(url, {
        "name": "Sample Task Changed",
        "priority": "2",
        "tags": "django"
    })

    assert resp.status_code == 302


@factory.django.mute_signals(signals.post_save)
def test_todo_create(auto_login_user, todo):

    _, client = auto_login_user()

    # The empty form
    url = urls.reverse("todo:create")
    resp = client.get(f"{url}?tagsearch=tag_0")

    assert resp.status_code == 200

    # The submitted form
    url = urls.reverse("todo:create")
    resp = client.post(url, {
        "name": "Sample Task",
        "priority": "2",
        "tags": "django"
    })

    assert resp.status_code == 302


def test_todo_delete(monkeypatch_todo, auto_login_user, todo):

    _, client = auto_login_user()

    url = urls.reverse("todo:delete", kwargs={"uuid": todo.uuid})
    resp = client.post(url, {})

    assert resp.status_code == 302


def test_sort_todo(auto_login_user, todo):

    _, client = auto_login_user()

    url = urls.reverse("todo:sort")
    resp = client.post(url, {
        "tag": "tag_0",
        "todo_uuid": todo.uuid,
        "position": "2"
    })

    assert resp.status_code == 200

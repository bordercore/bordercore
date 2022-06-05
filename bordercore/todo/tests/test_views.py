import factory
import pytest

from django import urls
from django.conf import settings
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
def test_todo_create(auto_login_user, todo):

    _, client = auto_login_user()

    url = urls.reverse("todo-list")
    resp = client.post(url, {
        "name": "Sample Task",
        "priority": "2",
        "tags": "django"
    })

    assert resp.status_code == 201

    uuid = resp.json()["uuid"]
    todo = Todo.objects.get(uuid=uuid)
    assert todo.name == "Sample Task"
    assert todo.priority == 2
    assert "django" in [x.name for x in todo.tags.all()]


@factory.django.mute_signals(signals.post_save)
def test_todo_update(auto_login_user, todo):

    # Quiet spurious output
    settings.NPLUSONE_WHITELIST = [
        {
            "label": "unused_eager_load",
            "model": "todo.Todo"
        }
    ]

    _, client = auto_login_user()

    url = urls.reverse("todo-detail", kwargs={"uuid": todo.uuid})
    resp = client.put(
        url,
        content_type="application/json",
        data={
            "todo_uuid": todo.uuid,
            "name": "New Task Name",
            "priority": "3",
            "tags": ["django"]
        }
    )

    assert resp.status_code == 200

    todo = Todo.objects.get(uuid=todo.uuid)
    assert todo.name == "New Task Name"
    assert todo.priority == 3
    assert "django" in [x.name for x in todo.tags.all()]


def test_sort_todo(auto_login_user, todo):

    _, client = auto_login_user()

    url = urls.reverse("todo:sort")
    resp = client.post(url, {
        "tag": "tag_0",
        "todo_uuid": todo.uuid,
        "position": "2"
    })

    assert resp.status_code == 200

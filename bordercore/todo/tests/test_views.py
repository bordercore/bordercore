import factory
import pytest

from django import urls
from django.db.models import signals

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    pass

pytestmark = pytest.mark.django_db


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
        "task": "Sample Task Changed",
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
        "task": "Sample Task",
        "priority": "2",
        "tags": "django"
    })

    assert resp.status_code == 302


def test_todo_delete(auto_login_user, todo):

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

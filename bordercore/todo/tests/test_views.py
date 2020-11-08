import pytest

from django import urls

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    pass

from django.contrib.auth.models import User  # isort:skip
from tag.models import Tag  # isort:skip
from blob.models import Blob  # isort:skip


@pytest.fixture(scope="function")
def user(db, client, django_user_model):
    username = "testuser"
    password = "password"
    email = "testuser@testdomain.com"

    user = django_user_model.objects.create_user(username, email, password)
    client.login(username=username, password=password)

    return user


def test_todo_list_empty(user, client):

    url = urls.reverse("todo:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_todo_list(user, client, todo_factory):

    url = urls.reverse("todo:list")
    resp = client.get(url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    assert soup.select("table#todo_list tr:nth-child(1) td")[4].text.strip() == "task_3"

import pytest

from django import urls

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


def test_todo_list(auto_login_user, todo_factory):

    _, client = auto_login_user()

    url = urls.reverse("todo:list")
    resp = client.get(url)

    assert resp.status_code == 200

    soup = BeautifulSoup(resp.content, "html.parser")

    assert soup.select("table#todo_list tr:nth-child(1) td")[4].text.strip() == "task_2"

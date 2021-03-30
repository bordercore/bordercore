import pytest

from django import urls

pytestmark = pytest.mark.django_db


def test_homepage(auto_login_user, bookmark, question, todo):

    _, client = auto_login_user()

    url = urls.reverse("homepage:homepage")
    resp = client.get(url)

    assert resp.status_code == 200

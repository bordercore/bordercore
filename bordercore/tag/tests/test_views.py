import pytest

from django import urls

pytestmark = [pytest.mark.django_db, pytest.mark.views]


def test_tag_search(auto_login_user, tag):

    _, client = auto_login_user()

    url = urls.reverse("tag:search")
    resp = client.get(f"{url}?query=djang")

    assert resp.status_code == 200


def test_tag_pin(auto_login_user, tag):

    _, client = auto_login_user()

    url = urls.reverse("tag:pin")
    resp = client.post(url, {
        "tag": "django"
    })

    assert resp.status_code == 302


def test_tag_unpin(auto_login_user, tag):

    _, client = auto_login_user()

    tag[0].pin()

    url = urls.reverse("tag:unpin")
    resp = client.post(url, {
        "tag": "django"
    })

    assert resp.status_code == 302

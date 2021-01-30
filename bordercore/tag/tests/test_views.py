import pytest

from django import urls

pytestmark = pytest.mark.django_db


def test_tag_search(auto_login_user, tag):

    _, client = auto_login_user()

    url = urls.reverse("tag:search")
    resp = client.get(f"{url}?query=djang")

    assert resp.status_code == 200


def test_tag_add_favorite_tag(auto_login_user, tag):

    _, client = auto_login_user()

    url = urls.reverse("tag:add_favorite_tag")
    resp = client.post(url, {
        "tag": "django"
    })

    assert resp.status_code == 302


def test_tag_remove_favorite_tag(auto_login_user, tag):

    _, client = auto_login_user()

    tag[0].add_favorite_tag()

    url = urls.reverse("tag:remove_favorite_tag")
    resp = client.post(url, {
        "tag": "django"
    })

    assert resp.status_code == 302

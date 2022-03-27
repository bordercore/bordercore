import pytest

from django import urls

from tag.models import TagAlias

pytestmark = [pytest.mark.django_db, pytest.mark.views]


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


def test_tag_list(auto_login_user, tag):

    user, client = auto_login_user()

    url = urls.reverse("tag:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_tag_add_alias(auto_login_user, tag):

    user, client = auto_login_user()

    tag_alias_name = "tag alias name"

    url = urls.reverse("tag:add_alias")
    resp = client.post(url, {
        "tag_name": tag[0].name,
        "alias_name": tag_alias_name
    })

    assert resp.status_code == 200

    tag_alias = TagAlias.objects.filter(name=tag_alias_name, tag=tag[0], user=user)

    assert tag_alias.exists()

    resp = client.post(url, {
        "tag_name": tag[0].name,
        "alias_name": tag_alias_name
    })

    assert resp.status_code == 200
    assert resp.json()["message"] == "Alias already exists"

    resp = client.post(url, {
        "tag_name": tag_alias,
        "alias_name": tag[0].name
    })

    assert resp.status_code == 200
    assert resp.json()["message"] == f"A tag with the name '{tag[0]}' already exists"


def test_tag_todo_counts(auto_login_user, tag):

    user, client = auto_login_user()

    url = urls.reverse("tag:get_todo_counts")
    resp = client.get(url)

    assert resp.status_code == 200

    response = resp.json()
    assert response["info"]["name"] in [x.name for x in tag]

    url = urls.reverse("tag:get_todo_counts")
    resp = client.get(f"{url}?tag_name={tag[1]}")

    assert resp.status_code == 200

    response = resp.json()
    assert response["info"]["name"] == tag[1].name
    assert response["info"]["blob__count"] == 0

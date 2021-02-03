import pytest

from django import urls

pytestmark = pytest.mark.django_db


def test_feed_list(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_feed_subscription_list(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:subscriptions")
    resp = client.get(url)

    assert resp.status_code == 200


def test_feed_create(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:create")
    resp = client.get(url)

    assert resp.status_code == 200


def test_feed_update(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:update", kwargs={"feed_id": feed[0].id})
    resp = client.post(url, {
        "Go": "Update",
        "name": "Feed Name Changed",
        "url": "https://www.bordercore.com/rss",
        "homepage": "https://www.bordercore.com"
    })

    assert resp.status_code == 200


def test_feed_delete(auto_login_user, feed):

    _, client = auto_login_user()

    feed[0].feeditem_set.all().delete()

    url = urls.reverse("feed:update", kwargs={"feed_id": feed[0].id})
    resp = client.post(url, {
        "Go": "Delete",
    })

    assert resp.status_code == 302


def test_sort_feed(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:sort")
    resp = client.post(url, {"feed_id": feed[0].id, "position": "2"})

    assert resp.status_code == 200


def test_feed_subscribe(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:subscribe")
    resp = client.post(url, {"feed_id": feed[1].id, "position": "1"})

    assert resp.status_code == 200


def test_feed_unsubscribe(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:unsubscribe")
    resp = client.post(url, {"feed_id": feed[0].id})

    assert resp.status_code == 200

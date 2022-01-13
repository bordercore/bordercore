import pytest

from django import urls

from feed.models import Feed

pytestmark = [pytest.mark.django_db, pytest.mark.views]


def test_feed_list(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:list")
    resp = client.get(url)

    assert resp.status_code == 200


def test_feed_delete(auto_login_user, feed):

    _, client = auto_login_user()

    feed[0].feeditem_set.all().delete()

    url = urls.reverse("feed-detail", kwargs={"uuid": feed[0].uuid})
    resp = client.delete(url)

    assert resp.status_code == 204

    assert Feed.objects.filter(uuid=feed[0].uuid).count() == 0


def test_sort_feed(auto_login_user, feed):

    _, client = auto_login_user()

    url = urls.reverse("feed:sort")
    resp = client.post(url, {"feed_id": feed[0].id, "position": "2"})

    assert resp.status_code == 200

import logging
from pathlib import Path

import pytest
import responses

import django

django.setup()

from feed.models import Feed, FeedItem  # isort:skip

pytestmark = pytest.mark.django_db


def test_feed_str(auto_login_user, feed):

    user, _ = auto_login_user()

    assert str(feed[0]) == "Hacker News"


def test_get_current_feed_id(auto_login_user, feed):

    user, _ = auto_login_user()

    session = {}
    assert Feed.get_current_feed_id(user, session) == feed[2].id

    session = {"current_feed": feed[0].id}
    assert Feed.get_current_feed_id(user, session) == feed[0].id

    # Test for a non-existent current. This should
    #  return the first feed
    # The test emits a warning we'd like to ignore
    logging.disable(logging.WARNING)
    session = {"current_feed": 666}
    assert Feed.get_current_feed_id(user, session) == feed[2].id


def test_get_first_feed(auto_login_user, feed):

    user, _ = auto_login_user()

    assert Feed.get_first_feed(user) == {
        "id": feed[2].id
    }


@responses.activate
def test_update(auto_login_user, feed):

    user, _ = auto_login_user()

    with open(Path(__file__).parent / "resources/rss.xml") as f:
        xml = f.read()

    responses.add(responses.GET, feed[0].url, body=xml)

    feed[0].update()

    assert feed[0].last_response_code == 200

    assert FeedItem.objects.filter(feed=feed[0]).count() == 4

    assert FeedItem.objects.filter(feed=feed[0])[2].title == "Bad Title"

    assert FeedItem.objects.filter(feed=feed[0])[3].title == "No Title"

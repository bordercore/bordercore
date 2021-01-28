from pathlib import Path

import pytest
import responses

import django

django.setup()

from feed.models import Feed, FeedItem  # isort:skip
from accounts.models import UserProfile  # isort:skip

pytestmark = pytest.mark.django_db


def test_feed_str(auto_login_user, feed):

    user, _ = auto_login_user()

    assert str(feed[0]) == "Hacker News"


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

    # Delete the feed and verify that the user is no longer subscribed
    FeedItem.objects.filter(feed=feed[0]).delete()
    feed[0].delete()
    userprofile = UserProfile.objects.get(user=user)

    assert feed[0].id not in userprofile.rss_feeds


def test_get_feed_list(auto_login_user, feed):

    user, _ = auto_login_user()

    rss_feeds = user.userprofile.rss_feeds
    feed_list = Feed.get_feed_list(rss_feeds)
    assert feed_list[0].name == "Hacker News"


def test_subscribe_user(auto_login_user, feed):

    user, _ = auto_login_user()

    feed[1].subscribe_user(user, 1)
    userprofile = UserProfile.objects.get(user=user)
    assert feed[1].id in userprofile.rss_feeds

    feed[1].unsubscribe_user(user)
    userprofile = UserProfile.objects.get(user=user)
    assert feed[1].id not in userprofile.rss_feeds


def test_unsubscribe_user(auto_login_user, feed):

    user, _ = auto_login_user()

    feed[0].unsubscribe_user(user)
    userprofile = UserProfile.objects.get(user=user)
    assert feed[0].id not in userprofile.rss_feeds

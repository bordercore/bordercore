import xml.sax.saxutils as saxutils
from datetime import datetime

import feedparser
import psycopg2
import psycopg2.extras
import requests

from django.db import models
from django.utils.timezone import utc

from accounts.models import UserProfile
from lib.mixins import TimeStampedModel

USER_AGENT = "Bordercore/1.0"


class Feed(TimeStampedModel):
    name = models.TextField()
    url = models.URLField(unique=True)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)
    homepage = models.URLField(null=True)

    def delete(self):
        # Unsubscribe all users who are currently subscribed to this feed
        subscribers = UserProfile.objects.filter(rss_feeds__contains=[int(self.pk)])
        for userprofile in subscribers:
            feeds = userprofile.rss_feeds
            feeds.remove(self.pk)
            userprofile.rss_feeds = feeds
            userprofile.save()
        super(Feed, self).delete()

    def update(self):
        try:

            headers = {'user-agent': USER_AGENT}
            r = requests.get(self.url, headers=headers)

            if r.status_code != 200:
                r.raise_for_status()

            d = feedparser.parse(r.text)

            FeedItem.objects.filter(feed_id=self.pk).delete()

            for x in d.entries:
                title = x.title.replace("\n", "") or 'No Title'
                link = x.link or ''
                FeedItem.objects.create(feed_id=self.pk, title=saxutils.unescape(title), link=saxutils.unescape(link))

        except Exception as e:

            message = ""
            if isinstance(e, requests.exceptions.HTTPError):
                message = e
            elif isinstance(e, psycopg2.Error):
                message = e.pgerror
            elif isinstance(e, UnicodeEncodeError):
                message = str(type(e)) + ': ' + str(e)
            else:
                message = e

            raise Exception(message)

        finally:

            self.last_response_code = r.status_code
            self.last_check = datetime.utcnow().replace(tzinfo=utc)
            self.save()

    def subscribe_user(self, user, position):
        feeds = user.userprofile.rss_feeds
        # Verify that the user isn't already subscribed
        if feeds is None:
            feeds = []
        if self.pk in feeds:
            return
        feeds.insert(position - 1, self.pk)
        user.userprofile.rss_feeds = feeds
        user.userprofile.save()

    def unsubscribe_user(self, user):
        feeds = user.userprofile.rss_feeds
        feeds.remove(self.pk)
        user.userprofile.rss_feeds = feeds
        user.userprofile.save()


class FeedItem(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.PROTECT)
    title = models.TextField()
    link = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

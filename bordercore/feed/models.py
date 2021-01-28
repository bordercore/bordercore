import xml.sax.saxutils as saxutils
from datetime import datetime

import feedparser
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

    def __str__(self):
        return self.name

    def delete(self):

        # Unsubscribe all users who are currently subscribed to this feed
        subscribers = UserProfile.objects.filter(rss_feeds__contains=[self.pk])
        for userprofile in subscribers:
            userprofile.rss_feeds.remove(self.pk)
            userprofile.save()
        super(Feed, self).delete()

    def update(self):

        r = None

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
                FeedItem.objects.create(feed=self, title=saxutils.unescape(title), link=saxutils.unescape(link))

        finally:
            if r:
                self.last_response_code = r.status_code
            self.last_check = datetime.utcnow().replace(tzinfo=utc)
            self.save()

    @staticmethod
    def get_feed_list(rss_feeds, get_feed_items=True):

        feed_info = []

        if rss_feeds:
            # We can't merely use Feed.objects.filter(), since this won't retrieve our feeds in
            #  the correct order (based on the order of the feed ids in userprofile.rss_feeds)
            #  So we store the feed name temporarily in a lookup table...
            lookup = {}

            qs = Feed.objects.filter(id__in=rss_feeds)
            if get_feed_items:
                qs = qs.prefetch_related("feeditem_set")

            for feed in qs:
                lookup[feed.id] = feed

            # ...then use that here, where the proper order is preserved
            for feed_id in rss_feeds:
                feed_info.append(lookup[feed_id])

        return feed_info

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

    def __str__(self):
        return self.title

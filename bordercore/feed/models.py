import uuid
import xml.sax.saxutils as saxutils
from datetime import datetime

import feedparser
import requests

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import utc

from lib.mixins import TimeStampedModel

USER_AGENT = "Bordercore/1.0"


class Feed(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    url = models.URLField(unique=True)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)
    homepage = models.URLField(null=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    def update(self):

        r = None

        try:

            headers = {"user-agent": USER_AGENT}
            r = requests.get(self.url, headers=headers)

            if r.status_code != 200:
                r.raise_for_status()

            d = feedparser.parse(r.text)

            FeedItem.objects.filter(feed_id=self.pk).delete()

            for x in d.entries:
                title = x.title.replace("\n", "") or "No Title"
                link = x.link or ""
                FeedItem.objects.create(
                    feed=self,
                    title=saxutils.unescape(title),
                    link=saxutils.unescape(link)
                )

        finally:
            if r:
                self.last_response_code = r.status_code
            self.last_check = datetime.utcnow().replace(tzinfo=utc)
            self.save()

    @staticmethod
    def get_current_feed(user, session):

        current_feed_id = session.get("current_feed")

        if not current_feed_id:
            # If there is not a current feed in the session, then just pick the first feed
            return Feed.get_first_feed(user)
        else:
            try:
                return Feed.objects.values("id", "homepage", "last_check", "name").filter(pk=current_feed_id)[0]
            except Exception as e:
                log.warning(f"Feed exception: {e}")
                # If the session's current feed has been deleted, then just pick the first feed
                return Feed.get_first_feed(user)

    @staticmethod
    def get_first_feed(user):
        return user.userprofile.feeds.values("id", "homepage", "last_check", "name").order_by("sortorderuserfeed__sort_order").first()


class FeedItem(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    title = models.TextField()
    link = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

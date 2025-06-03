import datetime
import html
import logging
import uuid

import feedparser
import requests

from django.contrib.auth.models import User
from django.db import models

from lib.mixins import TimeStampedModel

USER_AGENT = "Bordercore/1.0"

log = logging.getLogger(f"bordercore.{__name__}")


class Feed(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    url = models.URLField(unique=True)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)
    homepage = models.URLField(null=True)
    verify_ssl_certificate = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    def update(self):

        r = None
        feed_list = []

        try:

            headers = {"user-agent": USER_AGENT}
            r = requests.get(self.url, headers=headers, verify=self.verify_ssl_certificate)

            if r.status_code != 200:
                r.raise_for_status()

            d = feedparser.parse(r.text)
            feed_list = d.entries

            FeedItem.objects.filter(feed_id=self.pk).delete()

            for x in feed_list:

                # We need to unescape some titles twice, notably those from
                # Hacker News, since their RSS feed generates titles like this:
                #
                #   Microtiming in Metallica&amp;#x27;s “Master of Puppets” (2014)
                #
                # We need to first unescape '&amp;' to get a '&', then unescape again
                # to translate '&#x26;' to a single apostrophe ''' character.
                try:
                    title = x.title.replace("\n", "") or "No Title"
                    link = x.link or ""
                    FeedItem.objects.create(
                        feed=self,
                        title=html.unescape(html.unescape(title)),
                        link=html.unescape(link)
                    )
                except AttributeError as e:
                    log.error("feed_uuid=%s Missing data in feed item: %s", self.uuid, e)

        finally:
            if r:
                self.last_response_code = r.status_code
            self.last_check = datetime.datetime.now(datetime.timezone.utc)
            self.save()

        return len(feed_list)

    @staticmethod
    def get_current_feed_id(user, session):

        current_feed_id = session.get("current_feed")

        if not current_feed_id:
            # If there is not a current feed in the session, then just pick the first feed
            return Feed.get_first_feed(user)["id"]

        try:
            return Feed.objects.values("id").filter(pk=current_feed_id).first()["id"]
        except Exception as e:
            log.warning("Feed exception: %s", e)
            # If the session's current feed has been deleted, then just pick the first feed
            return Feed.get_first_feed(user)["id"]

    @staticmethod
    def get_first_feed(user):
        return user.userprofile.feeds.values(
            "id"
        ).order_by(
            "userfeed__sort_order"
        ).first()


class FeedItem(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    title = models.TextField()
    link = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

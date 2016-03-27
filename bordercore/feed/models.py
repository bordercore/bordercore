from django.db import models

from accounts.models import UserProfile
from lib.mixins import TimeStampedModel


class Feed(TimeStampedModel):
    name = models.TextField()
    url = models.URLField(unique=True)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)
    homepage = models.URLField(null=True)

    def delete(self):
        # Unsubscribe all users who are currently subscribed to this feed
        subscribers = UserProfile.objects.raw("select * from accounts_userprofile where %d = any (rss_feeds)" % int(self.pk))
        for userprofile in subscribers:
            feeds = userprofile.rss_feeds
            feeds.remove( self.pk )
            userprofile.rss_feeds = feeds
            userprofile.save()
        super(Feed, self).delete()

    def subscribe_user(self, user, position):
        feeds = user.userprofile.rss_feeds
        # Verify that the user isn't already subscribed
        if self.pk in feeds:
            return
        feeds.insert( position - 1, self.pk )
        user.userprofile.rss_feeds = feeds
        user.userprofile.save()

    def unsubscribe_user(self, user):
        feeds = user.userprofile.rss_feeds
        feeds.remove( self.pk )
        user.userprofile.rss_feeds = feeds
        user.userprofile.save()


class FeedItem(models.Model):
    feed = models.ForeignKey(Feed)
    title = models.TextField()
    link = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

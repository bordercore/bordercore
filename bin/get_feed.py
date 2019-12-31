#!/usr/bin/env python
# encoding: utf-8

from datetime import datetime
import django
import os
import sys

from django.utils.timezone import utc

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'

django.setup()

from feed.models import Feed, FeedItem

LOG_FILE = "/var/log/django/get_feed.log"


def update_feeds(feed_id=None):

    # If an argument is supplied on the command line, interpret that as the
    #  feed id to update.  Otherwise update all feeds.
    info = None
    if feed_id:
        info = Feed.objects.filter(pk=int(feed_id))
    else:
        info = Feed.objects.all()

    for feed in info:
        try:
            feed.update()
        except Exception as e:
            t = datetime.utcnow().replace(tzinfo=utc)
            log_file = open(LOG_FILE, 'a')
            log_file.write("%s Exception for %s (feed_id %d): %s\n" % (t.strftime('%Y-%m-%d %H:%M:%S'), feed.name, feed.id, e.args))
            log_file.close()


if __name__ == "__main__":

    if len(sys.argv) == 2:
        feed_id = sys.argv[1]
    else:
        feed_id = None

    update_feeds(feed_id)

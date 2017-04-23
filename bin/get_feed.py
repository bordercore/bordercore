#!/usr/bin/env python
# encoding: utf-8

from datetime import datetime
import feedparser
import django
import os
import psycopg2
import psycopg2.extras
import sys
import xml.sax.saxutils as saxutils

import requests

from django.utils.timezone import utc

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.config.settings.prod'
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore')
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore/bordercore')

django.setup()

from feed.models import Feed, FeedItem

LOG_FILE = "/home/www/logs/get_feed.log"


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

            r = requests.get(feed.url)

            if r.status_code != 200:
                r.raise_for_status()

            d = feedparser.parse(r.text)

            FeedItem.objects.filter(feed_id=feed.id).delete()

            for x in d.entries:
                title = x.title or 'No Title'
                link = x.link or ''
                FeedItem.objects.create(feed_id=feed.id, title=saxutils.unescape(title), link=saxutils.unescape(link))

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

            t = datetime.utcnow().replace(tzinfo=utc)
            log_file = open(LOG_FILE, 'a')
            log_file.write("%s Exception for %s (feed_id %d): %s\n" % (t.strftime('%Y-%m-%d %H:%M:%S'), feed.name, feed.id, message))
            log_file.close()

        finally:

            feed.last_response_code = r.status_code
            feed.last_check = datetime.utcnow().replace(tzinfo=utc)
            feed.save()


if __name__ == "__main__":

    if len(sys.argv) == 2:
        feed_id = sys.argv[1]
    else:
        feed_id = None

    update_feeds(feed_id)

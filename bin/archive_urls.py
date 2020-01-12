#!/usr/bin/env python3

import datetime
from datetime import timedelta
import logging
import time

import django
import requests

django.setup()

from bookmark.models import Bookmark

# Remove existing handlers added by Django
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    filename="/var/log/django/url-archiver.log",
                    datefmt="%m-%d %H:%M:%S",
                    filemode="a")

logger = logging.getLogger("bordercore.urlarchiver")

# Only let requests log at level WARNING or higher
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

# Get all urls saved within the last day
new_urls = Bookmark.objects.filter(
    created__gte=datetime.datetime.now(datetime.timezone.utc) - timedelta(seconds=86400))

for url in new_urls:

    logger.info("Archiving {}".format(url.url))
    wayback_url = "https://web.archive.org/save/{}".format(url.url)
    r = requests.get(wayback_url)
    if r.status_code != 200:
        logger.warning(" Error, status code={}".format(r.status_code))
    time.sleep(10)

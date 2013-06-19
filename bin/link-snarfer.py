#!/usr/bin/env python

import logging
import os
import quopri
import pprint
import sys
import re
import requests
from lxml.html import fromstring

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.settings'
sys.path.insert(0, '/home/www/htdocs/bordercore-django')
from bookmark.models import Bookmark

link_dict = {}  # Store links in a dict to avoid duplication

pp = pprint.PrettyPrinter()
p = re.compile("(https?://[^\">\s\n]*)[\">\s\n]")
ignore = re.compile("doubleclick|https://twitter.com|tapbots.com|tapbots.net|search.twitter.com")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename=os.environ['HOME'] + '/logs/link-snarfer.log',
                    filemode='a')

logger = logging.getLogger('bordercore.linksnarfer')

# Only let requests log at level WARNING or higher
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

def get_link_info(link):
    r = requests.get(link)
    http_content = r.text

    # If this link is a redirect (common for shortened urls), we
    #  want to keep the redirected link.
    # for prev in r.history:
    #     print "  redirected url: %s" % prev.url

    doc = fromstring(http_content)
    title = doc.xpath('.//title')
    if title:
        return (r.url, title[0].text)
    else:
        return (r.url, "No title")


buffer = ''
for line in sys.stdin:
    buffer += line

# Decode quoted-printable contents
buffer = quopri.decodestring(buffer)
matches = p.findall(buffer)

for link in matches:

    if not ignore.search(link):
        url, label = get_link_info(link)
        link_dict[ label ] = url

if link_dict:

    for label in link_dict.keys():

        print "label: %s" % label.encode('utf-8')
        print "link: %s" % link_dict[label]
        logger.info(link_dict[label])

        b = Bookmark(url=link_dict[label], title=label or 'No Label', user_id=1)
        b.save()

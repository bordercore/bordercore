#!/usr/bin/env python

import django
import email
import logging
import os
import quopri
import pprint
import sys
import re
import requests
from lxml import html

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.config.settings.prod'
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore')
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore/bordercore')

django.setup()

from bookmark.models import Bookmark


link_dict = {}  # Store links in a dict to avoid duplication

pp = pprint.PrettyPrinter()
p = re.compile("(https?://[^\">\s\n]*)[\">\s\n]")
ignore = re.compile("doubleclick|https://twitter.com|tapbots.com|tapbots.net|search.twitter.com|www.youtube.com/subscription_manager")

# Remove existing handlers added by Django
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

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
    headers = {'user-agent': 'Bordercore/1.0'}
    r = requests.get(link, headers=headers)
    http_content = r.text.encode('utf-8')

    # http://stackoverflow.com/questions/15830421/xml-unicode-strings-with-encoding-declaration-are-not-supported
    # parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
    # doc = fromstring(http_content, parser=parser)
    doc = html.fromstring(http_content)
    title = doc.xpath('.//title')
    if title:
        return (r.url, title[0].text)
    else:
        return (r.url, "No title")


def get_youtube_content(msg):

    info = {}

    for i, part in enumerate(msg.walk(), 1):
        if part.get_content_type() == 'text/plain':
            content = part.get_payload(decode=True)

    p = re.compile('^Content-Type: text/plain')
    lines = content.decode('UTF-8', 'ignore').split('\n')
    info['uploader'] = lines[0]
    info['title'] = lines[1]
    info['url'] = lines[2]

    p = re.compile('(.*) just uploaded a video')
    m = p.match(info['uploader'])
    if m:
        info['subject'] = "%s: %s" % (m.group(1), info['title'])
    else:
        info['subject'] = info['title']

    return info


buffer = ''
for line in sys.stdin:
    buffer += line

msg = email.message_from_string(buffer)
if msg.get('From', None).startswith('YouTube'):
    link_info = get_youtube_content(msg)
    logger.info('YouTube email: %s' % link_info['subject'])
    if link_info:
        b = Bookmark(url=link_info['url'], title=link_info['subject'] or 'No Label', user_id=1)
        b.save()
        sys.exit(0)


# Decode quoted-printable contents
buffer = quopri.decodestring(buffer)
matches = p.findall(buffer.decode('UTF-8', 'ignore'))

for link in matches:

    if not ignore.search(link):
        url, label = get_link_info(link)
        link_dict[label] = url

if link_dict:

    for label in link_dict.keys():
        logger.info(u"%s - %s" % (link_dict[label], label))
        b = Bookmark(url=link_dict[label], title=label or 'No Label', user_id=1)
        b.save()

#!/usr/bin/env python

import django
import email
import logging
import os
import quopri
from pathlib import Path
import pprint
import sys
import re
import requests
import time
from lxml import html

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'

django.setup()

from bookmark.models import Bookmark

link_dict = {}  # Store links in a dict to avoid duplication

pp = pprint.PrettyPrinter()
p = re.compile(r"(https?://[^\">\s\n]*)[\">\s\n]")
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
requests_log = logging.getLogger("requests").setLevel(logging.WARNING)


def get_link_info(link):
    headers = {'user-agent': 'Bordercore/1.0'}
    r = requests.get(link, headers=headers)
    http_content = r.text.encode('utf-8')

    # http://stackoverflow.com/questions/15830421/xml-unicode-strings-with-encoding-declaration-are-not-supported
    doc = html.fromstring(http_content)
    title = doc.xpath('.//title')
    if title:
        return (r.url, title[0].text)
    else:
        return (r.url, "No title")


def store_email(title, lines):

    dir = "/tmp/link_snarfer"
    if not Path(dir).isdir():
        os.makedirs(dir)

    filename = f"{title}-{time.time()}"
    with open(f"{dir}/{filename}", "a") as debug_file:
        debug_file.write(lines)


def find_first_link(lines):
    links = [x for x in lines if x.startswith("http")]
    return links[0].rstrip()


def get_title(lines):

    buffer = []
    for line in lines:
        if line.startswith("http"):
            return buffer[-1]
        buffer.append(line)

    return "No title"


def get_youtube_content(msg):

    info = {}

    for i, part in enumerate(msg.walk(), 1):
        if part.get_content_type() == 'text/plain':
            content = part.get_payload(decode=True)

    p = re.compile('^Content-Type: text/plain')
    content = content.decode('UTF-8', 'ignore')
    lines = content.split('\n')
    info['uploader'] = lines[0]
    # info['title'] = lines[1]
    info['title'] = get_title(lines)
    # info['url'] = lines[2]
    info['url'] = find_first_link(lines)

    if logger.level == "DEBUG":
        store_email(info["title"], content)

    # Sometimes the title takes up two lines
    if not info['url'].startswith('http'):
        info['url'] = lines[3]
        info['title'] = info['title'] + lines[2]

    p = re.compile('(.*) just uploaded a video')
    m = p.match(info['uploader'])
    if m:
        info['subject'] = "%s: %s" % (m.group(1), info['title'])
    else:
        info['subject'] = info['title']
        # return None

    return info


buffer = ''
for line in sys.stdin:
    buffer += line

msg = email.message_from_string(buffer)
if msg.get('From', '').startswith('YouTube'):
    link_info = get_youtube_content(msg)
    logger.info('YouTube email: %s' % link_info['subject'])
    if link_info:
        b = Bookmark(url=link_info['url'], title=link_info['subject'] or 'No Label', user_id=1)
        b.save()
        b.index_bookmark()
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
        b.index_bookmark()

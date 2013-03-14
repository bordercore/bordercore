#!/usr/bin/python

import logging
import os
import psycopg2
import quopri
import pprint
import sys
import re
import requests
from lxml.html import fromstring

# os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# sys.path.insert(0, "/home/jerrell/dev/django/bordercore")
# from bookmark.models import Bookmark

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

def get_link_info(link):
    r = requests.get(link)
    http_content = r.text

    # If this link is a redirect (common for shortened urls), return
    #  the redirected link for storage.
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

# Save the buffer to a file for later debugging
# import time
# f = open("/tmp/link-snarfer/" + str(time.time()), "w")
# f.write(buffer)
# f.close()

for link in matches:

    if not ignore.search(link):
        url, label = get_link_info(link)
        link_dict[ label ] = link

if link_dict:

    conn = psycopg2.connect("dbname=django host=localhost user=bordercore password=4locus2")
    cur = conn.cursor()

    for label in link_dict.keys():

        print "label: %s" % label
        print "link: %s" % link_dict[label]

        # b = Bookmark(url='http://www.google.com', title='Google Link', user_id=1)
        # b.save()

        cur.execute("insert into bookmark_bookmark(created,modified,active,url,title,user_id) values (now(), now(), 't', %s,%s,1)", (link, label))
        conn.commit()

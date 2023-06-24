import email
import json
import logging
import os
import quopri
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from django.conf import settings

from lib.util import parse_title_from_url

link_dict = {}  # Store links in a dict to avoid duplication

p = re.compile(r"(https?://[^\">\s\n]*)[\">\s\n]")
ignore = re.compile("doubleclick|https://twitter.com|tapbots.com|tapbots.net|search.twitter.com|www.youtube.com/subscription_manager|blogtrottr")

# Remove existing handlers added by Django
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M:%S",
                    filename=os.environ["HOME"] + "/logs/link-snarfer.log",
                    filemode="a")

logger = logging.getLogger("bordercore.linksnarfer")

# Only let requests log at level WARNING or higher
requests_log = logging.getLogger("requests").setLevel(logging.WARNING)


def get_drf_token():

    load_dotenv(f"{settings.BASE_DIR}/config/settings/secrets.env")
    return os.environ["DRF_TOKEN_JERRELL"]


def store_email(title, lines):

    dir = "/tmp/link_snarfer"
    if not Path(dir).is_dir():
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
        if part.get_content_type() == "text/plain":
            content = part.get_payload(decode=True)

    content = content.decode("UTF-8", "ignore")
    lines = content.split("\n")
    info["uploader"] = lines[0]
    info["title"] = get_title(lines)
    info["url"] = find_first_link(lines)

    if logger.level == "DEBUG":
        store_email(info["title"], content)

    # Sometimes the title takes up two lines
    if not info["url"].startswith("http"):
        info["url"] = lines[3]
        info["title"] = info["title"] + lines[2]

    info["subject"] = f"{info['uploader']}: {info['title']}"

    return info


def add_to_bordercore(link_info):

    payload = {
        "url": link_info["url"],
        "name": link_info["subject"],
        "user": 1
    }

    url = "https://www.bordercore.com/api/bookmarks/"

    token = get_drf_token()

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

    # We use a session so that we can set trust_env = None (see below)
    s = requests.Session()

    # Set this so that the ~/.netrc file is ignored for authentication
    s.trust_env = None

    s.post(url, data=json.dumps(payload), headers=headers)


buffer = ""
for line in sys.stdin:
    buffer += line

msg = email.message_from_string(buffer)
if "Blogtrottr" in msg.get("From", ""):
    link_info = get_youtube_content(msg)
    logger.info("YouTube email: %s" % link_info["subject"])
    if link_info:
        add_to_bordercore(link_info)
    sys.exit(0)

# Decode quoted-printable contents
buffer = quopri.decodestring(buffer)
matches = p.findall(buffer.decode("UTF-8", "ignore"))

for link in matches:

    if not ignore.search(link):
        url, label = parse_title_from_url(link)
        link_dict[label] = url

if link_dict:

    for label in link_dict.keys():
        logger.info(u"%s - %s" % (link_dict[label], label))
        link_info = {
            "url": link_dict[label],
            "subject": label or "No Title"
        }
        add_to_bordercore(link_info)

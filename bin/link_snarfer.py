"""
Link Snarfer for processing inbound email content, extracting URLs, and posting them to Bordercore.
Handles YouTube emails separately and parses content for link metadata.
Typically invoked by Procmail.
"""

import email
import json
import logging
import os
import quopri
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

from django.conf import settings

from lib.util import parse_title_from_url

link_dict = {}  # Store links in a dict to avoid duplication

p = re.compile(r"(https?://[^\">\s\n]*)[\">\s\n]")
ignore = re.compile(
    "doubleclick|"
    "https://twitter.com|"
    "search.twitter.com|"
    "www.youtube.com/subscription_manager|"
    "blogtrottr"
)

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
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

def get_drf_token() -> str:
    """
    Load DRF token from environment file for API authentication.

    Returns:
        str: The DRF token string.
    """
    load_dotenv(f"{settings.BASE_DIR}/config/settings/secrets.env")
    return os.environ["DRF_TOKEN_JERRELL"]


def store_email(title: str, lines: str) -> None:
    """
    Save email contents to a local debug file.

    Args:
        title (str): Filename prefix.
        lines (str): Content to write.
    """
    directory = "/tmp/link_snarfer"
    if not Path(directory).is_dir():
        os.makedirs(directory)

    filename = f"{title}-{time.time()}"
    with open(f"{directory}/{filename}", "a", encoding="utf-8") as debug_file:
        debug_file.write(lines)


def find_first_link(lines: list[str]) -> str:
    """
    Extract the first HTTP link from a list of lines.

    Args:
        lines (list): List of strings.

    Returns:
        str: First URL found.
    """
    links = [x for x in lines if x.startswith("http")]
    return links[0].rstrip()


def get_title(lines: list[str]) -> str:
    """
    Retrieve the title associated with the first link.

    Args:
        lines (list): List of strings from the email body.

    Returns:
        str: Title string or fallback message.
    """
    buffer: list[str] = []
    for line in lines:
        if line.startswith("http"):
            return buffer[-1]
        buffer.append(line)

    return "No title"


def get_youtube_content(msg: email.message.Message) -> Optional[dict[str, str]]:
    """
    Extract metadata from a YouTube-related email.

    Args:
        msg (email.message.Message): Parsed email message object.

    Returns:
        dict or None: Dictionary with uploader, title, URL, and subject — or None on error.
    """
    info = {}

    for _, part in enumerate(msg.walk(), 1):
        if part.get_content_type() == "text/plain":
            content = part.get_payload(decode=True)
            break

    if content is None:
        logger.error("No text/plain content found in email")
        return None

    if isinstance(content, bytes):
        decoded = content.decode("UTF-8", "ignore")
    else:
        logger.error("Expected bytes content, got non-bytes type")
        return None

    lines = decoded.split("\n")

    info["uploader"] = lines[0]
    info["title"] = get_title(lines)
    info["url"] = find_first_link(lines)

    if logger.level == "DEBUG":
        store_email(info["title"], decoded)

    # Sometimes the title takes up two lines
    if not info["url"].startswith("http"):
        info["url"] = lines[3]
        info["title"] = info["title"] + lines[2]

    info["subject"] = f"{info['uploader']}: {info['title']}"

    return info


def add_to_bordercore(link_info: dict[str, str]) -> None:
    """
    Send a link payload to Bordercore's bookmarks API.

    Args:
        link_info (dict): Dictionary with 'url' and 'subject' keys.
    """
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


def main() -> None:
    """
    Entry point for script execution.
    Reads email from stdin, parses content, and submits relevant links to Bordercore.
    Handles Blogtrottr YouTube messages specially.
    """
    buffer = "".join(sys.stdin)

    msg = email.message_from_string(buffer)
    if "Blogtrottr" in msg.get("From", ""):
        link_info = get_youtube_content(msg)
        if link_info:
            logger.info("YouTube email: %s", link_info['subject'])
            add_to_bordercore(link_info)
        sys.exit(0)

    # Decode quoted-printable contents
    buffer_bytes = quopri.decodestring(buffer.encode("utf-8"))
    matches = p.findall(buffer_bytes.decode("utf-8", "ignore"))

    for link in matches:
        if not ignore.search(link):
            url, label = parse_title_from_url(link)
            link_dict[label] = url

    if link_dict:
        for label, url in link_dict.items():
            logger.info("%s - %s", url, label)
            link_info = {
                "url": url,
                "subject": label or "No Title"
            }
            add_to_bordercore(link_info)


if __name__ == "__main__":
    main()

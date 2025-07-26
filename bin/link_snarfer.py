"""
Link Snarfer for processing inbound email content, extracting URLs, and posting them to Bordercore.
Handles YouTube emails separately and parses content for link metadata.
Typically invoked by Procmail.
"""

import email
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

logger = logging.getLogger("bordercore.linksnarfer")

# Only let requests log at level WARNING or higher
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                        datefmt="%m-%d %H:%M:%S",
                        filename=os.path.join(os.environ["HOME"], "logs", "link-snarfer.log"),
                        filemode="a")


def get_drf_token() -> str:
    """
    Load DRF token from environment file for API authentication.

    Returns:
        The DRF token string.
    """
    load_dotenv(f"{settings.BASE_DIR}/config/settings/secrets.env")
    return os.environ["DRF_TOKEN_JERRELL"]


def store_email(title: str, lines: str) -> None:
    """
    Save email contents to a local debug file.

    Args:
        title: Filename prefix.
        lines: Content to write.
    """
    directory = "/tmp/link_snarfer"
    Path(directory).mkdir(parents=True, exist_ok=True)

    filename = f"{title}-{time.time()}"
    with open(f"{directory}/{filename}", "a", encoding="utf-8") as debug_file:
        debug_file.write(lines)


def find_first_link(lines: list[str]) -> str:
    """
    Extract the first HTTP link from a list of lines.

    Args:
        lines (list): List of strings.

    Returns:
        First URL found.
    """
    links = [x for x in lines if x.startswith("http")]
    return links[0].rstrip()


def get_title(lines: list[str]) -> str:
    """
    Retrieve the title associated with the first link.

    Args:
        lines: List of strings from the email body.

    Returns:
        Title string or fallback message.
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
        msg: Parsed email message object.

    Returns:
        Dictionary with uploader, title, URL, and subject — or None on error.
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

    if len(lines) < 4:
        logger.warning("Unexpected YouTube email format")
        return None

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


def add_to_bordercore(
        link_info: dict[str, str],
        session: requests.Session,
        token: str
) -> None:
    """
    Send a link payload to Bordercore's bookmarks API.

    Args:
        link_info: Dictionary with 'url' and 'subject' keys.
        session: A configured `requests.Session` instance for making the API call.
        token: A DRF authentication token used in the Authorization header.
    """

    payload = {
        "url": link_info["url"],
        "name": link_info["subject"],
        "user": 1
    }

    url = "https://www.bordercore.com/api/bookmarks/"

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

    session.post(url, json=payload, headers=headers)


def handle_youtube_email(
    msg: email.message.Message,
    session: requests.Session,
    token: str
) -> None:
    """
    Extract and post YouTube link info from the given email message.

    Args:
        msg: Parsed email message object.
        session: Configured HTTP session for making API requests.
        token: DRF authentication token for API authorization.
    """
    link_info = get_youtube_content(msg)

    if not link_info:
        return

    if link_info["url"].startswith("https://www.youtube.com/shorts/"):
        logger.info("Skipping YouTube Short: %s", link_info["subject"])
        return

    logger.info("YouTube email: %s", link_info["subject"])
    add_to_bordercore(link_info, session, token)


def handle_generic_email(
    buffer: str,
    session: requests.Session,
    token: str
) -> None:
    """
    Extract and post all valid HTTP/HTTPS links from a generic email body.

    Args:
        buffer: Raw email content as a string.
        session: Configured HTTP session for making API requests.
        token: DRF authentication token for API authorization.
    """
    buffer_bytes = quopri.decodestring(buffer.encode("utf-8"))
    matches = p.findall(buffer_bytes.decode("utf-8", "ignore"))

    for link in matches:
        if not ignore.search(link):
            url, label = parse_title_from_url(link)
            logger.info("%s - %s", url, label)
            link_info = {
                "url": url,
                "subject": label or "No Title"
            }
            add_to_bordercore(link_info, session, token)


def main() -> None:
    """
    Entry point for script execution.

    Reads an email from stdin, determines if it's a YouTube notification or a
    general link email, and handles each case appropriately.
    """
    buffer = "".join(sys.stdin)
    msg = email.message_from_string(buffer)

    session = requests.Session()
    session.trust_env = None
    token = get_drf_token()

    if "Blogtrottr" in msg.get("From", ""):
        handle_youtube_email(msg, session, token)
    else:
        handle_generic_email(buffer, session, token)


if __name__ == "__main__":
    configure_logging()
    main()

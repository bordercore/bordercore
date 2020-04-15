# Parse SNS Notifications from AWS generated when a new
#  object is added to the blobs S3 bucket. Specifically,
#  parse the sha1sum and download it from S3 to a
#  corresponding location on local file storage.

import email
import json
import logging
import os
import re
import sys
from os import makedirs
from pathlib import Path
from urllib.parse import unquote

import boto3

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
django.setup()

from blob.models import ILLEGAL_FILENAMES  # isort:skip

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M:%S",
                    filename=f"{os.environ['HOME']}/logs/s3-procmail.log",
                    filemode="a")

logger = logging.getLogger("bordercore.sync_s3_to_wumpus")

BLOB_DIR = "/home/media"

s3_client = boto3.client("s3")


def get_info_from_message(buffer):

    msg = email.message_from_string(buffer)
    payload = json.loads(msg.get_payload())
    event = json.loads(payload["Message"])

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    object = event["Records"][0]["s3"].get("object", None)

    return {
        "bucket": bucket,
        "object": object,
        "eventName": event["Records"][0].get("eventName", None)
    }


def delete_object_from_wumpus(info):

    # Amazon replaces spaces with plus signs, so we must change them back
    key = Path(f"{BLOB_DIR}/{unquote(info['object']['key'])}".replace("+", " "))
    if key.name in ILLEGAL_FILENAMES:
        logger.info("  Skipping. File is cover image.")
        return

    # Remove the file
    if key.exists():
        key.unlink()

    # Remove any old cover files
    for cover in ILLEGAL_FILENAMES:
        cover_path = key.parent / cover
        if cover_path.exists():
            cover_path.unlink()

    # Remove the parent directory
    key.parent.rmdir()


def copy_object_to_wumpus(info):

    key = unquote(info["object"]["key"].replace("+", " "))
    file_path = f"{BLOB_DIR}/{key}"

    # First check if it already exists
    if os.path.isfile(file_path):
        logger.info("  Skipping. File already exists.")
    else:
        logger.info(file_path)
        matches = re.compile(r".*/(blobs/\w\w/[0-9a-f]{40})/(.*)").match(file_path)
        dirs = matches.group(1)
        filename = matches.group(2)

        if filename in ILLEGAL_FILENAMES:
            logger.info("  Skipping. File is cover image.")
        else:
            makedirs(f"{BLOB_DIR}/{dirs}", exist_ok=True)
            # Amazon replaces spaces with plus signs, so we must change them back
            s3_client.download_file(info["bucket"], key, file_path)


buffer = ""
for line in sys.stdin:
    buffer += line

logger.info(buffer)

info = get_info_from_message(buffer)

if not info["object"]:
    # There is no S3 object associated with this blob, so
    #  there is nothing for us to do.
    sys.exit(0)

if info["eventName"] == "ObjectRemoved:Delete":
    delete_object_from_wumpus(info)
else:
    logger.info(f"Downloading new object: {info['object']['key']}")
    copy_object_to_wumpus(info)

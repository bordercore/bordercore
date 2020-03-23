# Parse SNS Notifications from AWS generated when a new
#  object is added to the blobs S3 bucket. Specifically,
#  parse the sha1sum and download it from S3 to a
#  corresponding location on local file storage.

import email
import json
import os
import re
import sys
from os import makedirs

import boto3

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
django.setup()

from blob.models import ILLEGAL_FILENAMES  # isort:skip


BLOB_DIR = "/home/media"

s3_client = boto3.client("s3")


def get_key_from_message(buffer):

    msg = email.message_from_string(buffer)
    payload = json.loads(msg.get_payload())
    event = json.loads(payload["Message"])

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    object = event["Records"][0]["s3"]["object"]

    return (bucket, object)


def copy_object_to_wumpus(bucket, object):

    file_path = f"{BLOB_DIR}/{object['key']}"

    # First check if it already exists
    if os.path.isfile(file_path):
        print("  Skipping. File already exists.")
    else:
        print(file_path)
        matches = re.compile(r".*/(blobs/\w\w/[0-9a-f]{40})/(.*)").match(file_path)
        dirs = matches.group(1)
        filename = matches.group(2)

        if filename in ILLEGAL_FILENAMES:
            print("  Skipping. File is cover image.")
        else:
            makedirs(f"{BLOB_DIR}/{dirs}", exist_ok=True)
            s3_client.download_file(bucket, object["key"], file_path)


buffer = ""
for line in sys.stdin:
    buffer += line

bucket, object = get_key_from_message(buffer)

print(f"Downloading new object: {object['key']}")

copy_object_to_wumpus(bucket, object)
